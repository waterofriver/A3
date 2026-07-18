import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { ImmersiveLoginPage } from "@/components/landing/immersive-login-page"

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock("@/components/landing/learning-core-scene", () => ({
  LearningCoreScene: ({ activeChapter }: { activeChapter?: number }) => <div data-testid="learning-core-scene" data-active-chapter={activeChapter} />,
}))

describe("ImmersiveLoginPage", () => {
  it("presents the approved learning capabilities without course-specific content", () => {
    render(<ImmersiveLoginPage />)

    expect(screen.getByRole("heading", { name: "智学引擎" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "学习画像" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "智能资源" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "成长路径" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "评估与记忆" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "进入学习空间" })).toBeInTheDocument()
    expect(screen.queryByText(/ROS|机器人|实验/)).not.toBeInTheDocument()
  })

  it("opens and closes the floating login panel", async () => {
    render(<ImmersiveLoginPage />)

    await userEvent.click(screen.getByRole("button", { name: "进入学习空间" }))

    expect(screen.getByRole("dialog", { name: "进入学习空间" })).toBeInTheDocument()
    expect(screen.getByLabelText("用户 ID")).toBeInTheDocument()

    await userEvent.click(screen.getByRole("button", { name: "关闭登录窗口" }))

    expect(screen.queryByRole("dialog", { name: "进入学习空间" })).not.toBeInTheDocument()
  })

  it("moves to exactly one next chapter with the ArrowDown key", async () => {
    const scrollTo = vi.fn()
    Object.defineProperty(window, "scrollTo", { configurable: true, value: scrollTo })
    render(<ImmersiveLoginPage />)

    await userEvent.keyboard("{ArrowDown}")

    expect(scrollTo).toHaveBeenCalledTimes(1)
    expect(scrollTo).toHaveBeenCalledWith(expect.objectContaining({ behavior: "smooth" }))
  })

  it("does not pass chapter navigation into the particle scene", async () => {
    render(<ImmersiveLoginPage />)

    await userEvent.keyboard("{ArrowDown}")

    expect(screen.getByTestId("learning-core-scene")).not.toHaveAttribute("data-active-chapter")
  })
})
