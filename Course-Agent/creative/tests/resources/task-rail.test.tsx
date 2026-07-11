import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { TaskRail } from "@/components/resources/task-rail"
import { createResourceTaskState } from "@/lib/query/resource-cache"

describe("TaskRail", () => {
  it("keeps completed and failed resource rows visible independently", () => {
    const task = createResourceTaskState("task-1")
    task.status = "running"
    task.currentAgent = "题库Agent"
    task.byType.handout.status = "succeeded"
    task.byType.quiz.status = "failed"
    task.byType.quiz.error = {
      code: "UPSTREAM_TIMEOUT",
      message: "题库生成超时",
      retryable: true,
    }

    render(
      <TaskRail
        connectionState="open"
        onRetry={vi.fn()}
        selectedTypes={["handout", "quiz"]}
        task={task}
      />,
    )

    expect(screen.getByText("讲义文档")).toBeInTheDocument()
    expect(screen.getByText("习题题库")).toBeInTheDocument()
    expect(screen.getByText("已完成")).toBeInTheDocument()
    expect(screen.getByText("生成失败")).toBeInTheDocument()
    expect(screen.getByText("题库生成超时")).toBeInTheDocument()
    expect(screen.getByText("可重试")).toBeInTheDocument()
    expect(screen.getByText("题库Agent")).toBeInTheDocument()
  })
})
