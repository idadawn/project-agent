"use client"

import { useEffect, useState } from "react"

export type AgentEvent = {
  ts: number
  sessionId: string
  stage?: string
  agent?: string
  action?: string
  status?: "queued" | "running" | "succeeded" | "failed" | "processing"
  meta?: Record<string, any>
}

export function usePipelineEvents(sessionId: string) {
  const [events, setEvents] = useState<AgentEvent[]>([])

  useEffect(() => {
    if (!sessionId) return
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
    const es = new EventSource(`${apiBaseUrl}/api/v1/sse?session_id=${encodeURIComponent(sessionId)}`)
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data?.type === "agent_status") {
          setEvents((prev) =>
            prev.concat([
              {
                ts: Date.now(),
                sessionId,
                stage: data.stage || data.metadata?.stage,
                agent: data.agent,
                action: data.action,
                status: data.status,
                meta: data,
              },
            ])
          )
        }
      } catch {}
    }
    return () => es.close()
  }, [sessionId])

  return events
}


