import { render, screen } from "@testing-library/react"
import { Database } from "lucide-react"
import { describe, expect, it, vi } from "vitest"

import { EmptyState } from "@/components/shared/empty-state"
import { ErrorNotice } from "@/components/shared/error-notice"
import { OfflineBanner } from "@/components/shared/offline-banner"
import { ResourceErrorBoundary } from "@/components/shared/resource-error-boundary"
import { ApiError } from "@/lib/api/client"

describe("shared states", () => {
  it.each([
    ["VALIDATION_ERROR", "检查输入内容", false],
    ["CONTENT_BLOCKED", "调整问题后重试", false],
    ["UPSTREAM_TIMEOUT", "重试此任务", true],
    ["COURSE_NOT_READY", "课程资料未同步", false],
  ])("maps %s to the expected action", (code, label, retryable) => {
    render(
      <ErrorNotice
        error={new ApiError(code, "message", retryable, "trace-1")}
        onRetry={vi.fn()}
      />,
    )

    expect(screen.getByText(label)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /重试/ }) !== null).toBe(
      retryable,
    )
  })

  it("shows cached content beneath a non-modal offline banner", () => {
    const { rerender } = render(
      <div>
        <OfflineBanner online={false} />
        <p>已缓存课程内容</p>
      </div>,
    )

    expect(screen.getByText("当前离线，正在显示已缓存内容")).toBeInTheDocument()
    expect(screen.getByText("已缓存课程内容")).toBeInTheDocument()

    rerender(<OfflineBanner online />)
    expect(
      screen.queryByText("当前离线，正在显示已缓存内容"),
    ).not.toBeInTheDocument()
  })

  it("renders one-action empty states", () => {
    render(
      <EmptyState
        action={{ label: "返回工作台", onClick: vi.fn() }}
        description="尚未生成课程资源。"
        icon={Database}
        title="暂无资源"
      />,
    )

    expect(screen.getByText("暂无资源")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "返回工作台" })).toBeInTheDocument()
  })

  it("isolates a broken resource renderer and keeps its trace id", () => {
    function BrokenResource(): never {
      throw new Error("renderer failed")
    }
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => undefined)

    render(
      <ResourceErrorBoundary traceId="trace-render-1">
        <BrokenResource />
      </ResourceErrorBoundary>,
    )

    expect(screen.getByText("该资源暂时无法显示")).toBeInTheDocument()
    expect(screen.getByText("追踪号：trace-render-1")).toBeInTheDocument()
    consoleError.mockRestore()
  })
})
