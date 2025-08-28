'use client'

import { useState, useEffect } from 'react'

interface FileItem {
  name: string
  content: string
  type: 'upload' | 'wiki' | 'proposal' | 'plan' | 'other'
  folder?: 'uploads' | 'wiki' | 'root'
}

interface SessionData {
  session_id: string
  data: Record<string, any>
  snapshots: any[]
}

export function useSession(sessionId: string | null) {
  const [session, setSession] = useState<SessionData | null>(null)
  const [files, setFiles] = useState<FileItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addFiles = (newFiles: FileItem[]) => {
    console.log('addFiles called with:', newFiles.map(f => f.name))
    setFiles(prevFiles => {
      const updatedFiles = [...prevFiles]
      
      newFiles.forEach(newFile => {
        const existingIndex = updatedFiles.findIndex(f => f.name === newFile.name)
        if (existingIndex >= 0) {
          // Update existing file content
          console.log('Updating existing file:', newFile.name)
          updatedFiles[existingIndex] = newFile
        } else {
          // Add new file
          console.log('Adding new file:', newFile.name)
          updatedFiles.push(newFile)
        }
      })
      
      console.log('Total files after update:', updatedFiles.map(f => f.name))
      return updatedFiles
    })
    
    // 强制刷新文件树显示
    setTimeout(() => {
      if (sessionId) {
        console.log('Forcing file tree refresh after adding files')
        loadSessionFiles(sessionId)
      }
    }, 100)
  }

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId)
      loadSessionFiles(sessionId)
    } else {
      setSession(null)
      setFiles([])
    }
  }, [sessionId])

  const loadSession = async (id: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/${id}`)
      if (response.ok) {
        const data = await response.json()
        setSession(data)
      } else {
        setError('Failed to load session')
      }
    } catch (err) {
      setError('Failed to load session')
      console.error('Session load error:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadSessionFiles = async (id: string) => {
    try {
      console.log('Loading session files for session:', id)
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/${id}/files`)
      if (response.ok) {
        const data = await response.json()
        console.log('Received files from API:', data.files)
        
        const formattedFiles: FileItem[] = data.files.map((file: any) => ({
          name: file.name,
          content: file.content,
          type: file.type,
          folder: file.folder
        }))
        
        console.log('Formatted files:', formattedFiles.map(f => ({ name: f.name, type: f.type, folder: f.folder })))
        // Merge with existing files instead of replacing, to preserve optimistic entries
        setFiles(prev => {
          if (!formattedFiles || formattedFiles.length === 0) {
            return prev
          }
          const byName = new Map<string, FileItem>()
          // keep previous first
          for (const f of prev) byName.set(f.name, f)
          // then overlay server files
          for (const f of formattedFiles) byName.set(f.name, f)
          return Array.from(byName.values())
        })
      } else {
        console.error('Failed to load session files:', response.status, response.statusText)
      }
    } catch (err) {
      console.error('Files load error:', err)
    }
  }

  const createSnapshot = async (description: string) => {
    if (!sessionId) return null
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/${sessionId}/snapshot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description })
      })
      
      if (response.ok) {
        const data = await response.json()
        await loadSession(sessionId) // Reload to get updated snapshots
        return data
      }
    } catch (err) {
      console.error('Snapshot creation error:', err)
    }
    
    return null
  }

  const restoreSnapshot = async (snapshotId: string) => {
    if (!sessionId) return false
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/sessions/${sessionId}/restore/${snapshotId}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        await loadSession(sessionId)
        await loadSessionFiles(sessionId)
        return true
      }
    } catch (err) {
      console.error('Snapshot restore error:', err)
    }
    
    return false
  }

  const updateFileContent = async (filename: string, content: string) => {
    if (!sessionId) return
    
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
      const response = await fetch(`${apiBaseUrl}/api/v1/proposals/${sessionId}/content`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content })
      })
      
      if (response.ok) {
        // Update local files state
        setFiles(prevFiles => 
          prevFiles.map(file => 
            file.name === filename 
              ? { ...file, content }
              : file
          )
        )
      }
    } catch (err) {
      console.error('File update error:', err)
    }
  }

  return {
    session,
    files,
    loading,
    error,
    createSnapshot,
    restoreSnapshot,
    updateFileContent,
    addFiles,
    loadSessionFiles,
    reload: () => {
      if (sessionId) {
        loadSession(sessionId)
        loadSessionFiles(sessionId)
      }
    }
  }
}