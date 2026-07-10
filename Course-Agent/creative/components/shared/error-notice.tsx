import { AlertCircle, RotateCcw } from "lucide-react"

import { ApiError } from "@/lib/api/client"

type ErrorNoticeProps = {
  error: ApiError | Error | string
  onRetry?: () => void
}

function errorTitle(error: ApiError | Error | string) {
  if (!(error instanceof ApiError)) return "接口异常"
  if (error.code === "VALIDATION_ERROR") return "参数缺失"
  if (error.code === "NETWORK_UNAVAILABLE") return "接口异常"
  return "AI 生成失败"
}

export function ErrorNotice({ error, onRetry }: ErrorNoticeProps) {
  const message = typeof error === "string" ? error : error.message
  const canRetry = error instanceof ApiError && error.retryable && onRetry

  return (
    <div
      className="flex items-start gap-3 rounded-md border border-[#efc7c2] bg-[#fff7f5] p-4"
      role="alert"
    >
      <AlertCircle aria-hidden="true" className="mt-0.5 h-5 w-5 text-[#c7463c]" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-[#8d3029]">{errorTitle(error)}</p>
        <p className="mt-1 text-sm leading-6 text-[#74514e]">{message}</p>
        {error instanceof ApiError && error.traceId ? (
          <p className="mt-2 text-xs text-[#9a6f6a]">追踪号：{error.traceId}</p>
        ) : null}
      </div>
      {canRetry ? (
        <button
          className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md border border-[#e4aaa3] bg-white px-3 text-sm font-medium text-[#9f3b32] transition hover:bg-[#fff0ed]"
          onClick={onRetry}
          type="button"
        >
          <RotateCcw aria-hidden="true" className="h-4 w-4" />
          重试
        </button>
      ) : null}
    </div>
  )
}
