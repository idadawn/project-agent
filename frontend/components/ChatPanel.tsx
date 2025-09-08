'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X, File, Bot, ChevronDown, ChevronUp, Settings, CheckCircle, XCircle, Clock, Search, Edit, Puzzle, CheckSquare, FileText, Play, Loader2, Circle, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { OptimizationPanel } from './OptimizationPanel'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, any>
  timestamp?: string
}

interface AgentStatus {
  agent: string
  action: string
  status?: 'processing' | 'completed' | 'failed' | 'success'
  timestamp?: string
  error?: string
}

interface ChatPanelProps {
  messages: Message[]
  onSendMessage: (message: string, files?: File[]) => void
  onOptimizeText: (instruction: string) => void
  selectedText: string
  loading?: boolean
  sessionId: string | null
  agentStatus?: AgentStatus | null
  onFilesCreated?: (files: any[]) => void
}

export function ChatPanel({ 
  messages, 
  onSendMessage, 
  onOptimizeText,
  selectedText, 
  loading,
  sessionId,
  agentStatus,
  onFilesCreated
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [showOptimization, setShowOptimization] = useState(false)
  const [showAgentDetails, setShowAgentDetails] = useState(true)
  const [selectedModel, setSelectedModel] = useState('deepseek/deepseek-chat-v3.1')
  const [showModelOptions, setShowModelOptions] = useState(false)
  const [currentPipelineState, setCurrentPipelineState] = useState<{
    isActive: boolean
    currentAgent?: string
    agentStatus?: AgentStatus
  }>({ isActive: false })
  const [collapsedSteps, setCollapsedSteps] = useState<Set<string>>(new Set())
  const [collapsedDetails, setCollapsedDetails] = useState<Set<string>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 解析消息中的 docx 链接
  const extractDocxLinks = (text: string): string[] => {
    if (!text) return []
    const urlRegex = /(https?:\/\/[^\s)]+\.(?:docx|doc))(?!\w)/gi
    const matches = text.match(urlRegex) || []
    // 去重
    return Array.from(new Set(matches))
  }

  const getFilenameFromUrl = (url: string): string => {
    try {
      const u = new URL(url)
      const parts = u.pathname.split('/')
      const last = parts[parts.length - 1]
      return decodeURIComponent(last || 'document.docx')
    } catch {
      const parts = url.split('/')
      return decodeURIComponent(parts[parts.length - 1] || 'document.docx')
    }
  }

  // Pipeline 步骤定义
  const pipelineSteps = [
    { id: 'document_parsing', name: '文档解析', description: '解析招标文件', agent: 'coordinator', icon: 'FileText', agentKey: 'coordinator' },
    { id: 'structure_extraction', name: 'A-结构抽取', description: '提取投标文件格式要求', agent: 'StructureExtractor', icon: 'Search', agentKey: 'structure_extractor' },
    { id: 'spec_extraction', name: 'B-规格书提取', description: '提取技术规格书', agent: 'SpecExtractor', icon: 'FileText', agentKey: 'spec_extractor' },
  ]

  // 获取图标组件
  const getIconComponent = (iconName: string) => {
    const icons = { Search, FileText, Edit, Puzzle, CheckSquare }
    const Icon = icons[iconName as keyof typeof icons] || FileText
    return <Icon className="h-4 w-4 text-blue-600" />
  }

  // 切换步骤折叠状态
  const toggleStepCollapse = (stepId: string) => {
    setCollapsedSteps(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  // 切换详情折叠状态
  const toggleDetailsCollapse = (stepId: string) => {
    setCollapsedDetails(prev => {
      const newSet = new Set(prev)
      if (newSet.has(stepId)) {
        newSet.delete(stepId)
      } else {
        newSet.add(stepId)
      }
      return newSet
    })
  }

  // 智能体名称映射：将后端发送的智能体名称映射到前端的agentKey
  const mapAgentNameToKey = (backendAgentName: string): string => {
    const agentMapping: Record<string, string> = {
      'coordinator': 'coordinator',
      'document_parser': 'coordinator', // 文档解析阶段也显示为第一步
      'DocumentParserAgent': 'coordinator',
      'StructureExtractor': 'structure_extractor',
      'SpecExtractor': 'spec_extractor', 
      'PlanOutliner': 'plan_outliner',
      'BidAssembler': 'bid_assembler',
      'SanityChecker': 'sanity_checker',
      // 添加小写版本的映射
      'structure_extractor': 'structure_extractor',
      'spec_extractor': 'spec_extractor',
      'plan_outliner': 'plan_outliner', 
      'bid_assembler': 'bid_assembler',
      'sanity_checker': 'sanity_checker'
    }
    return agentMapping[backendAgentName] || backendAgentName
  }

  // 智能状态推断：根据消息内容推断当前执行状态
  const inferPipelineStateFromMessages = () => {
    if (messages.length === 0) return null
    
    // 从最新消息开始向前查找
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 3); i--) {
      const message = messages[i]
      if (message.role !== 'assistant') continue
      
      const content = message.content || ''
      const metadata = message.metadata || {}
      
      // 检查是否是完成状态
      if (content.includes('✅ 已完成A–E链路') || 
          content.includes('✅ 已完成最小链路') ||
          metadata.stage === 'bid_build_completed' ||
          metadata.action === 'bid_build_completed') {
        return {
          agent: 'spec_extractor', // 新流程以规格提取完成为止
          status: 'completed',
          action: 'bid_build_completed'
        }
      }
      
      // 检查具体的智能体执行状态
      if (metadata.current_agent) {
        // 映射智能体名称
        const mappedAgent = mapAgentNameToKey(metadata.current_agent)
        
        // 根据内容判断是否已完成
        let status = 'running'
        if (content.includes('✅') || content.includes('已完成') || 
            metadata.stage === 'parsing_completed' ||
            metadata.action === 'parsing_completed') {
          status = 'completed'
        }
        
        return {
          agent: mappedAgent,
          status,
          action: metadata.action || '正在执行'
        }
      }
      
      // 检查文件上传的指示
      if (content.includes('文档解析') || content.includes('DocumentParser')) {
        return {
          agent: 'coordinator',
          status: 'running', 
          action: '正在解析文档'
        }
      }
    }
    
    // 检查用户是否上传了文件
    for (let i = messages.length - 1; i >= Math.max(0, messages.length - 2); i--) {
      const message = messages[i]
      if (message.role === 'user' && 
          (message.content.includes('.docx') || message.content.includes('.doc') ||
           message.content.includes('分析') || message.content.includes('投标'))) {
        return {
          agent: 'coordinator',
          status: 'running',
          action: '正在分析请求'
        }
      }
    }
    
    return null
  }

  // 时间线样式的流水线进度显示
  const renderTimelinePipelineProgress = (currentAgent?: string, agentStatus?: AgentStatus) => {
    // 优先使用实时状态，然后从消息历史推断
    let finalState = null
    
    if (currentAgent && agentStatus) {
      const mappedAgent = mapAgentNameToKey(currentAgent)
      finalState = {
        agent: mappedAgent,
        status: agentStatus.action === 'bid_build_completed' ? 'completed' : 'running',
        action: agentStatus.action
      }
    } else {
      // 从消息历史推断
      finalState = inferPipelineStateFromMessages()
    }
    
    if (!finalState) return null
    
    const { agent: mappedAgentKey, status, action } = finalState
    
    // 调试信息
    console.log('Pipeline Debug:', {
      currentAgent,
      agentStatus,
      finalState,
      mappedAgentKey
    })
    
    const isAllCompleted = status === 'completed'
    const currentStepIndex = pipelineSteps.findIndex(step => step.agentKey === mappedAgentKey)
    const completedSteps = isAllCompleted ? pipelineSteps.length : Math.max(0, currentStepIndex + 1)
    const progress = (completedSteps / pipelineSteps.length) * 100

    // 获取步骤状态
    const getStepStatus = (index: number) => {
      if (isAllCompleted || index < currentStepIndex) return 'completed'
      if (index === currentStepIndex) return 'running'
      return 'pending'
    }

    // 获取状态图标
    const getStatusIcon = (status: string) => {
      switch (status) {
        case 'completed': 
          return <CheckCircle2 className="h-5 w-5 text-green-600 bg-white rounded-full" />
        case 'running': 
          return <Loader2 className="h-5 w-5 text-blue-600 bg-white rounded-full animate-spin" />
        case 'error': 
          return <XCircle className="h-5 w-5 text-red-600 bg-white rounded-full" />
        default: 
          return <Circle className="h-5 w-5 text-gray-400 bg-white rounded-full" />
      }
    }

    // 获取步骤详情
    const getStepDetails = (step: any, status: string, index: number) => {
      const isCollapsed = collapsedDetails.has(step.id)
      const details = [
        '操作流程：',
        `1. 收到文件，开始${step.description}`,
        '2. 调用相关AI智能体处理',
        '3. 生成结果文件并保存',
        `状态显示：${status === 'completed' ? '✅ 已完成' : status === 'running' ? '⏳ 执行中' : '⏸️ 等待中'}`
      ]
      
      return (
        <div className="mt-2 text-sm text-gray-600">
          <button 
            onClick={() => toggleDetailsCollapse(step.id)}
            className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs mb-2"
          >
            {isCollapsed ? <ChevronDown className="h-3 w-3" /> : <ChevronUp className="h-3 w-3" />}
            {isCollapsed ? '展开详情' : '收起详情'}
          </button>
          {!isCollapsed && (
            <div className="bg-gray-50 rounded-md p-3 space-y-1">
              {details.map((detail, i) => (
                <div key={i} className="text-xs">{detail}</div>
              ))}
            </div>
          )}
        </div>
      )
    }

    return (
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-4 shadow-sm">
        {/* 头部信息 */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 rounded-full p-2">
              <Play className="h-4 w-4 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-blue-900 text-lg">🤖 智能体执行流水线</h3>
              <p className="text-sm text-blue-700">正在执行最小工作流（解析→结构→规格），请稍候...</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-900">{completedSteps}/{pipelineSteps.length}</div>
            <div className="text-xs text-blue-700">已完成步骤</div>
          </div>
        </div>
        
        {/* 进度条 */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-blue-700 mb-2">
            <span>整体进度</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${
                isAllCompleted ? 'bg-gradient-to-r from-green-500 to-green-600' : 'bg-gradient-to-r from-blue-500 to-blue-600'
              }`} 
              style={{ width: `${progress}%` }} 
            />
          </div>
          <div className="mt-2 text-sm">
            {isAllCompleted ? (
              <span className="text-green-600 font-medium">✅ 所有步骤已完成</span>
            ) : (
              <span className="text-blue-600 font-medium">⚡ 正在执行: {pipelineSteps[currentStepIndex]?.name || '不明步骤'}</span>
            )}
          </div>
        </div>

        {/* 时间线步骤 */}
        <div className="space-y-0">
          {pipelineSteps.map((step, index) => {
            const stepStatus = getStepStatus(index)
            const isActive = !isAllCompleted && index === currentStepIndex
            const isCollapsed = collapsedSteps.has(step.id)
            const showConnector = index < pipelineSteps.length - 1
            
            return (
              <div key={step.id} className="relative">
                {/* 连接线 */}
                {showConnector && (
                  <div className={`absolute left-6 top-12 w-0.5 h-12 ${
                    stepStatus === 'completed' || (index < currentStepIndex) ? 'bg-green-400' : 'bg-gray-300'
                  }`} />
                )}
                
                {/* 步骤内容 */}
                <div className={`relative flex items-start gap-4 p-4 rounded-lg transition-all duration-300 ${
                  isActive ? 'bg-blue-100 border-2 border-blue-300 shadow-md' : 
                  stepStatus === 'completed' ? 'bg-green-50 border border-green-200' : 
                  'bg-white border border-gray-200'
                }`}>
                  {/* 状态图标 */}
                  <div className="flex-shrink-0 relative z-10">
                    {getStatusIcon(stepStatus)}
                  </div>
                  
                  {/* 步骤信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                          stepStatus === 'completed' ? 'bg-green-100 text-green-700' :
                          stepStatus === 'running' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
                        }`}>
                          {index === 0 ? '解析' : String.fromCharCode(64 + index)}
                        </div>
                        <div>
                          <h4 className={`font-bold ${
                            isActive ? 'text-blue-900' : 
                            stepStatus === 'completed' ? 'text-green-800' : 'text-gray-700'
                          }`}>
                            {step.name}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                        </div>
                        {getIconComponent(step.icon)}
                      </div>
                      
                      {/* 折叠按钮 */}
                      <button 
                        onClick={() => toggleStepCollapse(step.id)}
                        className="flex-shrink-0 p-1 rounded hover:bg-gray-100 transition-colors"
                      >
                        {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
                      </button>
                    </div>
                    
                    {/* 步骤详情 */}
                    {!isCollapsed && getStepDetails(step, stepStatus, index)}
                    
                    {/* 时间戳 */}
                    {(stepStatus === 'completed' || isActive) && (
                      <div className="mt-3 text-xs text-gray-500">
                        {stepStatus === 'completed' ? '完成时间' : '开始时间'}: {new Date().toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Effects
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    setShowOptimization(!!selectedText)
  }, [selectedText])

  useEffect(() => {
    if (agentStatus) {
      setCurrentPipelineState({ isActive: true, currentAgent: agentStatus.agent, agentStatus })
      // 不再自动隐藏完成的流水线，让用户能看到完整的执行结果
      // if (agentStatus.status === 'completed' || agentStatus.action === 'bid_build_completed') {
      //   setTimeout(() => setCurrentPipelineState(prev => ({ ...prev, isActive: false })), 8000)
      // }
    }
  }, [agentStatus])

  // Handlers
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() && attachedFiles.length === 0) return
    if (loading) return

    const hasWordFiles = attachedFiles.some(file => 
      file.type.includes('word') || file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc')
    )
    
    if (hasWordFiles && !input.trim()) {
      setInput('请帮我分析这份招标文件并生成投标方案')
    }

    onSendMessage(input.trim() || '请帮我分析这份招标文件并生成投标方案', attachedFiles)
    setInput('')
    setAttachedFiles([])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setAttachedFiles(Array.from(e.target.files))
  }

  const removeFile = (index: number) => {
    setAttachedFiles(files => files.filter((_, i) => i !== index))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
  }

    const getAgentDisplayName = (agent: string) => {
      const names = {
        'coordinator': '🤝 协调器',
        'structure_extractor': '🔍 A-结构抽取',
        'spec_extractor': '📄 B-规格提取',
        'plan_outliner': '✏️ C-方案提纲',
        'bid_assembler': '🧩 D-草案拼装',
        'sanity_checker': '✅ E-完整性校验'
      }
      return names[agent as keyof typeof names] || agent
    }

  const getActionDisplayName = (action: string) => {
    const actions = {
      'analyzing_request': '正在分析用户请求...',
      'bid_build_completed': '已完成投标文件生成',
      'processing': '正在处理...'
    }
    return actions[action as keyof typeof actions] || action
  }

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'success':
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
      case 'error': return <XCircle className="h-4 w-4 text-red-600" />
      default: return <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
    }
  }

  const modelOptions = [
    { id: 'deepseek/deepseek-chat-v3.1', name: 'DeepSeek Chat v3.1', description: '高级推理模型' },
    { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', description: '成熟性能' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', description: 'OpenAI多模态' }
  ]

  // 处理消息内容，过滤非关键信息
  const filterMessageContent = (content: string): string => {
    return content
      .replace(/成功解析了\s*\d+\s*个文档[\s\S]*?wiki文件夹。\s*/g, '')
      .replace(/📄\s*\*\*解析结果\*\*:[\s\S]*?工作流。\s*/g, '')
      .replace(/✅\s*已完成A–E链路生成以下文件:[\s\S]*?(?=\n\n|$)/g, '')
      .trim()
  }

  return (
    <div className="h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-5">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <Send className="h-8 w-8 mx-auto opacity-50 mb-4" />
            <p className="font-medium">💼 智能投标助手</p>
            <p className="text-sm mt-2">{sessionId ? '欢迎回来，继续您的项目' : '开始您的智能投标之旅'}</p>
            <div className="mt-4 text-xs space-y-2">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-blue-800">
                <p className="font-medium mb-1">📄 快速开始：</p>
                <p>1. 点击下方"📎"按钮上传Word招标文件</p>
                <p>2. 系统将自动解析并启动A-E智能体流水线</p>
                <p>3. 一键生成专业投标方案</p>
              </div>
              <p>🚀 支持PDF、DOCX、TXT、MD格式</p>
            </div>
          </div>
        ) : (
          <>
            {/* 消息列表 */}
            {messages.map((message) => {
              const filteredContent = filterMessageContent(message.content)
              
              // 如果消息内容被过滤掉，则不显示
              if (!filteredContent.trim()) return null
              
              return (
                <div key={message.id} className={cn("flex", message.role === 'user' ? 'justify-end' : 'justify-start')}>
                  <div className={cn("max-w-[95%] rounded-lg px-4 py-3 text-sm", 
                    message.role === 'user' ? "bg-primary text-primary-foreground" : "bg-muted text-foreground")}>
                    
                    {/* Agent Information Header */}
                    {message.role === 'assistant' && message.metadata?.current_agent && (
                      <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4 mb-3">
                        <div className="flex items-center gap-3">
                          <Bot className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900">{getAgentDisplayName(message.metadata.current_agent)} Agent</span>
                          {message.metadata.stage && (
                            <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">• {message.metadata.stage}</span>
                          )}
                          {getStatusIcon(message.metadata.status)}
                        </div>
                        {message.metadata.action && (
                          <div className="text-sm text-blue-900 mt-2">{getActionDisplayName(message.metadata.action)}</div>
                        )}
                        {message.metadata.files_created && message.metadata.files_created.length > 0 && (
                          <div className="text-xs text-blue-700 bg-blue-100 p-2 rounded mt-2">
                            已生成文件: {message.metadata.files_created.map((file: any) => file.name).join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="text-sm whitespace-pre-wrap">{filteredContent}</div>
                    
                    {message.timestamp && (
                      <div className="text-xs text-blue-600 mt-3 text-right">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* 新的时间线样式流水线进度显示 - 放在消息之后 */}
            {(loading || agentStatus || currentPipelineState.isActive) && renderTimelinePipelineProgress(
              agentStatus?.agent || currentPipelineState.currentAgent, 
              agentStatus || currentPipelineState.agentStatus
            )}
            
            {/* 简单加载状态 */}
            {loading && !agentStatus && !currentPipelineState.isActive && (
              <div className="flex justify-start">
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                    <span className="text-blue-900">正在处理您的请求...</span>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Optimization Panel */}
      {showOptimization && selectedText && (
        <OptimizationPanel selectedText={selectedText} onOptimize={onOptimizeText} onClose={() => setShowOptimization(false)} />
      )}

      {/* Input Area */}
      <div className="border-t border-border flex-shrink-0">
        {/* Model Selection */}
        <div className="px-4 pt-4 pb-3 border-b border-border/50">
          <div className="flex items-center gap-3">
            <Settings className="h-4 w-4 text-muted-foreground" />
            <div className="relative flex-1">
              <button onClick={() => setShowModelOptions(!showModelOptions)} 
                className="text-sm font-medium text-foreground hover:text-primary flex items-center gap-1">
                {modelOptions.find(m => m.id === selectedModel)?.name}
                <ChevronDown className="h-3 w-3" />
              </button>
              {showModelOptions && (
                <div className="absolute bottom-full left-0 mb-2 bg-background border border-border rounded-lg shadow-lg p-2 z-10 min-w-72">
                  {modelOptions.map((model) => (
                    <button key={model.id} onClick={() => { setSelectedModel(model.id); setShowModelOptions(false) }}
                      className={cn("w-full text-left px-4 py-3 rounded text-sm hover:bg-muted transition-colors", 
                        selectedModel === model.id && "bg-muted")}>
                      <div className="font-medium">{model.name}</div>
                      <div className="text-xs text-muted-foreground">{model.description}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4">
          {/* Attached Files */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 space-y-2">
              {attachedFiles.map((file, index) => (
                <div key={`${file.name}-${index}`} className="flex items-center gap-2 text-xs bg-muted p-2 rounded">
                  <File className="h-4 w-4" />
                  <span className="flex-1 truncate">{file.name}</span>
                  <span className="text-muted-foreground">{formatFileSize(file.size)}</span>
                  <button onClick={() => removeFile(index)} className="p-1 hover:bg-background rounded">
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
                placeholder="输入您的消息..." 
                className="w-full px-4 py-3 bg-background border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                rows={3} style={{ minHeight: '80px', maxHeight: '200px' }} />
            </div>
            
            <div className="flex flex-col gap-2">
              <input ref={fileInputRef} type="file" multiple onChange={handleFileSelect} 
                accept=".pdf,.docx,.txt,.md" className="hidden" />
              <button type="button" onClick={() => fileInputRef.current?.click()}
                className="p-3 hover:bg-muted rounded-lg transition-colors" title="添加文件">
                <Paperclip className="h-5 w-5" />
              </button>
              <button type="submit" disabled={(!input.trim() && attachedFiles.length === 0) || loading}
                className="p-3 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
                <Send className="h-5 w-5" />
              </button>
            </div>
          </form>
          
          <div className="mt-3 text-xs text-muted-foreground">按 Enter 发送，Shift+Enter 换行</div>
        </div>
      </div>
    </div>
  )
}
