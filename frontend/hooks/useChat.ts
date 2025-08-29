'use client'

import { useState, useCallback, useRef, useEffect } from 'react'

// ------------------------------
// Types
// ------------------------------
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

export interface AgentStatus {
  agent: string
  action: string
}

export type CreatedFileType = 'plan' | 'proposal' | 'other'

export interface ServerFile {
  name: string
  content: string
}

export interface CreatedFile extends ServerFile {
  type: CreatedFileType
}

export interface ChatOptions {
  onFilesCreated?: (files: CreatedFile[]) => void
  onSessionUpdate?: () => void
  onSessionReady?: (sessionId: string) => void
}

// SSE events coming from the server
interface SessionEvent {
  type: 'session'
  session_id?: string
}

interface AgentStatusEvent {
  type: 'agent_status'
  agent: string
  action: string
}

interface FileUpdateEvent {
  type: 'file_update'
  files_created?: ServerFile[]
}

interface MessageEvent {
  type: 'message'
  session_id?: string
  message: string
  metadata?: Record<string, unknown>
  files_created?: ServerFile[]
}

interface ErrorEvent {
  type: 'error'
  message: string
}

interface DoneEvent {
  type: 'done'
}

type SSEEvent =
  | SessionEvent
  | AgentStatusEvent
  | FileUpdateEvent
  | MessageEvent
  | ErrorEvent
  | DoneEvent

// ------------------------------
// Helpers
// ------------------------------
const classifyFileType = (name: string): CreatedFileType => {
  if (name === '投标文件.md') return 'proposal'
  if (name.toUpperCase().includes('PLAN')) return 'plan'
  if (name.toUpperCase().includes('PROPOSAL')) return 'proposal'
  return 'other'
}

const ensureServerFiles = (value: unknown): ServerFile[] => {
  if (!Array.isArray(value)) return []
  return (value as unknown[]).filter((f): f is ServerFile => {
    return (
      typeof (f as any)?.name === 'string' &&
      typeof (f as any)?.content === 'string'
    )
  })
}

const makeCreatedFiles = (serverFiles: ServerFile[]): CreatedFile[] =>
  serverFiles.map((f) => ({
    name: f.name,
    content: f.content,
    type: classifyFileType(f.name),
  }))

const generateMessageId = (): string => {
  try {
    // @ts-ignore crypto may exist in browser env
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      // @ts-ignore
      return crypto.randomUUID()
    }
  } catch {}
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

// ------------------------------
// Hook
// ------------------------------
export function useChat(sessionId: string | null, options?: ChatOptions) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [currentContent, setCurrentContent] = useState<string>('')
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null)
  const currentSessionId = useRef<string | null>(sessionId)

  // Load past conversation for a session
  const loadConversationHistory = useCallback(async (id: string) => {
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/${id}`)
      if (!response.ok) return

      const data = await response.json()
      const history = (data?.data?.conversation_history ?? []) as any[]

      const formattedMessages: Message[] = history.map((msg) => ({
        id: msg.id || generateMessageId(),
        role: msg.role as Message['role'],
        content: String(msg.content ?? ''),
        metadata: msg.metadata as Record<string, unknown> | undefined,
        timestamp: msg.timestamp as string | undefined,
      }))

      setMessages(formattedMessages)
      setCurrentContent(String(data?.data?.current_content ?? ''))
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('Failed to load conversation history:', err)
    }
  }, [])

  // React to sessionId prop changes (avoid state updates during render)
  useEffect(() => {
    const previousSessionId = currentSessionId.current
    currentSessionId.current = sessionId

    if (sessionId && previousSessionId && sessionId !== previousSessionId) {
      // Switching between two non-null sessions => load history
      loadConversationHistory(sessionId)
    } else if (!sessionId && previousSessionId) {
      // Explicitly going to no session => clear
      setMessages([])
      setCurrentContent('')
    }
  }, [sessionId, loadConversationHistory])

  const sendMessage = useCallback(
    async (content: string, files?: File[]) => {
      if (loading) return

      // Optimistically add the user message
      const userMessage: Message = {
        id: generateMessageId(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])
      setLoading(true)
      setAgentStatus(null)

      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
        let uploadedFiles: ServerFile[] = []

        // Convert files to base64 format if provided
        if (files && files.length > 0) {
          uploadedFiles = await Promise.all(
            files.map(async (file) => {
              const content = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader()
                reader.onload = () => {
                  const result = reader.result as string
                  // Remove the data URL prefix (e.g., "data:text/plain;base64,")
                  const base64Content = result.split(',')[1] || result
                  resolve(base64Content)
                }
                reader.onerror = reject
                reader.readAsDataURL(file)
              })

              return {
                name: file.name,
                content: content,
                type: file.type.includes('pdf') ? 'pdf' : 
                       file.type.includes('word') || file.name.endsWith('.docx') ? 'docx' :
                       file.type.includes('text') || file.name.endsWith('.txt') ? 'txt' :
                       file.name.endsWith('.md') ? 'md' : 'other'
              }
            })
          )

          // Immediately reflect uploaded files in the FileTree (left panel)
          if (options?.onFilesCreated && uploadedFiles.length > 0) {
            const initialEntries = uploadedFiles.map((f) => ({
              name: f.name,
              content: f.content,
              type: 'other' as const,
              // hint for grouping in FileTree
              folder: 'uploads' as const
            }))
            // pass folder info by loosening type here; downstream code accepts it
            ;(options.onFilesCreated as any)(initialEntries)
          }
        }

        // Send chat message (SSE stream)
        const response = await fetch(`${apiBaseUrl}/api/v1/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: currentSessionId.current,
            message: content,
            uploaded_files: uploadedFiles,
          }),
        })

        if (response.ok && response.body) {
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''

          try {
            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })

              let newlineIndex = buffer.indexOf('\n')
              while (newlineIndex >= 0) {
                const rawLine = buffer.slice(0, newlineIndex)
                buffer = buffer.slice(newlineIndex + 1)
                newlineIndex = buffer.indexOf('\n')

                const line = rawLine.trimEnd()
                if (!line.startsWith('data: ')) continue

                const jsonPayload = line.slice(6).trim()
                if (!jsonPayload) continue

                let parsed: SSEEvent | null = null
                try {
                  parsed = JSON.parse(jsonPayload) as SSEEvent
                } catch (parseError) {
                  // eslint-disable-next-line no-console
                  console.error('Error parsing SSE data:', parseError, jsonPayload)
                  continue
                }

                switch (parsed.type) {
                  case 'session': {
                    if (!currentSessionId.current && parsed.session_id) {
                      currentSessionId.current = parsed.session_id
                      if (options?.onSessionReady) {
                        options.onSessionReady(parsed.session_id)
                      }
                    }
                    break
                  }

                  case 'agent_status': {
                    console.log('Received agent_status:', parsed)  // 新增调试信息
                    setAgentStatus({ agent: parsed.agent, action: parsed.action })
                    break
                  }

                  case 'file_update': {
                    const created = ensureServerFiles(parsed.files_created)

                    // Update current content for known files
                    const finalProposal = created.find((f) => f.name === '投标文件.md')
                    if (finalProposal) setCurrentContent(finalProposal.content)

                    if (options?.onFilesCreated) {
                      const formatted = makeCreatedFiles(created)
                      // eslint-disable-next-line no-console
                      console.log(
                        'File update during streaming:',
                        formatted.map((f) => f.name)
                      )
                      options.onFilesCreated(formatted)
                    }
                    break
                  }

                  case 'message': {
                    // Ensure session id captured
                    if (!currentSessionId.current && parsed.session_id) {
                      currentSessionId.current = parsed.session_id
                      if (options?.onSessionReady) {
                        options.onSessionReady(parsed.session_id)
                      }
                    }

                    const created = ensureServerFiles(parsed.files_created)
                    const formatted = makeCreatedFiles(created)

                    // Prepare assistant message
                    const assistantMessage: Message = {
                      id: generateMessageId(),
                      role: 'assistant',
                      content: parsed.message,
                      metadata: {
                        ...(parsed.metadata ?? {}),
                        ...(formatted.length > 0 ? { new_files: formatted } : {}),
                      },
                      timestamp: new Date().toISOString(),
                    }
                    setMessages((prev) => [...prev, assistantMessage])

                    // Keep current content in sync if specific files were created
                    const finalProposalMsg = created.find((f) => f.name === '投标文件.md')
                    if (finalProposalMsg) setCurrentContent(finalProposalMsg.content)

                    if (formatted.length > 0 && options?.onFilesCreated) {
                      // eslint-disable-next-line no-console
                      console.log(
                        'Notifying about new files:',
                        formatted.map((f) => f.name)
                      )
                      options.onFilesCreated(formatted)
                    }
                    break
                  }

                  case 'error': {
                    throw new Error(parsed.message)
                  }

                  case 'done': {
                    setAgentStatus(null)
                    if (currentSessionId.current) {
                      await loadConversationHistory(currentSessionId.current)
                    }
                    // Notify parent component to refresh session files
                    if (options?.onSessionUpdate) {
                      options.onSessionUpdate()
                    }
                    break
                  }
                }
              }
            }
          } finally {
            reader.releaseLock()
          }
        } else {
          throw new Error('Failed to send message')
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Chat error:', error)

        const errorMessage: Message = {
          id: generateMessageId(),
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setLoading(false)
        setAgentStatus(null)
      }
    },
    [loading, loadConversationHistory]
  )

  const optimizeText = useCallback(
    async (selectedText: string, context: string, instruction: string) => {
      if (loading) return
      setLoading(true)

      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
        const response = await fetch(`${apiBaseUrl}/api/v1/chat/optimize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: currentSessionId.current,
            message: instruction,
            selected_text: selectedText,
            surrounding_context: context,
          }),
        })

        if (!response.ok) throw new Error('Failed to optimize text')

        const data = await response.json()

        const optimizationMessage: Message = {
          id: generateMessageId(),
          role: 'assistant',
          content: String(data?.message ?? ''),
          metadata: (data?.metadata ?? {}) as Record<string, unknown>,
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, optimizationMessage])

        if (data?.metadata?.optimized_content) {
          setCurrentContent(String(data.metadata.optimized_content))
        }
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Optimization error:', error)

        const errorMessage: Message = {
          id: generateMessageId(),
          role: 'assistant',
          content: 'Sorry, I encountered an error optimizing the text. Please try again.',
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setLoading(false)
      }
    },
    [loading]
  )

  return {
    messages,
    sendMessage,
    optimizeText,
    loading,
    currentContent,
    setCurrentContent,
    sessionId: currentSessionId.current,
    agentStatus,
  }
}
