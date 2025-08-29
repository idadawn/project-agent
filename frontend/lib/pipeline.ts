import type { AgentEvent } from "@/hooks/usePipelineEvents"

export const PIPELINE_ORDER = [
  "document_parsing",
  "parsing_completed",
  "bid_build_ready",
  "research",
  "drafting",
  "review",
  "final",
  "bid_build_completed",
] as const

export type StageKey = typeof PIPELINE_ORDER[number]

export function groupByStage(events: AgentEvent[]) {
  const stageMap = new Map<string, { agents: Map<string, AgentEvent[]>; status: "pending" | "running" | "succeeded" | "failed" }>()
  for (const s of PIPELINE_ORDER) {
    stageMap.set(s, { agents: new Map(), status: "pending" })
  }
  for (const ev of events) {
    const s = ev.stage || "general_coordination"
    if (!stageMap.has(s)) stageMap.set(s, { agents: new Map(), status: "pending" })
    const bucket = stageMap.get(s)!
    const agentKey = ev.agent || "unknown"
    if (!bucket.agents.has(agentKey)) bucket.agents.set(agentKey, [])
    bucket.agents.get(agentKey)!.push(ev)
    if (ev.status === "failed") bucket.status = "failed"
    else if (["running", "processing"].includes(ev.status || "")) bucket.status = bucket.status === "pending" ? "running" : bucket.status
    else if (ev.status === "succeeded" && bucket.status === "pending") bucket.status = "succeeded"
  }
  return stageMap
}


