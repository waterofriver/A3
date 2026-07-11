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
  code: "代码实操案例",
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
      <aside className="self-start border-l border-[#d9e1ec] pl-5" aria-label="资源任务进度">
        <button
          className="flex h-11 w-full items-center justify-between text-sm font-semibold text-[#344158]"
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
    <aside className="self-start border-l border-[#d9e1ec] pl-5" aria-label="资源任务进度">
      <header className="flex h-11 items-center justify-between border-b">
        <div>
          <p className="text-sm font-semibold text-[#27344a]">任务轨道</p>
          <p className="mt-0.5 text-[11px] text-[#7a8799]">
            {connectionState === "open" ? "实时连接" : connectionState === "error" ? "正在恢复连接" : "连接中"}
          </p>
        </div>
        <button
          aria-label={pinned ? "取消固定任务栏" : "固定任务栏"}
          className="flex h-8 w-8 items-center justify-center rounded-md text-[#718096] hover:bg-[#f0f4fb] hover:text-[#2457d6]"
          onClick={() => setPinned((current) => !current)}
          title={pinned ? "取消固定任务栏" : "固定任务栏"}
          type="button"
        >
          {pinned ? <PinOff aria-hidden="true" className="h-4 w-4" /> : <Pin aria-hidden="true" className="h-4 w-4" />}
        </button>
      </header>

      <div className="py-5">
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-[#7a8799]">全局进度</span>
          <span className="text-lg font-semibold tabular-nums text-[#2457d6]">
            {task.globalProgress}%
          </span>
        </div>
        <Progress className="mt-2 h-1.5 rounded-none" value={task.globalProgress} />
        <div className="mt-4 border-y py-3">
          <p className="text-[11px] text-[#8a96a8]">当前 Agent</p>
          <p className="mt-1 truncate text-sm font-semibold text-[#344158]">
            {task.currentAgent ?? "主管Agent"}
          </p>
        </div>

        <ol className="mt-3 divide-y">
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
                  className={`h-4 w-4 shrink-0 ${
                    item.status === "succeeded"
                      ? "text-[#648d28]"
                      : item.status === "failed"
                        ? "text-[#c7463c]"
                        : item.status === "running"
                          ? "animate-spin text-[#2457d6]"
                          : "text-[#a2acba]"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-xs font-medium text-[#46556c]">
                      {labels[resourceType]}
                    </span>
                    <span className="shrink-0 text-[11px] text-[#7a8799]">
                      {statusLabels[item.status]}
                    </span>
                  </div>
                  <Progress className="mt-2 h-1 rounded-none" value={item.progress} />
                  {item.error ? (
                    <div className="mt-2 flex items-start justify-between gap-2">
                      <p className="min-w-0 text-[11px] leading-4 text-[#a2463e]">
                        {item.error.message}
                      </p>
                      {item.error.retryable ? (
                        <span className="shrink-0 rounded-sm bg-[#fff0ed] px-1.5 py-0.5 text-[10px] font-semibold text-[#a2463e]">
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
            className="mt-4 flex h-9 w-full items-center justify-center gap-2 rounded-md border border-[#d1dbea] text-xs font-semibold text-[#2457d6] hover:bg-[#f4f7fc]"
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
