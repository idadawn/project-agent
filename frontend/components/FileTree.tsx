'use client'

import { useState } from 'react'
import { File, Folder, FileText, Upload, Database, BookOpen, ChevronDown, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileItem {
  name: string
  content: string
  type: 'upload' | 'wiki' | 'proposal' | 'other' | 'plan'
  folder?: 'uploads' | 'wiki' | 'root'
}

interface FileTreeProps {
  files: FileItem[]
  selectedFile: string | null
  onFileSelect: (filename: string) => void
  loading?: boolean
}

export function FileTree({ files, selectedFile, onFileSelect, loading }: FileTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(['uploads', 'parsed'])
  )
  
  // 调试信息
  console.log('FileTree received files:', files.map(f => ({ name: f.name, type: f.type, folder: f.folder })))

  const toggleFolder = (folder: string) => {
    const newExpanded = new Set(expandedFolders)
    if (newExpanded.has(folder)) {
      newExpanded.delete(folder)
    } else {
      newExpanded.add(folder)
    }
    setExpandedFolders(newExpanded)
  }

  const getFileExtensionIcon = (filename: string, type?: string) => {
    if (type === 'proposal' || filename === '投标文件.md') {
      return <BookOpen className="h-4 w-4 text-green-600" />
    }
    
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'md':
        return <FileText className="h-4 w-4 text-blue-500" />
      case 'txt':
        return <FileText className="h-4 w-4 text-gray-500" />
      case 'json':
        return <Database className="h-4 w-4 text-yellow-600" />
      case 'pdf':
        return <File className="h-4 w-4 text-red-500" />
      case 'docx':
      case 'doc':
        return <File className="h-4 w-4 text-blue-600" />
      default:
        return <File className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getFolderIcon = (folder: string) => {
    switch (folder) {
      case 'uploads':
        return <Upload className="h-4 w-4 text-blue-500" />
      case 'wiki':
        return <Database className="h-4 w-4 text-green-500" />
      case 'parsed':
        return <BookOpen className="h-4 w-4 text-purple-500" />
      default:
        return <Folder className="h-4 w-4 text-amber-500" />
    }
  }

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={`skeleton-${i}`} className="h-8 bg-muted rounded" />
          ))}
        </div>
      </div>
    )
  }

  // 按文件来源拆分：上传文件 vs 解析/生成文件
  const uploadFiles = files.filter(f => f.folder === 'uploads' || f.type === 'upload')
  const parsedFiles = files.filter(f => !(f.folder === 'uploads' || f.type === 'upload'))

  if (files.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <Folder className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">暂无文件</p>
        <p className="text-xs">上传招标文件开始处理</p>
      </div>
    )
  }

  const renderFolder = (folderName: string, folderFiles: FileItem[], displayName: string) => {
    const isExpanded = expandedFolders.has(folderName)
    
    return (
      <div key={folderName} className="mb-2">
        <button
          onClick={() => toggleFolder(folderName)}
          className="w-full flex items-center gap-2 px-2 py-1 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          {getFolderIcon(folderName)}
          <span>{displayName}</span>
          {folderFiles.length > 0 && (
            <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
              {folderFiles.length}
            </span>
          )}
        </button>
        
        {isExpanded && folderFiles.length > 0 && (
          <div className="ml-6 space-y-1 mt-1">
            {folderFiles.map((file) => (
              <button
                key={`file-${file.name}-${file.type}`}
                onClick={() => onFileSelect(file.name)}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-colors text-left hover:bg-muted/50",
                  selectedFile === file.name
                    ? "bg-accent text-accent-foreground"
                    : "text-foreground"
                )}
              >
                {getFileExtensionIcon(file.name, file.type)}
                <span className="flex-1 truncate">{file.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="p-2">
      <div className="space-y-1">
        {/* 上传文件夹 */}
        {renderFolder('uploads', uploadFiles, '📁 上传文件')}
        {/* 解析文件夹 */}
        {renderFolder('parsed', parsedFiles, '📚 方案文件')}
      </div>
      
      {/* 文件夹说明 */}
      {files.length > 0 && (
        <div className="mt-4 p-3 bg-muted/30 rounded-lg text-xs text-muted-foreground">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <Upload className="h-3 w-3" />
              <span>上传文件: 所有文件显示在此处</span>
            </div>
            <div className="flex items-center gap-1.5">
              <BookOpen className="h-3 w-3" />
              <span>解析文件: 系统生成与解析的文件显示在此处</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}