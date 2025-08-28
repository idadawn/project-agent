'use client'

import { useState } from 'react'
import { Wand2, X, RefreshCw, Languages, Edit3, Minimize2, Maximize2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface OptimizationPanelProps {
  selectedText: string
  onOptimize: (instruction: string) => void
  onClose: () => void
}

const optimizationPresets = [
  { id: 'rewrite', label: '重写', icon: Edit3, description: '提高清晰度和流畅性' },
  { id: 'expand', label: '扩展', icon: Maximize2, description: '添加更多细节' },
  { id: 'condense', label: '精简', icon: Minimize2, description: '更加简洁' },
  { id: 'formal', label: '正式化', icon: RefreshCw, description: '专业语调' },
  { id: 'translate', label: '翻译', icon: Languages, description: '翻译成中文' },
]

export function OptimizationPanel({ selectedText, onOptimize, onClose }: OptimizationPanelProps) {
  const [customInstruction, setCustomInstruction] = useState('')
  const [isCustomMode, setIsCustomMode] = useState(false)

  const handlePresetOptimize = (presetId: string) => {
    const preset = optimizationPresets.find(p => p.id === presetId)
    if (preset) {
      let instruction = ''
      switch (presetId) {
        case 'rewrite':
          instruction = '重写这段文本，使其更清晰流畅'
          break
        case 'expand':
          instruction = '扩展这段文本，添加更多细节和深度'
          break
        case 'condense':
          instruction = '简化这段文本，保留核心要点'
          break
        case 'formal':
          instruction = '将这段文本改写成更正式的语调'
          break
        case 'translate':
          instruction = '将这段文本翻译成中文'
          break
        default:
          instruction = `优化这段文本: ${preset.label}`
      }
      onOptimize(instruction)
    }
  }

  const handleCustomOptimize = () => {
    if (customInstruction.trim()) {
      onOptimize(customInstruction.trim())
      setCustomInstruction('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleCustomOptimize()
    }
  }

  return (
    <div className="border-t border-border bg-blue-50/50 p-4">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <Wand2 className="h-4 w-4 text-blue-600" />
          <h3 className="font-medium text-sm text-blue-900">文本优化</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-blue-100 rounded transition-colors"
        >
          <X className="h-4 w-4 text-blue-600" />
        </button>
      </div>
      
      <div className="mb-4">
        <div className="text-xs text-blue-700 bg-blue-100 p-3 rounded max-h-20 overflow-auto">
          "{selectedText.length > 100 ? selectedText.substring(0, 100) + '...' : selectedText}"
        </div>
      </div>

      {!isCustomMode ? (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-3">
            {optimizationPresets.map((preset) => {
              const Icon = preset.icon
              return (
                <button
                  key={preset.id}
                  onClick={() => handlePresetOptimize(preset.id)}
                  className="flex items-center gap-3 p-3 text-xs bg-white hover:bg-blue-50 border border-blue-200 rounded-lg transition-colors text-left"
                >
                  <Icon className="h-4 w-4 text-blue-600" />
                  <div>
                    <div className="font-medium text-blue-900">{preset.label}</div>
                    <div className="text-blue-600 text-xs">{preset.description}</div>
                  </div>
                </button>
              )
            })}
          </div>
          
          <button
            onClick={() => setIsCustomMode(true)}
            className="w-full p-3 text-sm bg-white hover:bg-blue-50 border border-blue-200 rounded-lg transition-colors text-blue-700"
          >
            自定义指令...
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex gap-3">
            <input
              type="text"
              value={customInstruction}
              onChange={(e) => setCustomInstruction(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入自定义优化指令..."
              className="flex-1 px-4 py-3 text-sm bg-white border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleCustomOptimize}
              disabled={!customInstruction.trim()}
              className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Wand2 className="h-4 w-4" />
            </button>
          </div>
          
          <button
            onClick={() => setIsCustomMode(false)}
            className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            ← 返回预设选项
          </button>
        </div>
      )}
    </div>
  )
}