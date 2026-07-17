"use client"

import {
  CheckCircle2,
  ChevronDown,
  Circle,
  LoaderCircle,
  Pin,
  PinOff,
  RotateCcw,
  TriangleAlert,
} from "lucide-react"
import { useEffect, useState } from "react"

import { Progress } from "@/components/ui/progress"
import type { ResourceConnectionState } from "@/lib/sse/resource-event-source"
import type { ResourceType } from "@/lib/api/resource-types"
import type { ResourceTaskState } from "@/lib/query/resource-cache"

const labels: Record<ResourceType, string> = {
  handout: "讲义文档",
  mindmap: "思维导图",
  quiz: "习题题库",
  code: "拓展阅读",
  video: "教学图文视频",
}

const statusLabels = {
  idle: "等待中",
  running: "生成中",
  succeeded: "已完成",
  failed: "生成失败",
}

type TaskRailProps = {
  task: ResourceTaskState
  selectedTypes: ResourceType[]
  connectionState: ResourceConnectionState
  onRetry?: () => void
}

export function TaskRail({
  task,
  selectedTypes,
  connectionState,
  onRetry,
}: TaskRailProps) {
  const [pinned, setPinned] = useState(false)
  const [expanded, setExpanded] = useState(true)
  const autoCollapse = task.status === "succeeded"

  useEffect(() => {
    if (autoCollapse && !pinned) setExpanded(false)
  }, [autoCollapse, pinned])

  if (!expanded) {
    return (
      <aside className="self-start border-l border-slate-200 pl-5" aria-label="资源任务进度">
        <button
          className="flex h-11 w-full items-center justify-between text-sm font-semibold text-slate-700 hover:text-primary transition-colors"
          onClick={() => setExpanded(true)}
          type="button"
        >
          任务已完成
          <ChevronDown aria-hidden="true" className="h-4 w-4" />
        </button>
      </aside>
    )
  }

  return (
    <aside className="self-start border-l border-slate-200 pl-5" aria-label="资源任务进度">
      <header className="flex h-11 items-center justify-between border-b border-slate-200">
        <div>
          <p className="text-sm font-semibold text-slate-700">任务轨道</p>
          <p className="mt-0.5 text-[10px] font-medium text-slate-400 uppercase tracking-wider">
            {connectionState === "open" ? "实时连接" : connectionState === "error" ? "正在恢复连接" : "连接中"}
          </p>
        </div>
        <button
          aria-label={pinned ? "取消固定任务栏" : "固定任务栏"}
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-400 transition hover:bg-slate-50 hover:text-primary active:scale-95"
          onClick={() => setPinned((current) => !current)}
          title={pinned ? "取消固定任务栏" : "固定任务栏"}
          type="button"
        >
          {pinned ? <PinOff aria-hidden="true" className="h-3.5 w-3.5" /> : <Pin aria-hidden="true" className="h-3.5 w-3.5" />}
        </button>
      </header>

      <div className="py-5">
        <div className="flex items-baseline justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase">全局进度</span>
          <span className="text-lg font-bold tabular-nums text-primary">
            {task.globalProgress}%
          </span>
        </div>
        <Progress className="mt-2 h-1.5 rounded-full overflow-hidden" value={task.globalProgress} />
        <div className="mt-4 border-y border-slate-100 py-3 bg-slate-50/30 rounded-xl px-3 border-dashed">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">当前 Agent</p>
          <p className="mt-1 truncate text-xs font-bold text-slate-700">
            {task.currentAgent ?? "主管Agent"}
          </p>
        </div>

        <ol className="mt-3 divide-y divide-slate-100">
          {selectedTypes.map((resourceType) => {
            const item = task.byType[resourceType]
            const StatusIcon =
              item.status === "succeeded"
                ? CheckCircle2
                : item.status === "failed"
                  ? TriangleAlert
                  : item.status === "running"
                    ? LoaderCircle
                    : Circle
            return (
              <li className="flex min-h-[68px] items-center gap-3 py-3" key={resourceType}>
                <StatusIcon
                  aria-hidden="true"
                  className={`h-4.5 w-4.5 shrink-0 ${
                    item.status === "succeeded"
                      ? "text-emerald-500"
                      : item.status === "failed"
                        ? "text-rose-500"
                        : item.status === "running"
                          ? "animate-spin text-primary"
                          : "text-slate-300"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-bold text-slate-600">
                      {labels[resourceType]}
                    </span>
                    <span className="shrink-0 text-[10px] font-semibold text-slate-400">
                      {statusLabels[item.status]}
                    </span>
                  </div>
                  <Progress className="mt-2 h-1 rounded-full overflow-hidden" value={item.progress} />
                  {item.error ? (
                    <div className="mt-2 flex items-start justify-between gap-2">
                      <p className="min-w-0 text-[10px] font-medium leading-relaxed text-rose-600">
                        {item.error.message}
                      </p>
                      {item.error.retryable ? (
                        <span className="shrink-0 rounded-lg bg-rose-50 border border-rose-100 px-1.5 py-0.5 text-[9px] font-bold text-rose-600">
                          可重试
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </li>
            )
          })}
        </ol>

        {onRetry && (task.status === "failed" || task.status === "partial_success") ? (
          <button
            className="mt-4 flex h-9 w-full items-center justify-center gap-2 rounded-xl border border-slate-200 text-xs font-bold text-primary hover:bg-slate-50 transition-all duration-150 active:scale-95 shadow-sm"
            onClick={onRetry}
            type="button"
          >
            <RotateCcw aria-hidden="true" className="h-3.5 w-3.5" />
            重试任务
          </button>
        ) : null}
      </div>
    </aside>
  )
}
