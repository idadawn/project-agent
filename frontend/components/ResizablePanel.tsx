'use client'

import { useState, useRef, useEffect } from 'react'

interface ResizablePanelProps {
  children: React.ReactNode
  direction: 'horizontal' | 'vertical'
  initialSize?: number
  minSize?: number
  maxSize?: number
  className?: string
  onResize?: (size: number) => void
  position?: 'left' | 'right' | 'top' | 'bottom' // 新增位置属性
  collapsible?: boolean // 新增：是否可折叠
  collapsed?: boolean // 新增：是否已折叠
  onToggleCollapse?: () => void // 新增：折叠切换回调
  title?: string // 新增：面板标题
}

export function ResizablePanel({ 
  children, 
  direction, 
  initialSize = 300, 
  minSize = 200, 
  maxSize = 800, 
  className = '',
  onResize,
  position = 'left', // 默认为左侧面板
  collapsible = false,
  collapsed = false,
  onToggleCollapse,
  title
}: ResizablePanelProps) {
  const [size, setSize] = useState(initialSize)
  const [isResizing, setIsResizing] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const startMousePos = useRef<number>(0)
  const startSize = useRef<number>(0)

  // 折叠状态下的尺寸
  const collapsedSize = 40 // 折叠后的尺寸
  const currentSize = collapsed ? collapsedSize : size

  const startResizing = (e: React.MouseEvent) => {
    if (collapsed) return // 折叠状态下不允许拖拽
    
    e.preventDefault()
    e.stopPropagation()
    setIsResizing(true)
    
    // 记录初始位置和尺寸
    startMousePos.current = direction === 'horizontal' ? e.clientX : e.clientY
    startSize.current = size
    
    // 添加全局事件监听
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', stopResizing)
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return

    e.preventDefault()
    e.stopPropagation()
    
    const currentMousePos = direction === 'horizontal' ? e.clientX : e.clientY
    let delta = currentMousePos - startMousePos.current
    
    // 根据位置调整方向
    if (position === 'right' || position === 'bottom') {
      delta = -delta
    }
    
    const newSize = startSize.current + delta
    const clampedSize = Math.max(minSize, Math.min(maxSize, newSize))
    
    setSize(clampedSize)
    onResize?.(clampedSize)
  }

  const stopResizing = () => {
    if (!isResizing) return
    
    setIsResizing(false)
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', stopResizing)
    
    // 恢复全局样式
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  useEffect(() => {
    // 清理函数确保事件监听器被正确移除
    const cleanup = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', stopResizing)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    
    return cleanup
  }, [])

  const style = direction === 'horizontal' 
    ? { width: `${currentSize}px`, minWidth: collapsed ? `${collapsedSize}px` : `${minSize}px`, maxWidth: `${maxSize}px` }
    : { height: `${currentSize}px`, minHeight: collapsed ? `${collapsedSize}px` : `${minSize}px`, maxHeight: `${maxSize}px` }

  // 折叠切换函数
  const handleToggleCollapse = () => {
    onToggleCollapse?.()
  }

  return (
    <div 
      ref={panelRef}
      className={`relative ${className} ${isResizing ? 'resizing' : ''} transition-all duration-300`}
      style={style}
    >
      {/* 折叠按钮 */}
      {collapsible && (
        <div 
          className={`absolute z-20 transition-all duration-200 ${
            direction === 'horizontal'
              ? (position === 'left' 
                  ? 'top-4 right-2' 
                  : 'top-4 left-2'
                )
              : (position === 'top'
                  ? 'bottom-2 right-4'
                  : 'top-2 right-4'
                )
          }`}
        >
          <button
            onClick={handleToggleCollapse}
            className="p-1.5 bg-background border border-border rounded hover:bg-muted transition-colors shadow-sm"
            title={collapsed ? `展开${title || '面板'}` : `折叠${title || '面板'}`}
          >
            {direction === 'horizontal' ? (
              position === 'left' ? (
                collapsed ? (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                )
              ) : (
                collapsed ? (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )
              )
            ) : (
              position === 'top' ? (
                collapsed ? (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                )
              ) : (
                collapsed ? (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )
              )
            )}
          </button>
        </div>
      )}
      
      {/* 面板内容 */}
      <div className={`h-full ${collapsed ? 'overflow-hidden' : ''}`}>
        {children}
      </div>
      
      {/* 拖拽手柄 - 只在非折叠状态下显示 */}
      {!collapsed && (
        <div
          data-resize-handle
          className={`absolute transition-all duration-200 z-10 group select-none ${direction === 'horizontal' ? 'cursor-col-resize' : 'cursor-row-resize'} ${
            direction === 'horizontal' 
              ? (position === 'left' 
                  ? 'right-0 top-0 bottom-0 w-2 -mr-1 hover:w-3' 
                  : 'left-0 top-0 bottom-0 w-2 -ml-1 hover:w-3'
                )
              : (position === 'top'
                  ? 'bottom-0 left-0 right-0 h-2 -mb-1 hover:h-3'
                  : 'top-0 left-0 right-0 h-2 -mt-1 hover:h-3'
                )
          }`}
          onMouseDown={startResizing}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
        >
          {/* 拖拽手柄背景 */}
          <div 
            className={`w-full h-full transition-all duration-200 rounded-sm pointer-events-none ${
              isHovering || isResizing 
                ? 'bg-blue-500/70 shadow-md' 
                : 'bg-transparent group-hover:bg-border/40'
            }`}
          />
          
          {/* 拖拽指示器 */}
          <div 
            className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 ${
              isHovering || isResizing ? 'opacity-100 scale-110' : 'opacity-0 group-hover:opacity-70 scale-100'
            }`}
          >
            {direction === 'horizontal' ? (
              <div className="flex flex-col gap-0.5">
                <div className="w-0.5 h-2 bg-white rounded-full shadow-sm"></div>
                <div className="w-0.5 h-2 bg-white rounded-full shadow-sm"></div>
                <div className="w-0.5 h-2 bg-white rounded-full shadow-sm"></div>
              </div>
            ) : (
              <div className="flex gap-0.5">
                <div className="h-0.5 w-2 bg-white rounded-full shadow-sm"></div>
                <div className="h-0.5 w-2 bg-white rounded-full shadow-sm"></div>
                <div className="h-0.5 w-2 bg-white rounded-full shadow-sm"></div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}