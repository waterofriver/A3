import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { LearningPathGraph } from "@/components/learning-path/learning-path-graph"

const nodes = [
  { id: "n1", position: 0, stage_name: "基础补全", difficulty: "基础", resource_id: "r1", completed_at: null },
  { id: "n2", position: 1, stage_name: "知识点学习", difficulty: "进阶", resource_id: "r2", completed_at: null },
  { id: "n3", position: 2, stage_name: "习题训练", difficulty: "巩固", resource_id: "r3", completed_at: null },
  { id: "n4", position: 3, stage_name: "代码实操", difficulty: "实操", resource_id: "r4", completed_at: null },
  { id: "n5", position: 4, stage_name: "拓展视频", difficulty: "拓展", resource_id: "r5", completed_at: null },
]

describe("LearningPathGraph", () => {
  it("renders five nodes and opens bound resources", () => {
    const onOpenResource = vi.fn()
    render(<LearningPathGraph nodes={nodes} onOpenResource={onOpenResource} />)

    for (const node of nodes) {
      expect(screen.getByText(node.stage_name)).toBeInTheDocument()
    }
    fireEvent.click(screen.getByText("习题训练"))
    expect(onOpenResource).toHaveBeenCalledWith("r3")
  })
})
