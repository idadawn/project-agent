'use client'

import { useState, useEffect } from 'react'
import { Plus, History, Trash2, Download, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Session {
  session_id: string
  created_at: string
  last_activity: string
  message_count: number
  has_proposal: boolean
  proposal_title?: string
}

interface SessionManagerProps {
  currentSessionId: string | null
  onSessionChange: (sessionId: string | null) => void
}

export function SessionManager({ currentSessionId, onSessionChange }: SessionManagerProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (showHistory) {
      loadSessions()
    }
  }, [showHistory])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/list`)
      if (response.ok) {
        const data = await response.json()
        setSessions(data)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    } finally {
      setLoading(false)
    }
  }

  const createNewSession = () => {
    onSessionChange(null)
    setShowHistory(false)
  }

  const selectSession = (sessionId: string) => {
    onSessionChange(sessionId)
    setShowHistory(false)
  }

  const deleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this session?')) return

    try {
      const response = await fetch(`/api/v1/sessions/${sessionId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setSessions(sessions => sessions.filter(s => s.session_id !== sessionId))
        if (currentSessionId === sessionId) {
          onSessionChange(null)
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  const exportSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    try {
      const response = await fetch(`/api/v1/proposals/${sessionId}/export/md`)
      if (response.ok) {
        const data = await response.json()
        
        // Download the file
        const blob = new Blob([data.content], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Failed to export session:', error)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (!showHistory) {
    return (
      <div className="space-y-3">
        <button
          onClick={createNewSession}
          className="w-full flex items-center gap-3 px-4 py-3 text-sm bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg transition-colors"
        >
          <Plus className="h-4 w-4" />
          新建会话
        </button>
        
        <button
          onClick={() => setShowHistory(true)}
          className="w-full flex items-center gap-3 px-4 py-3 text-sm bg-muted hover:bg-muted/80 rounded-lg transition-colors"
        >
          <History className="h-4 w-4" />
          会话历史
        </button>
        
        {currentSessionId && (
          <div className="text-xs text-muted-foreground px-4 py-3 bg-muted/50 rounded">
            Current: {currentSessionId.slice(0, 8)}...
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-sm">会话管理</h3>
        <button
          onClick={() => setShowHistory(false)}
          className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded hover:bg-muted"
        >
          关闭
        </button>
      </div>
      
      <button
        onClick={createNewSession}
        className="w-full flex items-center gap-3 px-4 py-3 text-sm bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg transition-colors"
      >
        <Plus className="h-4 w-4" />
        新建会话
      </button>
      
      <div className="max-h-64 overflow-auto space-y-2">
        {loading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            正在加载会话...
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            暂无历史会话
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              onClick={() => selectSession(session.session_id)}
              className={cn(
                "p-3 rounded-lg cursor-pointer transition-colors group",
                currentSessionId === session.session_id
                  ? "bg-primary/10 border border-primary/20"
                  : "hover:bg-muted"
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">
                    {session.proposal_title || `Session ${session.session_id.slice(0, 8)}`}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {session.message_count} messages
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {formatDate(session.last_activity)}
                  </div>
                  {session.has_proposal && (
                    <div className="text-xs text-green-600 font-medium mt-1">
                      ✅ Complete
                    </div>
                  )}
                </div>
                
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {session.has_proposal && (
                    <button
                      onClick={(e) => exportSession(session.session_id, e)}
                      className="p-1 hover:bg-background rounded transition-colors"
                      title="Export proposal"
                    >
                      <Download className="h-3 w-3" />
                    </button>
                  )}
                  
                  <button
                    onClick={(e) => deleteSession(session.session_id, e)}
                    className="p-1 hover:bg-background rounded transition-colors text-destructive"
                    title="Delete session"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}