import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { UserIdLoginForm } from "@/components/auth/user-id-login-form"
import { apiFetch } from "@/lib/api/client"

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

describe("UserIdLoginForm", () => {
  beforeEach(() => {
    localStorage.clear()
    push.mockReset()
    vi.mocked(apiFetch).mockReset()
  })

  it("stores a trimmed new-user ID and routes to profile collection", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      exists: false,
      user_id: "student-001",
      display_name: null,
      profile: null,
      profile_confirmed: false,
    })

    render(<UserIdLoginForm />)

    await userEvent.type(screen.getByLabelText("用户 ID"), " student-001 ")
    await userEvent.click(screen.getByRole("button", { name: "进入学习平台" }))

    expect(localStorage.getItem("zhixue_user_id")).toBe("student-001")
    expect(push).toHaveBeenCalledWith("/profile")
  })
})
