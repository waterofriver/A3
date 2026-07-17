import { render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { AppShell } from "@/components/app-shell/app-shell"
import { SessionGuard } from "@/components/app-shell/session-guard"
import { announceDemoMode } from "@/lib/runtime/demo-mode"

const replace = vi.fn()

vi.mock("next/navigation", () => ({
  usePathname: () => "/workspace",
  useRouter: () => ({ push: vi.fn(), replace }),
}))

describe("AppShell", () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem("zhixue_user_id", "student-001")
    replace.mockReset()
  })

  it("renders the five fixed navigation destinations", () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>,
    )

    for (const label of [
      "画像采集",
      "资源工作台",
      "学习路径",
      "学习评估",
      "课程知识库",
    ]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument()
    }
    expect(screen.queryByText("社区")).not.toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "打开智能答疑" }),
    ).toBeInTheDocument()
  })

  it("redirects a missing session to login", async () => {
    localStorage.clear()
    render(
      <SessionGuard>
        <div>private content</div>
      </SessionGuard>,
    )

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/login"))
    expect(screen.queryByText("private content")).not.toBeInTheDocument()
  })

  it("renders guarded content for a stored user", async () => {
    render(
      <SessionGuard>
        <div>private content</div>
      </SessionGuard>,
    )

    expect(await screen.findByText("private content")).toBeInTheDocument()
  })

  it("shows demo mode in remote mode only after a fallback event", async () => {
    render(
      <AppShell initialDemoMode={false}>
        <div>remote content</div>
      </AppShell>,
    )
    expect(screen.queryByText("演示模式")).not.toBeInTheDocument()

    announceDemoMode()

    expect(await screen.findByText("演示模式")).toBeInTheDocument()
  })

  it("shows the selected course instead of generic course status badges", () => {
    localStorage.setItem("zhixue_selected_course", "机器人与安全")

    render(
      <AppShell>
        <div>course content</div>
      </AppShell>,
    )

    expect(screen.getByText("机器人与安全")).toBeInTheDocument()
    expect(screen.queryByText("课程未选择")).not.toBeInTheDocument()
    expect(screen.queryByText("演示模式")).not.toBeInTheDocument()
  })
})
