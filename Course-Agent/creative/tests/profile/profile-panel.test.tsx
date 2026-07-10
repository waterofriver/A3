import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { ProfilePanel } from "@/components/profile/profile-panel"

const profile = {
  knowledge_foundation: "入门基础",
  cognitive_style: "案例驱动",
  weak_points: ["ROS2 通信"],
  learning_pace: "分阶段",
  content_preferences: ["图解", "代码案例"],
  short_term_goal: "完成通信强化",
}

describe("ProfilePanel", () => {
  it("renders exactly the six fixed dimensions", () => {
    render(<ProfilePanel profile={profile} />)
    for (const label of [
      "知识基础",
      "认知风格",
      "薄弱知识点",
      "学习节奏",
      "内容偏好",
      "短期学习目标",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })
})
