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
}

export function ResizablePanel({ 
  children, 
  direction, 
  initialSize = 300, 
  minSize = 200, 
  maxSize = 800, 
  className = '',
  onResize 
}: ResizablePanelProps) {
  const [size, setSize] = useState(initialSize)
  const [isResizing, setIsResizing] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  const startResizing = (e: React.MouseEvent) => {
    e.preventDefault()
    setIsResizing(true)
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', stopResizing)
    document.body.style.cursor = direction === 'horizontal' ? 'col-resize' : 'row-resize'
    document.body.style.userSelect = 'none'
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing) return

    let newSize
    if (direction === 'horizontal') {
      const rect = panelRef.current?.getBoundingClientRect()
      if (rect) {
        newSize = e.clientX - rect.left
      }
    } else {
      const rect = panelRef.current?.getBoundingClientRect()
      if (rect) {
        newSize = e.clientY - rect.top
      }
    }

    if (newSize !== undefined) {
      const clampedSize = Math.max(minSize, Math.min(maxSize, newSize))
      setSize(clampedSize)
      onResize?.(clampedSize)
    }
  }

  const stopResizing = () => {
    setIsResizing(false)
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', stopResizing)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  useEffect(() => {
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', stopResizing)
    }
  }, [])

  const style = direction === 'horizontal' 
    ? { width: `${size}px`, minWidth: `${minSize}px`, maxWidth: `${maxSize}px` }
    : { height: `${size}px`, minHeight: `${minSize}px`, maxHeight: `${maxSize}px` }

  return (
    <div 
      ref={panelRef}
      className={`relative ${className}`}
      style={style}
    >
      {children}
      <div
        className={`absolute top-0 bottom-0 transition-all duration-200 z-10 cursor-col-resize ${
          direction === 'horizontal' 
            ? 'right-0 w-2 -mr-1 hover:w-3' 
            : 'bottom-0 h-2 -mb-1 hover:h-3'
        }`}
        onMouseDown={startResizing}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        {/* 拖拽手柄背景 */}
        <div 
          className={`w-full h-full transition-colors duration-200 ${
            isHovering || isResizing 
              ? 'bg-blue-500/70 shadow-sm' 
              : 'bg-border/30 hover:bg-border/50'
          }`}
        />
        
        {/* 拖拽指示器 */}
        <div 
          className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200 ${
            isHovering || isResizing ? 'opacity-100 scale-110' : 'opacity-60 scale-100'
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
    </div>
  )
}