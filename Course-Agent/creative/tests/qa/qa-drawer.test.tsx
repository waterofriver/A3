import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { QaDrawer } from "@/components/qa/qa-drawer"
import type { GatewayEvent } from "@/lib/sse/task-reducer"

const event = (overrides: Partial<GatewayEvent>): GatewayEvent => ({
  event: "content.delta",
  task_id: "qa-task-1",
  seq: 1,
  trace_id: "trace-qa-1",
  progress: 20,
  content: "",
  finish_flag: false,
  resource_ids: [],
  demo_mode: true,
  ...overrides,
})

describe("QaDrawer", () => {
  it("streams Markdown and shows a truthful empty media state in demo mode", async () => {
    const streamQa = vi.fn(async (_path, _body, onEvent) => {
      onEvent(
        event({
          event: "agent.started",
          current_agent: "智能答疑Agent",
          progress: 10,
        }),
      )
      onEvent(
        event({
          event: "content.delta",
          seq: 2,
          content: "## 发布订阅\n\n发布者负责发送消息。",
          progress: 55,
        }),
      )
      onEvent(
        event({
          event: "media.ready",
          seq: 3,
          resource_type: "video",
          media_url: null,
          content: "等待真实多模态 Agent 返回素材链接。",
          progress: 88,
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
      return "qa-task-1"
    })

    render(
      <QaDrawer
        open
        onOpenChange={() => undefined}
        streamQa={streamQa}
        userId="student-001"
      />,
    )

    await userEvent.type(
      screen.getByLabelText("课程问题"),
      "什么是发布订阅？",
    )
    await userEvent.click(screen.getByRole("radio", { name: "短视频讲解" }))
    await userEvent.click(screen.getByRole("button", { name: "发送问题" }))

    expect(await screen.findByRole("heading", { name: "发布订阅" })).toBeInTheDocument()
    expect(screen.getByText("智能答疑Agent")).toBeInTheDocument()
    expect(screen.getByText("等待真实 Agent 返回素材")).toBeInTheDocument()
    expect(screen.queryByTestId("video-player")).not.toBeInTheDocument()
    expect(streamQa).toHaveBeenCalledWith(
      "/api/chat/qa",
      {
        user_id: "student-001",
        question: "什么是发布订阅？",
        answer_mode: "video",
      },
      expect.any(Function),
      expect.any(AbortSignal),
    )
  })

  it("renders a video card when the real Agent returns a media URL", async () => {
    const streamQa = vi.fn(async (_path, _body, onEvent) => {
      onEvent(
        event({
          event: "media.ready",
          resource_type: "video",
          media_url: "https://agent.example/lesson.mp4",
          progress: 88,
        }),
      )
      onEvent(
        event({
          event: "task.completed",
          seq: 2,
          progress: 100,
          finish_flag: true,
        }),
      )
      return "qa-task-1"
    })

    render(
      <QaDrawer
        open
        onOpenChange={() => undefined}
        streamQa={streamQa}
        userId="student-001"
      />,
    )
    await userEvent.type(screen.getByLabelText("课程问题"), "请用视频讲解")
    await userEvent.click(screen.getByRole("radio", { name: "短视频讲解" }))
    await userEvent.click(screen.getByRole("button", { name: "发送问题" }))

    await waitFor(() => expect(screen.getByTestId("video-player")).toBeInTheDocument())
    expect(screen.getByTestId("video-player")).toHaveAttribute(
      "src",
      "https://agent.example/lesson.mp4",
    )
  })
})
