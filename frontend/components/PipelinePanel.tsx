"use client"

import React from "react"
import type { AgentEvent } from "@/hooks/usePipelineEvents"
import { groupByStage, PIPELINE_ORDER } from "@/lib/pipeline"

export default function PipelinePanel({ events }: { events: AgentEvent[] }) {
  const stageMap = groupByStage(events)

  return (
    <div className="space-y-4">
      {/* 顶部：阶段进度条 */}
      <ol className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {PIPELINE_ORDER.map((s, i) => {
          const bucket = stageMap.get(s)
          const status = bucket?.status ?? "pending"
          const badge =
            status === "failed"
              ? "bg-red-100 text-red-700"
              : status === "running"
              ? "bg-blue-100 text-blue-700"
              : status === "succeeded"
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-600"
          return (
            <li key={s} className={`rounded-xl px-3 py-2 flex items-center justify-between shadow-sm ${badge}`}>
              <span className="truncate">{i + 1}. {labelOfStage(s)}</span>
              <span className="text-xs uppercase">{status}</span>
            </li>
          )
        })}
      </ol>

      {/* 下方：每个阶段的智能体执行 */}
      <div className="space-y-3">
        {PIPELINE_ORDER.map((s) => {
          const bucket = stageMap.get(s)
          if (!bucket) return null
          const agents = [...bucket.agents.entries()]
          return (
            <div key={s} className="rounded-2xl border p-3">
              <div className="mb-2 font-medium">{labelOfStage(s)}</div>
              {agents.length === 0 ? (
                <div className="text-sm text-gray-500">暂无执行记录</div>
              ) : (
                <ul className="space-y-1">
                  {agents.map(([agent, list]) => {
                    const last = list[list.length - 1]
                    const color =
                      last?.status === "failed"
                        ? "text-red-600"
                        : ["running", "processing"].includes(last?.status || "")
                        ? "text-blue-600"
                        : last?.status === "succeeded"
                        ? "text-green-600"
                        : "text-gray-600"
                    return (
                      <li key={agent} className="flex items-center justify-between">
                        <span className="truncate">{agent}</span>
                        <span className={`text-xs ${color}`}>{last?.status ?? "pending"}</span>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function labelOfStage(key: string) {
  switch (key) {
    case "document_parsing":
      return "文档解析"
    case "parsing_completed":
      return "解析完成"
    case "bid_build_ready":
      return "方案构建"
    case "research":
      return "资料收集"
    case "drafting":
      return "方案起草"
    case "review":
      return "质量校验"
    case "bid_build_completed":
      return "方案完成"
    case "final":
      return "完成"
    default:
      return key
  }
}


