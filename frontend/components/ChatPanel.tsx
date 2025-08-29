'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, X, File, Bot, ChevronDown, ChevronUp, Settings, CheckCircle, XCircle, Clock, Search, Edit, Puzzle, CheckSquare, FileText, Play } from 'lucide-react'
import { cn } from '@/lib/utils'
import { OptimizationPanel } from './OptimizationPanel'
import PipelinePanel from '@/components/PipelinePanel'
import { PIPELINE_ORDER } from '@/lib/pipeline'
import type { AgentEvent } from '@/hooks/usePipelineEvents'

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
  const [tab, setTab] = useState<'pipeline'|'chat'>('pipeline')
  const [pipelineEvents, setPipelineEvents] = useState<AgentEvent[]>([])
  const [selectedModel, setSelectedModel] = useState('deepseek/deepseek-chat-v3.1')
  const [showModelOptions, setShowModelOptions] = useState(false)
  const [currentPipelineState, setCurrentPipelineState] = useState<{
    isActive: boolean
    currentAgent?: string
    agentStatus?: AgentStatus
  }>({ isActive: false })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Pipeline 步骤定义
  const pipelineSteps = [
    { id: 'document_parsing', name: '文档解析', description: '解析招标文件', agent: 'coordinator', icon: 'FileText', agentKey: 'coordinator' },
    { id: 'structure_extraction', name: 'A-结构抽取', description: '提取投标文件格式要求', agent: 'StructureExtractor', icon: 'Search', agentKey: 'structure_extractor' },
    { id: 'spec_extraction', name: 'B-规格书提取', description: '提取技术规格书', agent: 'SpecExtractor', icon: 'FileText', agentKey: 'spec_extractor' },
    { id: 'plan_outlining', name: 'C-方案提纲生成', description: '生成投标方案提纲', agent: 'PlanOutliner', icon: 'Edit', agentKey: 'plan_outliner' },
    { id: 'bid_assembly', name: 'D-草案拼装', description: '拼装投标文件', agent: 'BidAssembler', icon: 'Puzzle', agentKey: 'bid_assembler' },
    { id: 'sanity_check', name: 'E-完整性校验', description: '校验完整性', agent: 'SanityChecker', icon: 'CheckSquare', agentKey: 'sanity_checker' }
  ]

  // 获取图标组件
  const getIconComponent = (iconName: string) => {
    const icons = { Search, FileText, Edit, Puzzle, CheckSquare }
    const Icon = icons[iconName as keyof typeof icons] || FileText
    return <Icon className="h-4 w-4 text-blue-600" />
  }

  // 获取状态图标
  const getPipelineStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'running': return <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
      case 'error': return <XCircle className="h-4 w-4 text-red-600" />
      default: return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  // 渲染流水线进度
  const renderPipelineProgress = (currentAgent?: string, agentStatus?: AgentStatus) => {
    // 从消息历史推断进度
    if (!currentAgent && messages.length > 0) {
      const lastMessage = messages[messages.length - 1]
      if (lastMessage.role === 'assistant' && lastMessage.metadata?.current_agent) {
        currentAgent = lastMessage.metadata.current_agent
        if (lastMessage.content.includes('✅') || lastMessage.content.includes('已完成') || lastMessage.metadata.stage === 'bid_build_completed') {
          agentStatus = { agent: currentAgent!, action: '已完成所有步骤', status: 'completed' }
        }
      }
    }

    if (!currentAgent) return null

    const isAllCompleted = agentStatus?.status === 'completed' && agentStatus?.action?.includes('已完成')
    const completedSteps = isAllCompleted ? pipelineSteps : pipelineSteps.slice(0, Math.max(1, pipelineSteps.findIndex(step => step.agentKey === currentAgent)))
    const progress = (completedSteps.length / pipelineSteps.length) * 100

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Play className="h-4 w-4 text-blue-600" />
            <span className="font-medium text-blue-900">🤖 智能体执行流水线</span>
            {isAllCompleted && <CheckCircle className="h-4 w-4 text-green-600" />}
          </div>
          <span className="text-sm text-blue-700">{completedSteps.length} / {pipelineSteps.length}</span>
        </div>
        
        <div className="mb-4">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div className={`h-2 rounded-full transition-all duration-300 ${isAllCompleted ? 'bg-green-500' : 'bg-blue-500'}`} style={{ width: `${progress}%` }} />
          </div>
          <div className="mt-2 text-sm">
            {isAllCompleted ? (
              <span className="text-green-600">✅ 所有步骤已完成</span>
            ) : (
              <span className="text-blue-600">⚡ 正在执行: {pipelineSteps.find(step => step.agentKey === currentAgent)?.name}</span>
            )}
          </div>
        </div>

        <div className="space-y-2">
          {pipelineSteps.map((step, index) => {
            const status = isAllCompleted ? 'completed' : (step.agentKey === currentAgent ? 'running' : (index < completedSteps.length ? 'completed' : 'pending'))
            const isActive = !isAllCompleted && step.agentKey === currentAgent
            
            return (
              <div key={step.id} className={`flex items-center gap-3 p-2 rounded ${isActive ? 'bg-blue-100' : ''}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                  status === 'completed' ? 'bg-green-100 text-green-700' :
                  status === 'running' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {index === 0 ? '解析' : String.fromCharCode(64 + index)}
                </div>
                <div className="flex-shrink-0">{getPipelineStatusIcon(status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{step.name}</span>
                    {getIconComponent(step.icon)}
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{step.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }
  // 收集 pipeline 事件（由后端 agent_status 推断）
  useEffect(() => {
    // 从 messages 中提取 agent_status 风格的元数据（适配现有返回）
    const events: AgentEvent[] = []
    for (const m of messages) {
      if (m.role === 'assistant' && m.metadata) {
        const md: any = m.metadata
        if (md.stage || md.action || md.current_agent) {
          events.push({
            ts: Date.now(),
            sessionId: sessionId || '',
            stage: md.stage,
            agent: md.current_agent,
            action: md.action,
            status: (md.status as any) || (md.stage === 'bid_build_completed' ? 'succeeded' : undefined),
            meta: md,
          })
        }
      }
    }
    setPipelineEvents(events)
  }, [messages, sessionId])


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
      if (agentStatus.status === 'completed' || agentStatus.action === 'bid_build_completed') {
        setTimeout(() => setCurrentPipelineState(prev => ({ ...prev, isActive: false })), 8000)
      }
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

  return (
    <div className="h-full flex flex-col">
      {/* Pipeline/Chat Tabs */}
      <div className="px-4 pt-4 border-b border-border/50">
        <div className="flex items-center gap-2">
          <button onClick={() => setTab('pipeline')} className={`px-3 py-1 rounded ${tab==='pipeline'?'bg-black text-white':'bg-gray-100'}`}>Pipeline</button>
          <button onClick={() => setTab('chat')} className={`px-3 py-1 rounded ${tab==='chat'?'bg-black text-white':'bg-gray-100'}`}>Chat</button>
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-auto p-4 space-y-5">
        {tab === 'pipeline' ? (
          <PipelinePanel events={pipelineEvents} />
        ) : (
          <>
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
          messages.map((message) => (
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
                
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                
                {message.timestamp && (
                  <div className="text-xs text-blue-600 mt-3 text-right">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {/* Pipeline Progress Display */}
        {(loading || agentStatus || currentPipelineState.isActive) && (
          <div className="space-y-3">
            {(agentStatus || currentPipelineState.isActive) && renderPipelineProgress(
              agentStatus?.agent || currentPipelineState.currentAgent, 
              agentStatus || currentPipelineState.agentStatus
            )}
            
            {agentStatus && (
              <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Bot className="h-4 w-4 text-blue-600" />
                  <span className="font-medium text-blue-900">{getAgentDisplayName(agentStatus.agent)}</span>
                  {getStatusIcon(agentStatus.status)}
                </div>
                <div className="text-sm text-blue-900">{getActionDisplayName(agentStatus.action)}</div>
                {agentStatus.timestamp && (
                  <div className="text-xs text-blue-600 mt-2">
                    时间: {new Date(agentStatus.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            )}
            
            {loading && !agentStatus && (
              <div className="flex justify-start">
                <div className="bg-muted text-foreground rounded-lg px-4 py-3 text-sm">
                  <div className="flex items-center gap-3">
                    <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                    处理中...
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
          </>
        )}
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