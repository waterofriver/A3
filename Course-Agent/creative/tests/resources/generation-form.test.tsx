import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { GenerationForm } from "@/components/resources/generation-form"

const demoCourse = {
  name: "机器人操作系统（演示）",
  slug: "robotics",
  content_ready: false,
  is_demo: true,
}

describe("GenerationForm", () => {
  it("submits stable resource enum values", async () => {
    const user = userEvent.setup()
    const onGenerate = vi.fn()
    render(<GenerationForm courses={[demoCourse]} onGenerate={onGenerate} />)

    await user.selectOptions(screen.getByLabelText("课程"), "robotics")
    await user.type(screen.getByLabelText("薄弱知识点"), "ROS2 通信")
    await user.click(screen.getByLabelText("讲义文档"))
    await user.click(screen.getByLabelText("习题题库"))
    await user.click(screen.getByRole("button", { name: "生成学习资源" }))

    expect(onGenerate).toHaveBeenCalledWith(
      expect.objectContaining({
        course_name: "机器人操作系统（演示）",
        resource_type_list: ["handout", "quiz"],
        weak_point: "ROS2 通信",
      }),
    )
  })

  it("selects all five resource types with one command", async () => {
    const user = userEvent.setup()
    const onGenerate = vi.fn()
    render(<GenerationForm courses={[demoCourse]} onGenerate={onGenerate} />)

    await user.click(screen.getByRole("button", { name: "全选资源" }))
    await user.click(screen.getByRole("button", { name: "生成学习资源" }))

    expect(onGenerate.mock.calls[0][0].resource_type_list).toEqual([
      "handout",
      "mindmap",
      "quiz",
      "code",
      "video",
    ])
  })
})
