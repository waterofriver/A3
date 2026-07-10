import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { QuizPlayer } from "@/components/resources/quiz-player"
import type { QuizResourceDetail } from "@/lib/api/resource-types"

const resource: QuizResourceDetail = {
  id: "quiz-1",
  task_id: "task-1",
  course_name: "机器人操作系统",
  title: "ROS2 题库",
  media_url: null,
  created_at: "2026-07-10T08:00:00Z",
  resource_type: "quiz",
  payload: {
    questions: [
      {
        id: "q1",
        question_type: "choice",
        prompt: "选择正确选项",
        options: ["A", "B"],
        answer: "B",
        explanation: "B 是正确选项。",
      },
      {
        id: "q2",
        question_type: "blank",
        prompt: "填写节点名称",
        options: [],
        answer: "节点",
        explanation: "节点是基本运行单元。",
      },
    ],
  },
}

describe("QuizPlayer", () => {
  it("submits answers and displays score with explanations", async () => {
    const user = userEvent.setup()
    const submitQuiz = vi.fn().mockResolvedValue({
      attempt_id: "attempt-1",
      score: 100,
      results: [
        {
          question_id: "q1",
          correct: true,
          submitted_answer: "B",
          expected_answer: "B",
          explanation: "B 是正确选项。",
        },
        {
          question_id: "q2",
          correct: true,
          submitted_answer: "节点",
          expected_answer: "节点",
          explanation: "节点是基本运行单元。",
        },
      ],
    })
    render(
      <QuizPlayer
        resource={resource}
        submitQuiz={submitQuiz}
        userId="student-001"
      />,
    )

    await user.click(screen.getByLabelText("B"))
    await user.type(screen.getByLabelText("填写节点名称"), "节点")
    await user.click(screen.getByRole("button", { name: "提交答案" }))

    expect(submitQuiz).toHaveBeenCalledWith({ q1: "B", q2: "节点" })
    expect(await screen.findByText("得分 100")).toBeInTheDocument()
    expect(screen.getByText("节点是基本运行单元。")).toBeInTheDocument()
  })
})
