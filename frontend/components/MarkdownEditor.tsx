'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Edit3, Eye, Download, Copy } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MarkdownEditorProps {
  content: string
  onChange: (content: string) => void
  onTextSelection: (selectedText: string, context: string) => void
  selectedText: string
  loading?: boolean
}

export function MarkdownEditor({ 
  content, 
  onChange, 
  onTextSelection, 
  selectedText,
  loading 
}: MarkdownEditorProps) {
  const [mode, setMode] = useState<'edit' | 'preview'>('preview')
  const [localContent, setLocalContent] = useState(content)
  const previewRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setLocalContent(content)
  }, [content])

  const handleTextSelection = useCallback(() => {
    if (mode !== 'preview') return

    const selection = window.getSelection()
    if (!selection || selection.isCollapsed) {
      if (selectedText) {
        onTextSelection('', '')
      }
      return
    }

    const selectedTextContent = selection.toString().trim()
    if (!selectedTextContent) return

    // Get surrounding context
    const range = selection.getRangeAt(0)
    const container = range.commonAncestorContainer
    const textContent = container.textContent || ''
    
    // Find the position of selected text in the container
    const beforeText = textContent.substring(0, textContent.indexOf(selectedTextContent))
    const afterText = textContent.substring(textContent.indexOf(selectedTextContent) + selectedTextContent.length)
    
    // Get context (100 chars before and after)
    const contextBefore = beforeText.slice(-100)
    const contextAfter = afterText.slice(0, 100)
    const context = `${contextBefore}[${selectedTextContent}]${contextAfter}`

    onTextSelection(selectedTextContent, context)
  }, [mode, selectedText, onTextSelection])

  const handleContentChange = (newContent: string) => {
    setLocalContent(newContent)
    onChange(newContent)
  }

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(content)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const downloadMarkdown = () => {
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'proposal.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col min-h-0 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-muted/30 flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMode('preview')}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              mode === 'preview' 
                ? "bg-primary text-primary-foreground" 
                : "bg-transparent hover:bg-muted"
            )}
          >
            <Eye className="h-4 w-4 inline mr-2" />
            预览
          </button>
          <button
            onClick={() => setMode('edit')}
            className={cn(
              "px-4 py-2 rounded-md text-sm font-medium transition-colors",
              mode === 'edit' 
                ? "bg-primary text-primary-foreground" 
                : "bg-transparent hover:bg-muted"
            )}
          >
            <Edit3 className="h-4 w-4 inline mr-2" />
            编辑
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={copyToClipboard}
            className="p-2 hover:bg-muted rounded transition-colors"
            title="复制到剪贴板"
          >
            <Copy className="h-4 w-4" />
          </button>
          <button
            onClick={downloadMarkdown}
            className="p-2 hover:bg-muted rounded transition-colors"
            title="下载Markdown文件"
          >
            <Download className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content Area (inner scrolling only) */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {mode === 'edit' ? (
          <div className="flex-1 min-h-0 overflow-hidden">
            <textarea
              ref={textareaRef}
              value={localContent}
              onChange={(e) => handleContentChange(e.target.value)}
              className="w-full h-full min-h-full p-6 bg-background border-none outline-none resize-none font-mono text-sm overflow-y-auto"
              placeholder="Start writing your proposal..."
            />
          </div>
        ) : (
          <div
            ref={previewRef}
            className="flex-1 min-h-0 overflow-y-auto p-6"
            onMouseUp={handleTextSelection}
            onTouchEnd={handleTextSelection}
          >
            {content ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                className="prose max-w-none"
                components={{
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-foreground">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-foreground">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-foreground">{children}</h3>,
                  p: ({ children }) => <p className="mb-4 leading-relaxed text-foreground">{children}</p>,
                  ul: ({ children }) => <ul className="mb-4 ml-6 list-disc">{children}</ul>,
                  ol: ({ children }) => <ol className="mb-4 ml-6 list-decimal">{children}</ol>,
                  li: ({ children }) => <li className="mb-2">{children}</li>,
                  code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-sm">{children}</code>,
                  pre: ({ children }) => <pre className="bg-muted p-4 rounded-lg overflow-x-auto mb-4">{children}</pre>,
                  blockquote: ({ children }) => <blockquote className="border-l-4 border-border pl-4 italic text-muted-foreground mb-4">{children}</blockquote>,
                  table: ({ children }) => (
                    <div className="overflow-x-auto mb-4">
                      <table className="table-auto min-w-full border-collapse">{children}</table>
                    </div>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <Edit3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>暂无内容</p>
                <p className="text-sm">开始对话以生成方案</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selection Indicator */}
      {selectedText && mode === 'preview' && (
        <div className="p-3 bg-blue-50 border-t border-border flex-shrink-0">
          <p className="text-xs text-blue-700">
            Selected: "{selectedText.substring(0, 50)}{selectedText.length > 50 ? '...' : ''}"
          </p>
        </div>
      )}
    </div>
  )
}