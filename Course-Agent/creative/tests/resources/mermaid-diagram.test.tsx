import { describe, expect, it } from "vitest"
import { render, screen } from "@testing-library/react"

import { MermaidDiagram } from "@/components/resources/mermaid-diagram"

const VALID_MERMAID = `graph TD
    A[Start] --> B[End]`

const INVALID_MERMAID = "this is not valid mermaid syntax @@@@"

describe("MermaidDiagram", () => {
  it("shows a loading state on first render", () => {
    render(<MermaidDiagram code={VALID_MERMAID} />)
    expect(screen.getByRole("status")).toBeDefined()
  })

  it("renders an error state for invalid Mermaid syntax", async () => {
    render(<MermaidDiagram code={INVALID_MERMAID} />)
    const errorText = await screen.findByText(/图解渲染失败/, {}, { timeout: 8000 })
    expect(errorText).toBeDefined()
  })

  // SVG rendering requires a real browser (getBoundingClientRect etc.);
  // jsdom cannot produce the final <svg> output.  The happy path is
  // validated in the full-platform-flow Playwright e2e suite instead.
})
