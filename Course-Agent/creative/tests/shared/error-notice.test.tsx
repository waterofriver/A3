import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { ErrorNotice } from "@/components/shared/error-notice"
import { ApiError } from "@/lib/api/client"

describe("ErrorNotice", () => {
  it("labels network failures as interface errors", () => {
    render(
      <ErrorNotice
        error={new ApiError("NETWORK_UNAVAILABLE", "网络不可用。", true)}
        onRetry={vi.fn()}
      />,
    )

    expect(screen.getByText("接口异常")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "重试" })).toBeInTheDocument()
  })

  it("does not offer retry for blocked content", () => {
    render(
      <ErrorNotice
        error={new ApiError("CONTENT_BLOCKED", "内容未通过安全检查。", false)}
      />,
    )

    expect(screen.getByText("内容安全拦截")).toBeInTheDocument()
    expect(screen.getByText("调整问题后重试")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "重试" })).not.toBeInTheDocument()
  })
})
