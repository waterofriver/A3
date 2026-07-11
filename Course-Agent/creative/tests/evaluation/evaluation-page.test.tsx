import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { EvaluationPageContent } from "@/components/evaluation/evaluation-page-content"
import type { components } from "@/lib/api/generated"

type EvaluationReport = components["schemas"]["EvaluationReportData"]

const report: EvaluationReport = {
  id: "report-1",
  user_id: "student-001",
  course_name: "机器人操作系统",
  theory_score: 80,
  practice_score: 50,
  weak_points: [{ name: "ROS2 服务通信", frequency: 3 }],
  recommended_changes: [
    {
      stage_name: "ROS2 服务通信专项练习",
      difficulty: "巩固",
      reason: "该薄弱项在学习证据中出现 3 次。",
      resource_id: "quiz-1",
    },
  ],
  source_path_id: "path-1",
  applied_path_id: null,
  created_at: "2026-07-11T03:00:00Z",
}

describe("EvaluationPageContent", () => {
  it("shows scores, weak points, and applies the recommended plan", async () => {
    const onApply = vi.fn()
    render(
      <EvaluationPageContent
        isApplying={false}
        onApply={onApply}
        report={report}
      />,
    )

    expect(screen.getByText("理论掌握度")).toBeInTheDocument()
    expect(screen.getByText("80")).toBeInTheDocument()
    expect(screen.getByText("实操能力")).toBeInTheDocument()
    expect(screen.getByText("50")).toBeInTheDocument()
    expect(screen.getByText("ROS2 服务通信")).toBeInTheDocument()

    await userEvent.click(
      screen.getByRole("button", { name: "一键更新学习计划" }),
    )
    expect(onApply).toHaveBeenCalledWith(report.id)
  })

  it("renders an explicit empty state when evidence is not ready", () => {
    render(
      <EvaluationPageContent
        isApplying={false}
        onApply={() => undefined}
        report={null}
      />,
    )

    expect(screen.getByText("评估数据不足")).toBeInTheDocument()
    expect(
      screen.queryByRole("button", { name: "一键更新学习计划" }),
    ).not.toBeInTheDocument()
  })
})
