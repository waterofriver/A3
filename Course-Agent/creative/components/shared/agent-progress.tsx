"use client"

import { Activity, CheckCircle2, LoaderCircle, TriangleAlert } from "lucide-react"
import { useEffect } from "react"

import { announceDemoMode } from "@/lib/runtime/demo-mode"

type AgentProgressProps = {
  progress: number
  currentAgent?: string
  status: "idle" | "running" | "succeeded" | "failed"
  demoMode?: boolean
}

const statusLabel = {
  idle: "等待对话",
  running: "正在生成",
  succeeded: "本轮完成",
  failed: "执行失败",
}

export function AgentProgress({
  progress,
  currentAgent,
  status,
  demoMode,
}: AgentProgressProps) {
  useEffect(() => {
    if (demoMode) announceDemoMode()
  }, [demoMode])

  const normalizedProgress = Math.max(0, Math.min(100, progress))
  const StatusIcon =
    status === "succeeded"
      ? CheckCircle2
      : status === "failed"
        ? TriangleAlert
        : status === "running"
          ? LoaderCircle
          : Activity

  return (
    <section className="h-[92px] rounded-lg border bg-white px-5 py-4" aria-label="Agent 进度">
      <div className="flex items-center justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[#edf3ff] text-[#2457d6]">
            <StatusIcon
              aria-hidden="true"
              className={status === "running" ? "h-4 w-4 animate-spin" : "h-4 w-4"}
            />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-[#27344a]">
              {currentAgent ?? "画像抽取Agent"}
            </p>
            <p className="mt-0.5 text-xs text-[#7a8799]">{statusLabel[status]}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {demoMode ? (
            <span className="rounded-md bg-[#fff3d9] px-2 py-1 text-[11px] font-semibold text-[#8a5b05]">
              演示模式
            </span>
          ) : null}
          <span className="w-10 text-right text-sm font-semibold tabular-nums text-[#2457d6]">
            {normalizedProgress}%
          </span>
        </div>
      </div>
      <div
        aria-label="生成进度"
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={normalizedProgress}
        className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#e8edf5]"
        role="progressbar"
      >
        <div
          className="h-full rounded-full bg-[#2457d6] transition-[width] duration-300"
          style={{ width: `${normalizedProgress}%` }}
        />
      </div>
    </section>
  )
}
