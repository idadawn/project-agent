'use client'

import { useState, useRef, useEffect } from 'react'
import { FileTree } from '@/components/FileTree'
import { MarkdownEditor } from '@/components/MarkdownEditor'
import { ChatPanel } from '@/components/ChatPanel'
import { ResizablePanel } from '@/components/ResizablePanel'
import { useSession } from '@/hooks/useSession'
import { useChat } from '@/hooks/useChat'
import { SessionManager } from '@/components/SessionManager'

export default function Home() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [selectedText, setSelectedText] = useState<string>('')
  const [surroundingContext, setSurroundingContext] = useState<string>('')
  
  const { session, files, loading: sessionLoading, addFiles, reload, loadSessionFiles } = useSession(sessionId)
  const { 
    messages, 
    sendMessage, 
    optimizeText,
    loading: chatLoading,
    currentContent,
    setCurrentContent,
    agentStatus
  } = useChat(sessionId, {
    onFilesCreated: (newFiles) => {
      console.log('Received new files in main component:', newFiles.map(f => f.name))
      addFiles(newFiles)
      
      // 立即刷新文件树
      if (sessionId) {
        console.log('Immediately refreshing file tree after files created')
        setTimeout(() => {
          loadSessionFiles(sessionId)
        }, 200)
      }
      
      // 优先自动选择最终方案文档（proposal 类型或 文件名=投标文件.md）
      const finalProposal = newFiles.find(f => (f.type === 'proposal') || f.name === '投标文件.md')
      if (finalProposal) {
        console.log('Auto-selecting final proposal file:', finalProposal.name)
        setSelectedFile(finalProposal.name)
        return
      }
      // 兼容旧文件名已移除
    },
    onSessionUpdate: () => {
      // Refresh session files when chat completes
      if (sessionId) {
        console.log('Refreshing session files after chat completion')
        // Use the session hook's reload function to refresh files
        setTimeout(() => {
          reload()
        }, 500)
      }
    },
    onSessionReady: (id) => {
      // Sync chat-provided session id back to the page so file loading works
      setSessionId(id)
    }
  })

  const handleTextSelection = (text: string, context: string) => {
    setSelectedText(text)
    setSurroundingContext(context)
  }

  const handleOptimization = async (instruction: string) => {
    if (!selectedText) return
    
    await optimizeText(selectedText, surroundingContext, instruction)
    setSelectedText('')
    setSurroundingContext('')
  }

  const handleFileSelect = (filename: string) => {
    setSelectedFile(filename)
  }

  const getCurrentFileContent = () => {
    if (!selectedFile) return ''
    
    // First try to get from files list (this will have the latest updates from addFiles)
    if (files) {
      const file = files.find(f => f.name === selectedFile)
      if (file) return file.content
    }
    
    // 当选中文件是最终方案文档（proposal 类型约定命名）时，从 currentContent 回退
    if (
      selectedFile === 'PROPOSAL_PLAN.md' ||
      selectedFile === 'FINAL_PROPOSAL.md' ||
      selectedFile.startsWith('PROPOSAL_')
    ) {
      return currentContent || ''
    }
    
    return ''
  }

  const handleContentChange = (content: string) => {
    setCurrentContent(content)
  }

  // Debug effect to monitor content updates
  useEffect(() => {
    if (selectedFile) {
      console.log(`Content update for ${selectedFile}:`, getCurrentFileContent().substring(0, 100))
    }
  }, [selectedFile, files, currentContent])

  const [leftPanelWidth, setLeftPanelWidth] = useState(256)
  const [rightPanelWidth, setRightPanelWidth] = useState(400)

  return (
    <div className="flex h-screen bg-background">
      {/* Left Panel - File Tree */}
      <ResizablePanel 
        direction="horizontal" 
        initialSize={280}
        minSize={200}
        maxSize={500}
        onResize={setLeftPanelWidth}
        className="flex flex-col border-r border-border"
      >
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold text-base">文件</h2>
        </div>
        
        <div className="flex-1 overflow-auto">
          <FileTree
            files={files || []}
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            loading={sessionLoading}
          />
        </div>
        
        <div className="p-4 border-t border-border">
          <SessionManager
            currentSessionId={sessionId}
            onSessionChange={setSessionId}
          />
        </div>
      </ResizablePanel>

      {/* Center Panel - Markdown Editor */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold text-base">
            {selectedFile || '编辑器'}
          </h2>
        </div>
        
        <div className="flex-1 overflow-hidden min-h-0">
          <MarkdownEditor
            content={getCurrentFileContent()}
            onChange={handleContentChange}
            onTextSelection={handleTextSelection}
            selectedText={selectedText}
            loading={sessionLoading}
          />
        </div>
      </div>

      {/* Right Panel - Chat */}
      <ResizablePanel 
        direction="horizontal" 
        initialSize={500}
        minSize={400}
        maxSize={800}
        onResize={setRightPanelWidth}
        className="flex flex-col border-l border-border"
      >
        <div className="p-4 border-b border-border">
          <h2 className="font-semibold text-base">聊天</h2>
        </div>
        
        <div className="flex-1 overflow-hidden">
          <ChatPanel
            messages={messages}
            onSendMessage={sendMessage}
            onOptimizeText={handleOptimization}
            selectedText={selectedText}
            loading={chatLoading}
            sessionId={sessionId}
            agentStatus={agentStatus}
          />
        </div>
      </ResizablePanel>
    </div>
  )
}