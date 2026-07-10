import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ResourceCard } from "@/components/resources/resource-card"
import type { ResourceDetail } from "@/lib/api/resource-types"

const base = {
  id: "res-1",
  task_id: "task-1",
  course_name: "机器人操作系统",
  created_at: "2026-07-10T08:00:00Z",
}

const handoutResource: ResourceDetail = {
  ...base,
  resource_type: "handout",
  title: "ROS2 讲义",
  payload: { markdown: "# 节点通信\n\n| 项目 | 内容 |\n| --- | --- |\n| 模式 | 发布订阅 |" },
  media_url: null,
}

const codeResource: ResourceDetail = {
  ...base,
  id: "res-2",
  resource_type: "code",
  title: "ROS2 publisher",
  payload: {
    language: "python",
    code: "publisher.publish(message)",
    description: "发布消息",
  },
  media_url: null,
}

const videoResource: ResourceDetail = {
  ...base,
  id: "res-3",
  resource_type: "video",
  title: "ROS2 视频",
  payload: {
    summary: "节点通信讲解",
    poster_url: "http://localhost:8000/media/poster.png",
    duration_seconds: 180,
  },
  media_url: "http://localhost:8000/media/video.mp4",
}

describe("ResourceCard", () => {
  it("renders handout, code, and video payloads with actions", () => {
    const { rerender } = render(<ResourceCard resource={handoutResource} />)
    expect(screen.getByRole("heading", { name: "ROS2 讲义" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "复制内容" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "下载文档" })).toBeInTheDocument()
    expect(screen.getByRole("table")).toBeInTheDocument()

    rerender(<ResourceCard resource={codeResource} />)
    expect(screen.getByText("python")).toBeInTheDocument()
    expect(screen.getByText("publisher.publish(message)")).toBeInTheDocument()

    rerender(<ResourceCard resource={videoResource} />)
    expect(screen.getByTestId("video-player")).toHaveAttribute(
      "src",
      videoResource.media_url,
    )
  })

  it("shows a truthful video empty state when the agent returned no url", () => {
    render(
      <ResourceCard
        resource={{ ...videoResource, id: "res-empty", media_url: null }}
      />,
    )

    expect(screen.getByText("等待 Agent 返回视频素材")).toBeInTheDocument()
    expect(screen.queryByTestId("video-player")).not.toBeInTheDocument()
  })
})
