import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { KnowledgePageContent } from "@/components/knowledge/knowledge-page-content"
import type { components } from "@/lib/api/generated"

type CourseBase = components["schemas"]["CourseBaseData"]

const readyCourse: CourseBase = {
  name: "机器人操作系统",
  slug: "ros2",
  content_ready: true,
  is_demo: false,
  chapters: [
    {
      path: "01-basics",
      name: "01 基础知识",
      documents: [
        {
          id: "doc-1",
          chapter_path: "01-basics",
          filename: "intro.md",
          file_type: "md",
          sha256: "abc",
          size_bytes: 128,
          preview_text: "# ROS2 基础\n\n真实课程正文",
          media_url: "/media/courses/ros2/01-basics/intro.md",
        },
      ],
    },
  ],
}

const notReadyCourse: CourseBase = {
  name: "机器人操作系统（演示）",
  slug: "robotics-demo",
  content_ready: false,
  is_demo: true,
  chapters: [],
}

describe("KnowledgePageContent", () => {
  it("renders real chapters and an explicit not-ready state", () => {
    const { rerender } = render(<KnowledgePageContent course={readyCourse} />)

    expect(screen.getByText("01 基础知识")).toBeInTheDocument()
    expect(screen.getAllByText("intro.md").length).toBeGreaterThan(0)
    expect(screen.getByRole("heading", { name: "ROS2 基础" })).toBeInTheDocument()

    rerender(<KnowledgePageContent course={notReadyCourse} />)
    expect(screen.getByText("课程资料未同步")).toBeInTheDocument()
    expect(screen.queryByText("示例正文")).not.toBeInTheDocument()
  })
})
