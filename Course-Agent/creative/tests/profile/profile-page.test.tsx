import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProfilePage } from "@/components/profile/profile-page"
import type { components } from "@/lib/api/generated"
import type { GatewayEvent } from "@/lib/sse/task-reducer"

type UserInfo = components["schemas"]["UserInfoData"]

const push = vi.fn()

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}))

const event = (overrides: Partial<GatewayEvent>): GatewayEvent => ({
  event: "content.delta",
  task_id: "task-1",
  seq: 1,
  trace_id: "trace-1",
  progress: 20,
  content: "",
  finish_flag: false,
  resource_ids: [],
  demo_mode: true,
  ...overrides,
})

function renderProfilePage(
  options: Partial<React.ComponentProps<typeof ProfilePage>> = {},
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfilePage {...options} />
    </QueryClientProvider>,
  )
}

describe("ProfilePage", () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem("zhixue_user_id", "student-001")
    push.mockReset()
  })

  it("streams assistant text and updates the six-dimension panel", async () => {
    const loadUser = vi.fn<() => Promise<UserInfo>>().mockResolvedValue({
      exists: false,
      user_id: "student-001",
      display_name: null,
      profile: null,
      profile_confirmed: false,
    })
    const streamProfile = vi.fn(async (_path, _body, onEvent) => {
      onEvent(
        event({
          event: "agent.started",
          current_agent: "画像抽取Agent",
          progress: 10,
        }),
      )
      onEvent(
        event({
          event: "content.delta",
          seq: 2,
          progress: 45,
          content: "正在分析你的学习目标。",
        }),
      )
      onEvent(
        event({
          event: "profile.patch",
          seq: 3,
          progress: 85,
          profile_patch: {
            knowledge_foundation: "入门基础",
            cognitive_style: "案例驱动",
            weak_points: ["ROS2 通信"],
            learning_pace: "分阶段",
            content_preferences: ["代码案例"],
            short_term_goal: "完成通信强化",
          },
        }),
      )
      onEvent(
        event({
          event: "task.completed",
          seq: 4,
          progress: 100,
          finish_flag: true,
        }),
      )
      return "task-1"
    })
    renderProfilePage({ loadUser, streamProfile })

    const input = await screen.findByPlaceholderText(
      "介绍你的专业、基础或学习目标",
    )
    await userEvent.type(input, "我想加强 ROS2 通信")
    await userEvent.click(screen.getByRole("button", { name: "发送" }))

    expect(await screen.findByText("正在分析你的学习目标。")).toBeInTheDocument()
    expect(screen.getAllByText("ROS2 通信").length).toBeGreaterThan(0)
    expect(screen.getByText("画像抽取Agent")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "画像确认完成" })).toBeEnabled()
  })

  it("confirms a complete profile and opens the workspace", async () => {
    const completeProfile = {
      knowledge_foundation: "入门基础",
      cognitive_style: "案例驱动",
      weak_points: ["ROS2 通信"],
      learning_pace: "分阶段",
      content_preferences: ["代码案例"],
      short_term_goal: "完成通信强化",
    }
    const loadUser = vi.fn<() => Promise<UserInfo>>().mockResolvedValue({
      exists: true,
      user_id: "student-001",
      display_name: null,
      profile: completeProfile,
      profile_confirmed: false,
    })
    const confirmProfile = vi
      .fn<() => Promise<UserInfo>>()
      .mockResolvedValue({
        exists: true,
        user_id: "student-001",
        display_name: null,
        profile: completeProfile,
        profile_confirmed: true,
      })
    renderProfilePage({ loadUser, confirmProfile })

    await userEvent.click(
      await screen.findByRole("button", { name: "画像确认完成" }),
    )

    expect(confirmProfile).toHaveBeenCalled()
    expect(push).toHaveBeenCalledWith("/workspace")
  })
})
