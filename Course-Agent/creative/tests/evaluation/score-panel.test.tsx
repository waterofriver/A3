import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ScorePanel } from "@/components/evaluation/score-panel"

describe("ScorePanel", () => {
  it("keeps score content inset from each card edge", () => {
    const { container } = render(<ScorePanel practiceScore={11} theoryScore={25} />)

    expect(screen.getByText("理论掌握度")).toBeVisible()
    expect(container.querySelectorAll("article.p-6")).toHaveLength(2)
  })
})
