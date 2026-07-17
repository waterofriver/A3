import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { KnowledgeTree } from "@/components/knowledge/knowledge-tree"

const chapters = [
  {
    path: "first",
    name: "第一章",
    documents: [
      {
        id: "first-document",
        chapter_path: "first",
        filename: "第一章资料.pdf",
        file_type: "pdf",
        sha256: "first",
        size_bytes: 1,
        preview_text: null,
        media_url: "/first.pdf",
      },
    ],
  },
  {
    path: "second",
    name: "第二章",
    documents: [
      {
        id: "second-document",
        chapter_path: "second",
        filename: "第二章资料.pdf",
        file_type: "pdf",
        sha256: "second",
        size_bytes: 1,
        preview_text: null,
        media_url: "/second.pdf",
      },
    ],
  },
]

describe("KnowledgeTree", () => {
  it("keeps only the most recently opened chapter expanded", async () => {
    const user = userEvent.setup()
    render(<KnowledgeTree chapters={chapters} onSelect={vi.fn()} />)

    expect(screen.getByText("第一章资料.pdf")).toBeInTheDocument()
    expect(screen.queryByText("第二章资料.pdf")).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "第二章" }))

    expect(screen.queryByText("第一章资料.pdf")).not.toBeInTheDocument()
    expect(screen.getByText("第二章资料.pdf")).toBeInTheDocument()
  })
})
