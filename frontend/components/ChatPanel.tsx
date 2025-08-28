'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, Wand2, Upload, X, File, Bot, ChevronDown, ChevronUp, Settings, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
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
}

export function ChatPanel({ 
  messages, 
  onSendMessage, 
  onOptimizeText,
  selectedText, 
  loading,
  sessionId,
  agentStatus
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [showOptimization, setShowOptimization] = useState(false)
  const [showAgentDetails, setShowAgentDetails] = useState(true)
  const [selectedModel, setSelectedModel] = useState('deepseek/deepseek-chat-v3.1')
  const [showModelOptions, setShowModelOptions] = useState(false)
  const [showThinkingProcess, setShowThinkingProcess] = useState(false)
  const [collapsedMessages, setCollapsedMessages] = useState<Set<string>>(new Set())
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const toggleMessageCollapse = (messageId: string) => {
    setCollapsedMessages(prev => {
      const newSet = new Set(prev)
      if (newSet.has(messageId)) {
        newSet.delete(messageId)
      } else {
        newSet.add(messageId)
      }
      return newSet
    })
  }
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (selectedText) {
      setShowOptimization(true)
    } else {
      setShowOptimization(false)
    }
  }, [selectedText])

  useEffect(() => {
    if (agentStatus) {
      // Determine status based on agent and action
      let status: 'processing' | 'success' | 'failed' | 'completed' = 'processing'
      
      if (agentStatus.agent === 'completed') {
        status = 'success'
      } else if (agentStatus.action.includes('error') || agentStatus.status === 'failed') {
        status = 'failed'
      } else if (agentStatus.status === 'success' || agentStatus.status === 'completed') {
        status = 'success'
      } else if (agentStatus.action.includes('finished') || agentStatus.action.includes('completed')) {
        status = 'success'
      }
      
      // 不再需要更新执行历史，因为执行信息现在直接显示在消息中
      // const statusWithTimestamp = {
      //   ...agentStatus,
      //   timestamp: new Date().toISOString(),
      //   status: status
      // }
    }
  }, [agentStatus])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() && attachedFiles.length === 0) return
    if (loading) return

    onSendMessage(input.trim(), attachedFiles)
    setInput('')
    setAttachedFiles([])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setAttachedFiles(Array.from(e.target.files))
    }
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
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getAgentDisplayName = (agent: string) => {
    const names: Record<string, string> = {
      'coordinator': '🤝 Coordinator',
      'planner': '📋 Planner',
      'researcher': '🔍 Researcher',
      'writer': '✍️ Writer',
      'optimizer': '✨ Optimizer',
      'completed': '✅ Completed'
    }
    return names[agent] || agent
  }

  const getActionDisplayName = (action: string) => {
    const actions: Record<string, string> = {
      'analyzing_request': '正在分析您的请求并确定执行流程...',
      'processing_files': '正在处理上传的文件进行调研分析...',
      'creating_plan': '正在创建详细的项目计划和提纲...',
      'generating_content': '正在创建全面的内容...',
      'optimizing_text': '正在优化和润色文本...',
      'research_in_progress': '正在进行文档分析和调研...',
      'planning_in_progress': '正在制定结构化计划和提纲...',
      'writing_in_progress': '正在撰写完整的解决方案内容...',
      'optimization_requested': '正在进行文本优化...',
      'awaiting_plan_confirmation': '等待您确认计划...',
      'finished': '任务完成！',
      'writing_completed': '内容创作完成 ✅',
      'plan_created': '计划制定完成 ✅',
      'research_completed': '研究分析完成 ✅',
      'optimization_completed': '文本优化完成 ✅'
    }
    return actions[action] || action
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      case 'processing':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-yellow-50 border-yellow-200'
    }
  }

  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return 'text-green-800'
      case 'failed':
        return 'text-red-800'
      case 'processing':
        return 'text-blue-800'
      default:
        return 'text-yellow-800'
    }
  }

  const shouldCollapseMessage = (message: Message) => {
    // 如果有执行详情，总是可以折叠
    if (message.metadata?.execution_details) {
      return true
    }
    
    // 如果消息内容很长，可以折叠
    if (message.content.length > 200) {
      return true
    }
    
    // 如果有生成的文件信息，可以折叠
    if (message.metadata?.files_created && message.metadata.files_created.length > 0) {
      return true
    }
    
    // 对于智能体消息，总是可以折叠以显示详细信息
    if (message.role === 'assistant' && message.metadata?.current_agent) {
      return true
    }
    
    return false
  }

  const getCollapsedPreview = (content: string) => {
    const lines = content.split('\n')
    const firstLines = lines.slice(0, 3).join('\n')
    return firstLines.length > 150 ? firstLines.substring(0, 150) + '...' : firstLines
  }

  const getExecutionDetailsPreview = (executionDetails: any[]) => {
    if (!executionDetails || executionDetails.length === 0) return ''
    
    const completedCount = executionDetails.filter(d => d.status === 'success' || d.status === 'completed').length
    const totalCount = executionDetails.length
    
    return `${completedCount}/${totalCount} 个智能体已完成任务`
  }

  const getMessagePreview = (message: Message) => {
    // 如果有执行详情，显示执行状态预览
    if (message.metadata?.execution_details) {
      return getExecutionDetailsPreview(message.metadata.execution_details)
    }
    
    // 如果有生成的文件，显示文件信息
    if (message.metadata?.files_created && message.metadata.files_created.length > 0) {
      return `已生成 ${message.metadata.files_created.length} 个文件`
    }
    
    // 如果内容很长，显示内容预览
    if (message.content.length > 200) {
      return getCollapsedPreview(message.content)
    }
    
    // 默认显示完整内容
    return message.content
  }

  const inferAgentExecutionFromMessage = (message: Message) => {
    const agents: any[] = []
    
    // 如果没有元数据，返回空数组
    if (!message.metadata) {
      return agents
    }
    
    // 根据当前智能体类型推断执行状态
    const currentAgent = message.metadata.current_agent
    if (!currentAgent) {
      return agents
    }
    
    // 动态推断智能体状态，基于实际消息内容
    const agentInfo = {
      agent: currentAgent,
      action: message.metadata.action || 'processing',
      status: message.metadata.status || 'processing',
      timestamp: message.timestamp,
      input: message.metadata.input || message.metadata.user_request || '用户请求',
      output: message.metadata.output || message.metadata.result || message.content.substring(0, 100) + '...'
    }
    
    // 根据智能体类型和消息内容推断具体的执行状态
    if (currentAgent === 'coordinator') {
      // 协调者智能体：分析请求并规划执行流程
      agentInfo.action = message.metadata.action || 'analyzing_request'
      agentInfo.output = message.metadata.output || '正在分析用户请求并规划执行流程...'
    } else if (currentAgent === 'planner') {
      // 规划者智能体：创建执行计划
      agentInfo.action = message.metadata.action || 'creating_plan'
      agentInfo.output = message.metadata.output || '正在创建结构化执行计划...'
    } else if (currentAgent === 'researcher') {
      // 研究者智能体：进行调研分析
      agentInfo.action = message.metadata.action || 'researching'
      agentInfo.output = message.metadata.output || '正在进行相关调研和分析...'
    } else if (currentAgent === 'writer') {
      // 写作者智能体：创建内容
      agentInfo.action = message.metadata.action || 'writing'
      agentInfo.output = message.metadata.output || '正在创建内容...'
    } else if (currentAgent === 'optimizer') {
      // 优化者智能体：优化内容
      agentInfo.action = message.metadata.action || 'optimizing'
      agentInfo.output = message.metadata.output || '正在优化和润色内容...'
    }
    
    // 根据消息内容长度和元数据推断执行进度
    if (message.content.length > 500) {
      agentInfo.status = 'completed'
    } else if (message.content.length > 100) {
      agentInfo.status = 'processing'
    } else {
      agentInfo.status = 'processing'
    }
    
    // 如果有执行详情，使用实际的执行状态
    if (message.metadata.execution_details) {
      agentInfo.status = message.metadata.execution_details.status || agentInfo.status
      agentInfo.output = message.metadata.execution_details.output || agentInfo.output
    }
    
    // 如果有文件创建信息，更新输出描述
    if (message.metadata.files_created && message.metadata.files_created.length > 0) {
      agentInfo.output = `已生成 ${message.metadata.files_created.length} 个文件`
      agentInfo.status = 'completed'
    }
    
    agents.push(agentInfo)
    
    return agents
  }

  const modelOptions = [
    { id: 'deepseek/deepseek-chat-v3.1', name: 'DeepSeek Chat v3.1', description: '高级推理模型' },
    { id: 'z-ai/glm-4.5v', name: 'GLM-4.5V', description: '多模态理解' },
    { id: 'anthropic/claude-sonnet-4', name: 'Claude Sonnet 4', description: '最新Anthropic模型' },
    { id: 'openai/gpt-5-mini', name: 'GPT-5 Mini', description: '高效OpenAI模型' },
    { id: 'anthropic/claude-3.5-sonnet', name: 'Claude 3.5 Sonnet', description: '成熟性能' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', description: 'OpenAI多模态' }
  ]

  const isThinkingModel = selectedModel.startsWith('o1')

  return (
    <div className="h-full flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-auto p-4 space-y-5">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <div className="mb-4">
              <Send className="h-8 w-8 mx-auto opacity-50" />
            </div>
            <p className="font-medium">欢迎使用解决方案智能体</p>
            <p className="text-sm mt-2">
              {sessionId ? '继续您的对话' : '开始新的对话'}
            </p>
            <div className="mt-4 text-xs space-y-1">
              <p>尝试: "帮我写一份产品发布会策划案"</p>
              <p>或上传文件进行分析</p>
            </div>
          </div>
        ) : (
          messages.map((message) => {
            // If this is an assistant message with execution details, render each agent as separate blocks
            if (message.role === 'assistant' && message.metadata?.execution_details) {
              return (
                <div key={message.id} className="space-y-4">
                  {/* Main message content */}
                  <div className="flex justify-start">
                    <div className="max-w-[95%] rounded-lg px-4 py-3 text-sm bg-muted text-foreground">
                      {/* Agent Information Header */}
                      {message.metadata.current_agent && (
                        <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4 mb-3">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <Bot className="h-4 w-4 text-blue-600" />
                              <span className="text-sm font-medium text-blue-900">
                                {getAgentDisplayName(message.metadata.current_agent)} Agent
                              </span>
                              {message.metadata.stage && (
                                <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">• {message.metadata.stage}</span>
                              )}
                              {/* Show success/failure indicators */}
                              {message.metadata.status === 'success' || message.metadata.stage === 'project_completed' || message.metadata.stage === 'writing_completed' || message.metadata.stage === 'plan_created' || message.metadata.stage === 'research_completed' ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : message.metadata.status === 'failed' ? (
                                <XCircle className="h-4 w-4 text-red-600" />
                              ) : (
                                <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                              )}
                            </div>
                          </div>
                          
                          {/* 重要信息直接显示 - 只在没有execution_details时显示 */}
                          {!message.metadata.execution_details && message.metadata.action && (
                            <div className="text-sm text-blue-900 mb-2">
                              {getActionDisplayName(message.metadata.action)}
                            </div>
                          )}
                          
                          {/* 错误信息显示 */}
                          {message.metadata.status === 'error' && (
                            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2">
                              <span className="font-medium">⚠️ 执行失败:</span> {message.metadata.error_type === 'incomplete_critical_info' ? '关键信息缺失' : '执行错误'}
                            </div>
                          )}
                          
                          {/* 生成的文件信息 */}
                          {message.metadata.files_created && message.metadata.files_created.length > 0 && (
                            <div className="text-xs text-blue-700 bg-blue-100 p-2 rounded mb-2">
                              已生成文件: {message.metadata.files_created.map((file: any) => file.name).join(', ')}
                            </div>
                          )}
                        </div>
                      )}
                      
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      
                      {/* 添加展开/折叠按钮 */}
                      {message.content.length > 200 && (
                        <button
                          onClick={() => toggleMessageCollapse(message.id)}
                          className="text-xs text-blue-600 hover:text-blue-800 mt-3 font-medium"
                        >
                          {collapsedMessages.has(message.id) ? '展开详情 →' : '折叠详情 ←'}
                        </button>
                      )}
                      
                      {message.timestamp && (
                        <div className="text-xs text-blue-600 mt-3 text-right">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Individual agent blocks */}
                  {message.metadata.execution_details.map((detail: any, index: number) => (
                    <div key={`${message.id}-agent-${index}`} className="flex justify-start">
                      <div className="max-w-[95%] rounded-lg px-4 py-3 text-sm bg-blue-50 border border-blue-200">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(detail.status || 'processing')}
                            <span className="font-medium text-blue-900">
                              {getAgentDisplayName(detail.agent)}
                            </span>
                            {detail.status === 'success' && (
                              <CheckCircle className="h-3 w-3 text-green-600" />
                            )}
                            {detail.status === 'failed' && (
                              <XCircle className="h-3 w-3 text-red-600" />
                            )}
                          </div>
                          {detail.timestamp && (
                            <span className="text-xs text-blue-600 text-nowrap">
                              {new Date(detail.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </span>
                          )}
                        </div>
                        
                        {/* 输入信息 */}
                        {detail.input && (
                          <div className="mb-2">
                            <div className="text-xs text-blue-700 font-medium mb-1">输入:</div>
                            <div className="text-xs text-blue-800 bg-blue-100 p-2 rounded">
                              {detail.input}
                            </div>
                          </div>
                        )}
                        
                        {/* 输出信息 */}
                        {detail.output && (
                          <div className="mb-2">
                            <div className="text-xs text-blue-700 font-medium mb-1">输出:</div>
                            <div className="text-xs text-blue-800 bg-blue-100 p-2 rounded">
                              {detail.output}
                            </div>
                          </div>
                        )}
                        
                        {/* 动作描述 */}
                        <div className="text-xs text-blue-700">
                          {getActionDisplayName(detail.action)}
                        </div>
                        
                        {/* 错误信息 */}
                        {detail.error && (
                          <div className="mt-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
                            <span className="font-medium">错误:</span> {detail.error}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {/* 生成的文件信息 */}
                  {message.metadata?.files_created && message.metadata.files_created.length > 0 && (
                    <div className="flex justify-start">
                      <div className="max-w-[95%] rounded-lg px-4 py-3 text-sm bg-blue-50 border border-blue-200">
                        <div className="text-xs text-blue-700 mb-2 font-medium">已创建文件:</div>
                        <div className="space-y-1">
                          {message.metadata.files_created.map((file: any, i: number) => (
                            <div key={`${message.id}-file-${file.name}-${i}`} className="text-xs text-blue-800 bg-blue-100 p-2 rounded flex items-center gap-2">
                              <File className="h-3 w-3 text-blue-600" />
                              <span className="font-medium">{file.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            }
            
            // 对于没有execution_details的智能体消息，使用简化的渲染逻辑
            if (message.role === 'assistant' && message.metadata?.current_agent && !message.metadata?.execution_details) {
              
              return (
                <div key={message.id} className="space-y-4">
                  {/* Main message content */}
                  <div className="flex justify-start">
                    <div className="max-w-[95%] rounded-lg px-4 py-3 text-sm bg-muted text-foreground">
                      {/* Agent Information Header */}
                      <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4 mb-3">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <Bot className="h-4 w-4 text-blue-600" />
                            <span className="text-sm font-medium text-blue-900">
                              {getAgentDisplayName(message.metadata.current_agent)} Agent
                            </span>
                            {message.metadata.stage && (
                              <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">• {message.metadata.stage}</span>
                            )}
                            {/* Show success/failure indicators */}
                            {message.metadata.status === 'success' || message.metadata.stage === 'project_completed' || message.metadata.stage === 'writing_completed' || message.metadata.stage === 'plan_created' || message.metadata.stage === 'research_completed' ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : message.metadata.status === 'failed' ? (
                              <XCircle className="h-4 w-4 text-red-600" />
                            ) : (
                              <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                            )}
                          </div>
                        </div>
                        
                        {/* 重要信息直接显示 */}
                        <div className="text-sm text-blue-900 mb-2">
                          {message.metadata.action && getActionDisplayName(message.metadata.action)}
                        </div>
                        
                        {/* 生成的文件信息 */}
                        {message.metadata.files_created && message.metadata.files_created.length > 0 && (
                          <div className="text-xs text-blue-700 bg-blue-100 p-2 rounded mb-2">
                            已生成文件: {message.metadata.files_created.map((file: any) => file.name).join(', ')}
                          </div>
                        )}
                      </div>
                      
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      
                      {/* 添加展开/折叠按钮 */}
                      {message.content.length > 200 && (
                        <button
                          onClick={() => toggleMessageCollapse(message.id)}
                          className="text-xs text-blue-600 hover:text-blue-800 mt-3 font-medium"
                        >
                          {collapsedMessages.has(message.id) ? '展开详情 →' : '折叠详情 ←'}
                        </button>
                      )}
                      
                      {message.timestamp && (
                        <div className="text-xs text-blue-600 mt-3 text-right">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* 不再显示推断的智能体块，避免重复信息 */}
                  {/* 如果需要显示详细的执行信息，可以在主消息头部添加 */}
                  
                  {/* 生成的文件信息 */}
                  {message.metadata?.files_created && message.metadata.files_created.length > 0 && (
                    <div className="flex justify-start">
                      <div className="max-w-[95%] rounded-lg px-4 py-3 text-sm bg-blue-50 border border-blue-200">
                        <div className="text-xs text-blue-700 mb-2 font-medium">已创建文件:</div>
                        <div className="space-y-1">
                          {message.metadata.files_created.map((file: any, i: number) => (
                            <div key={`${message.id}-file-${file.name}-${i}`} className="text-xs text-blue-800 bg-blue-100 p-2 rounded flex items-center gap-2">
                              <File className="h-3 w-3 text-blue-600" />
                              <span className="font-medium">{file.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            }
            
            // Regular message rendering for other messages
            return (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    "max-w-[95%] rounded-lg px-4 py-3 text-sm",
                    message.role === 'user'
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  )}
                >
                  {/* Agent Information Header for Assistant Messages */}
                  {message.role === 'assistant' && message.metadata?.current_agent && (
                    <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4 mb-3">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Bot className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900">
                            {getAgentDisplayName(message.metadata.current_agent)} Agent
                          </span>
                          {message.metadata.stage && (
                            <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">• {message.metadata.stage}</span>
                          )}
                          {/* Show success/failure indicators based on stage and status */}
                          {message.metadata.status === 'success' || message.metadata.stage === 'project_completed' || message.metadata.stage === 'writing_completed' || message.metadata.stage === 'plan_created' || message.metadata.stage === 'research_completed' ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : message.metadata.status === 'failed' ? (
                            <XCircle className="h-4 w-4 text-red-600" />
                          ) : (
                            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
                          )}
                        </div>
                        
                        {/* 添加折叠按钮 */}
                        {(message.metadata.execution_details || message.content.length > 200) && (
                          <button
                            onClick={() => toggleMessageCollapse(message.id)}
                            className="p-1 hover:bg-blue-100 rounded transition-colors"
                            title={collapsedMessages.has(message.id) ? '展开详情' : '折叠详情'}
                          >
                            {collapsedMessages.has(message.id) ? (
                              <ChevronDown className="h-4 w-4 text-blue-600" />
                            ) : (
                              <ChevronUp className="h-4 w-4 text-blue-600" />
                            )}
                          </button>
                        )}
                      </div>
                      
                      {/* 重要信息直接显示 - 只在没有execution_details时显示 */}
                      {!message.metadata.execution_details && message.metadata.action && (
                        <div className="text-sm text-blue-900 mb-2">
                          {getActionDisplayName(message.metadata.action)}
                        </div>
                      )}
                      
                      {/* 错误信息显示 */}
                      {message.metadata.status === 'error' && (
                        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2">
                          <span className="font-medium">⚠️ 执行失败:</span> {message.metadata.error_type === 'incomplete_critical_info' ? '关键信息缺失' : '执行错误'}
                        </div>
                      )}
                      
                      {/* 生成的文件信息 */}
                      {message.metadata.files_created && message.metadata.files_created.length > 0 && (
                        <div className="text-xs text-blue-700 bg-blue-100 p-2 rounded mb-2">
                          已生成文件: {message.metadata.files_created.map((file: any) => file.name).join(', ')}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="whitespace-pre-wrap">
                    {collapsedMessages.has(message.id) && shouldCollapseMessage(message) ? (
                      <>
                        {/* 折叠状态下的重要信息预览 */}
                        <div className="text-sm text-muted-foreground mb-3">
                          {getMessagePreview(message)}
                        </div>
                        
                        <button
                          onClick={() => toggleMessageCollapse(message.id)}
                          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        >
                          展开详情 →
                        </button>
                      </>
                    ) : shouldCollapseMessage(message) ? (
                      <>
                        <div className="text-sm">{message.content}</div>
                        
                        <button
                          onClick={() => toggleMessageCollapse(message.id)}
                          className="text-xs text-blue-600 hover:text-blue-800 mt-3 font-medium"
                        >
                          折叠详情 ←
                        </button>
                      </>
                    ) : (
                      <div className="text-sm">{message.content}</div>
                    )}
                  </div>
                  
                  {message.metadata?.files_created && message.metadata.files_created.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200/30">
                      <div className="text-xs text-blue-700 mb-2 font-medium">已创建文件:</div>
                      <div className="space-y-1">
                        {message.metadata.files_created.map((file: any, i: number) => (
                          <div key={`${message.id}-file-${file.name}-${i}`} className="text-xs text-blue-800 bg-blue-100 p-2 rounded flex items-center gap-2">
                            <File className="h-3 w-3 text-blue-600" />
                            <span className="font-medium">{file.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {message.timestamp && (
                    <div className="text-xs text-blue-600 mt-3 text-right">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
        
        {(loading || agentStatus) && (
          <div className="space-y-3">
            {/* Agent Status Display */}
            {agentStatus && (
              <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <Bot className="h-4 w-4 text-blue-600" />
                    <span className="font-medium text-blue-900">
                      {getAgentDisplayName(agentStatus.agent)}
                    </span>
                    {getStatusIcon(agentStatus.status || 'processing')}
                  </div>
                  <button
                    onClick={() => setShowAgentDetails(!showAgentDetails)}
                    className="p-1 hover:bg-blue-100 rounded transition-colors"
                    title={showAgentDetails ? '折叠详情' : '展开详情'}
                  >
                    {showAgentDetails ? (
                      <ChevronUp className="h-3 w-3 text-blue-600" />
                    ) : (
                      <ChevronDown className="h-3 w-3 text-blue-600" />
                    )}
                  </button>
                </div>
                
                {/* 重要信息直接显示 */}
                <div className="text-sm text-blue-900 mb-2">
                  {getActionDisplayName(agentStatus.action)}
                </div>
                
                {/* 可折叠的详细信息 */}
                {showAgentDetails && (
                  <div className="mt-3 pt-3 border-t border-blue-200/50">
                    <div className="text-xs text-blue-700 space-y-2">
                      {agentStatus.error && (
                        <div className="bg-red-50 border border-red-200 rounded p-2">
                          <span className="font-medium">错误:</span> {agentStatus.error}
                        </div>
                      )}
                      {agentStatus.timestamp && (
                        <div className="text-blue-600">
                          时间: {new Date(agentStatus.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                      {/* 可以在这里添加更多详细信息 */}
                    </div>
                  </div>
                )}
              </div>
            )}
            
            {/* Loading fallback */}
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
        
        {/* 移除智能体执行记录部分 */}
      </div>

      {/* Optimization Panel */}
      {showOptimization && selectedText && (
        <OptimizationPanel
          selectedText={selectedText}
          onOptimize={onOptimizeText}
          onClose={() => setShowOptimization(false)}
        />
      )}

      {/* Input Area */}
      <div className="border-t border-border">
        {/* Model Selection */}
        <div className="px-4 pt-4 pb-3 border-b border-border/50">
          <div className="flex items-center gap-3">
            <Settings className="h-4 w-4 text-muted-foreground" />
            <div className="relative flex-1">
              <button
                onClick={() => setShowModelOptions(!showModelOptions)}
                className="text-sm font-medium text-foreground hover:text-primary flex items-center gap-1"
                title="模型选择（后端使用配置的模型）"
              >
                {modelOptions.find(m => m.id === selectedModel)?.name}
                <ChevronDown className="h-3 w-3" />
              </button>
              
              {showModelOptions && (
                <div className="absolute bottom-full left-0 mb-2 bg-background border border-border rounded-lg shadow-lg p-2 z-10 min-w-72">
                  {modelOptions.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => {
                        setSelectedModel(model.id)
                        setShowModelOptions(false)
                      }}
                      className={cn(
                        "w-full text-left px-4 py-3 rounded text-sm hover:bg-muted transition-colors",
                        selectedModel === model.id && "bg-muted"
                      )}
                    >
                      <div className="font-medium">{model.name}</div>
                      <div className="text-xs text-muted-foreground">{model.description}</div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            {isThinkingModel && (
              <button
                onClick={() => setShowThinkingProcess(!showThinkingProcess)}
                className={cn(
                  "px-3 py-2 text-xs rounded transition-colors",
                  showThinkingProcess 
                    ? "bg-blue-100 text-blue-700" 
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                )}
              >
                {showThinkingProcess ? '隐藏' : '显示'} 思考过程
              </button>
            )}
          </div>
        </div>

        <div className="p-4">
          {/* Attached Files */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 space-y-2">
              {attachedFiles.map((file, index) => (
                <div
                  key={`attached-file-${file.name}-${file.size}-${index}`}
                  className="flex items-center gap-2 text-xs bg-muted p-2 rounded"
                >
                  <File className="h-4 w-4" />
                  <span className="flex-1 truncate">{file.name}</span>
                  <span className="text-muted-foreground">{formatFileSize(file.size)}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 hover:bg-background rounded"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入您的消息..."
                className="w-full px-4 py-3 bg-background border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                rows={3}
                style={{ minHeight: '80px', maxHeight: '200px' }}
              />
            </div>
            
            <div className="flex flex-col gap-2">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
              />
              
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-3 hover:bg-muted rounded-lg transition-colors"
                title="添加文件"
              >
                <Paperclip className="h-5 w-5" />
              </button>
              
              <button
                type="submit"
                disabled={(!input.trim() && attachedFiles.length === 0) || loading}
                className="p-3 bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </form>
          
          <div className="mt-3 text-xs text-muted-foreground">
            按 Enter 发送，Shift+Enter 换行
          </div>
        </div>
      </div>
    </div>
  )
}