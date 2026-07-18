import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { LoginPanel } from "@/components/auth/login-panel"
import { ApiError, apiFetch } from "@/lib/api/client"

const push = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}))

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>(
    "@/lib/api/client",
  )
  return { ...actual, apiFetch: vi.fn() }
})

describe("LoginPanel", () => {
  beforeEach(() => {
    localStorage.clear()
    push.mockReset()
    vi.mocked(apiFetch).mockReset()
  })

  it("routes a new user to profile collection", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      exists: false,
      user_id: "student-001",
      display_name: null,
      profile: null,
      profile_confirmed: false,
    })
    render(<LoginPanel />)

    await userEvent.click(screen.getByRole("button", { name: "进入学习空间" }))
    await userEvent.type(screen.getByLabelText("用户 ID"), " student-001 ")
    await userEvent.click(screen.getByRole("button", { name: "进入学习平台" }))

    expect(localStorage.getItem("zhixue_user_id")).toBe("student-001")
    expect(push).toHaveBeenCalledWith("/profile")
  })

  it("routes a returning user to the workspace", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      exists: true,
      user_id: "student-002",
      display_name: "同学",
      profile: null,
      profile_confirmed: true,
    })
    render(<LoginPanel />)

    await userEvent.click(screen.getByRole("button", { name: "进入学习空间" }))
    await userEvent.type(screen.getByLabelText("用户 ID"), "student-002")
    await userEvent.click(screen.getByRole("button", { name: "进入学习平台" }))

    expect(push).toHaveBeenCalledWith("/workspace")
  })

  it("shows gateway errors beside the form", async () => {
    vi.mocked(apiFetch).mockRejectedValue(
      new ApiError("NETWORK_UNAVAILABLE", "学习服务暂时不可用。", true),
    )
    render(<LoginPanel />)

    await userEvent.click(screen.getByRole("button", { name: "进入学习空间" }))
    await userEvent.type(screen.getByLabelText("用户 ID"), "student-003")
    await userEvent.click(screen.getByRole("button", { name: "进入学习平台" }))

    expect(await screen.findByText("学习服务暂时不可用。")).toBeInTheDocument()
    expect(push).not.toHaveBeenCalled()
  })
})
