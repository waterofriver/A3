import { AlertCircle, RotateCcw } from "lucide-react"

import { ApiError } from "@/lib/api/client"

type ErrorNoticeProps = {
  error: ApiError | Error | string
  onRetry?: () => void
}

const errorPresentations: Record<
  string,
  { title: string; guidance: string; retryLabel?: string }
> = {
  VALIDATION_ERROR: {
    title: "参数缺失",
    guidance: "检查输入内容",
  },
  CONTENT_BLOCKED: {
    title: "内容安全拦截",
    guidance: "调整问题后重试",
  },
  UPSTREAM_TIMEOUT: {
    title: "AI 生成超时",
    guidance: "重试此任务",
    retryLabel: "重试此任务",
  },
  UPSTREAM_UNAVAILABLE: {
    title: "Agent 服务不可用",
    guidance: "检查服务状态后重试",
  },
  UPSTREAM_NOT_CONFIGURED: {
    title: "Agent 服务未配置",
    guidance: "检查远程 Agent 环境变量",
  },
  COURSE_NOT_READY: {
    title: "课程不可用",
    guidance: "课程资料未同步",
  },
  NETWORK_UNAVAILABLE: {
    title: "接口异常",
    guidance: "检查网络后重试",
  },
}

function presentation(error: ApiError | Error | string) {
  if (!(error instanceof ApiError)) {
    return { title: "接口异常", guidance: "稍后重试" }
  }
  return (
    errorPresentations[error.code] ?? {
      title: "AI 生成失败",
      guidance: error.retryable ? "稍后重试" : "检查任务参数",
    }
  )
}

export function ErrorNotice({ error, onRetry }: ErrorNoticeProps) {
  const message = typeof error === "string" ? error : error.message
  const meta = presentation(error)
  const canRetry = error instanceof ApiError && error.retryable && onRetry

  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-rose-100 bg-rose-50/50 p-4 shadow-sm"
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="mt-0.5 h-5 w-5 text-rose-550 text-rose-500 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-rose-700">{meta.title}</p>
        <p className="mt-1 text-sm font-medium leading-relaxed text-rose-600">{message}</p>
        {!canRetry || meta.guidance !== meta.retryLabel ? (
          <p className="mt-1 text-xs font-semibold text-rose-500">{meta.guidance}</p>
        ) : null}
        {error instanceof ApiError && error.traceId ? (
          <p className="mt-2 text-xs font-semibold text-rose-400">追踪号：{error.traceId}</p>
        ) : null}
      </div>
      {canRetry ? (
        <button
          className="inline-flex h-9 shrink-0 items-center gap-2 rounded-xl border border-rose-200 bg-white px-3 text-sm font-semibold text-rose-600 shadow-sm transition-all duration-150 hover:bg-rose-50 hover:border-rose-300 active:scale-95"
          onClick={onRetry}
          type="button"
        >
          <RotateCcw aria-hidden="true" className="h-4 w-4" />
          {meta.retryLabel ?? "重试"}
        </button>
      ) : null}
    </div>
  )
}
