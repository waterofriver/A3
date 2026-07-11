import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { AnswerModeControl } from "@/components/qa/answer-mode-control"

describe("AnswerModeControl", () => {
  it("renders all three mode labels inside the segmented control", () => {
    render(
      <AnswerModeControl
        onValueChange={vi.fn()}
        value="text"
      />,
    )

    expect(screen.getByText("纯文字")).toBeVisible()
    expect(screen.getByText("图解配图")).toBeVisible()
    expect(screen.getByText("短视频讲解")).toBeVisible()
  })
})
