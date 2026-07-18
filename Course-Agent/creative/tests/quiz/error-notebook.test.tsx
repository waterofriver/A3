import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ErrorNotebook } from "@/components/quiz/error-notebook"

const data = {
  total_errors: 1,
  unique_concepts: 1,
  questions: [
    {
      question_id: "q-1",
      attempt_id: "a-1",
      quiz_title: "ROS2 基础",
      prompt: "发布者与订阅者如何通信？",
      question_type: "choice",
      options: ["话题", "服务"],
      user_answer: "服务",
      correct_answer: "话题",
      explanation: "发布订阅通过话题传递消息。",
      concept: "发布订阅通信",
      created_at: "2026-07-18T09:00:00Z",
    },
  ],
}

describe("ErrorNotebook", () => {
  it("keeps hook order when loading turns into a populated notebook", () => {
    const view = render(
      <ErrorNotebook data={undefined} error={null} isLoading onRetry={() => undefined} />,
    )

    view.rerender(
      <ErrorNotebook data={data} error={null} isLoading={false} onRetry={() => undefined} />,
    )

    expect(screen.getByText("1 道错题")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: /发布订阅通信/ })).toBeInTheDocument()
  })
})
