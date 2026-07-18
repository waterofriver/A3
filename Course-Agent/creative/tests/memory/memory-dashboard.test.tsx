import { render, screen, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { MemoryDashboard, type MemoryReport } from "@/components/memory/memory-dashboard"

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  getRememberedCourse: vi.fn(),
  getUserId: vi.fn(),
  selectInitialCourse: vi.fn(),
  subscribeToSelectedCourse: vi.fn(),
}))

vi.mock("@/lib/session/user-session", () => ({ getUserId: mocks.getUserId }))
vi.mock("@/lib/course-selection", () => ({
  getRememberedCourse: mocks.getRememberedCourse,
  selectInitialCourse: mocks.selectInitialCourse,
  subscribeToSelectedCourse: mocks.subscribeToSelectedCourse,
}))
vi.mock("@/lib/api/client", () => ({ apiFetch: mocks.apiFetch }))

import MemoryPage from "@/app/(platform)/memory/page"

const report: MemoryReport = {
  memory_health: 68,
  summary: "ROS2 通信相关知识正在遗忘，建议今天安排一次短时复习。",
  has_personal_evidence: true,
  knowledge_points: [
    {
      id: "qos",
      name: "QoS 通信策略",
      retention: 58,
      base_mastery: 74,
      days_since_review: 5,
      risk_level: "urgent",
      curve: [
        { day: 0, retention: 74 },
        { day: 3, retention: 63 },
        { day: 5, retention: 58 },
        { day: 7, retention: 48 },
      ],
      recommendation: "建议复习 QoS 的可靠性与持久性设置，再完成一题变式练习。",
      blockage: {
        knowledge_point_id: "pub-sub",
        name: "发布订阅通信",
        reason: "先理解消息如何传递，再处理 QoS 策略会更轻松。",
      },
    },
  ],
  today_actions: [
    {
      knowledge_point_id: "qos",
      title: "回忆 QoS 策略的适用场景",
      minutes: 8,
      action_type: "recall",
      reason: "距离上次复习已 5 天，正处在最佳复习窗口。",
    },
  ],
}

describe("MemoryDashboard", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset()
    mocks.getRememberedCourse.mockReturnValue(null)
    mocks.getUserId.mockReturnValue(null)
    mocks.selectInitialCourse.mockReturnValue(undefined)
    mocks.subscribeToSelectedCourse.mockReturnValue(() => undefined)
  })
  it("shows actionable revision advice, curve description, and prerequisite help", () => {
    render(<MemoryDashboard report={report} />)

    expect(screen.getByRole("heading", { name: "今日复习建议" })).toBeInTheDocument()
    expect(screen.getByText(/建议复习 QoS 的可靠性/)).toBeInTheDocument()
    expect(screen.getByLabelText(/QoS 通信策略的预计记忆保持度曲线/)).toBeInTheDocument()
    expect(screen.getByText("先补什么")).toBeInTheDocument()
    expect(screen.getByText("发布订阅通信")).toBeInTheDocument()
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "QoS 通信策略" })).toHaveAttribute("aria-pressed", "true")
  })

  it("shows a clear empty state before the user signs in", () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryPage />
      </QueryClientProvider>,
    )

    expect(screen.getByText("请先登录后查看你的记忆地图。")).toBeInTheDocument()
  })

  it("shows a clear empty state when there is no available course", async () => {
    mocks.getUserId.mockReturnValue("student-1")
    mocks.apiFetch.mockResolvedValue([])
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryPage />
      </QueryClientProvider>,
    )

    expect(await screen.findByText("暂时没有可用课程，选择课程后即可生成记忆地图。")).toBeInTheDocument()
    expect(mocks.subscribeToSelectedCourse).toHaveBeenCalled()
  })

  it("waits for the remembered course before requesting a report and follows course changes", async () => {
    let courseListener: ((name: string) => void) | undefined
    mocks.getUserId.mockReturnValue("student-1")
    mocks.getRememberedCourse.mockReturnValue("ROS2 通信")
    mocks.subscribeToSelectedCourse.mockImplementation((listener) => {
      courseListener = listener
      return () => undefined
    })
    mocks.selectInitialCourse.mockImplementation((courses, rememberedName) =>
      courses.find((course: { name: string }) => course.name === rememberedName) ?? courses[0],
    )
    mocks.apiFetch.mockImplementation((path: string) =>
      Promise.resolve(path === "/api/course/list" ? [
        { name: "默认课程", content_ready: true },
        { name: "ROS2 通信", content_ready: true },
        { name: "新课程", content_ready: true },
      ] : report),
    )
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    queryClient.setQueryData(["courses"], [
      { name: "默认课程", content_ready: true },
      { name: "ROS2 通信", content_ready: true },
      { name: "新课程", content_ready: true },
    ])
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryPage />
      </QueryClientProvider>,
    )

    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("course_name=ROS2%20%E9%80%9A%E4%BF%A1")))
    expect(mocks.apiFetch).not.toHaveBeenCalledWith(expect.stringContaining("course_name=%E9%BB%98%E8%AE%A4%E8%AF%BE%E7%A8%8B"))
    courseListener?.("新课程")
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalledWith(expect.stringContaining("course_name=%E6%96%B0%E8%AF%BE%E7%A8%8B")))
  })
})
