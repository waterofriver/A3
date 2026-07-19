import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { buildGraph, LearningPathGraph } from "@/components/learning-path/learning-path-graph"

const nodes = [
  { id: "n1", position: 0, stage_name: "基础补全", difficulty: "基础", resource_id: "r1", completed_at: null },
  { id: "n2", position: 1, stage_name: "知识点学习", difficulty: "进阶", resource_id: "r2", completed_at: null },
  { id: "n3", position: 2, stage_name: "习题训练", difficulty: "巩固", resource_id: "r3", completed_at: null },
  { id: "n4", position: 3, stage_name: "代码实操", difficulty: "实操", resource_id: "r4", completed_at: null },
  { id: "n5", position: 4, stage_name: "拓展视频", difficulty: "拓展", resource_id: "r5", completed_at: null },
]

describe("LearningPathGraph", () => {
  it("opens a selected node in a detail dialog", () => {
    const onOpenResource = vi.fn()
    render(<LearningPathGraph nodes={nodes} onOpenResource={onOpenResource} />)

    for (const node of nodes) {
      expect(screen.getByText(node.stage_name)).toBeInTheDocument()
    }
    fireEvent.click(screen.getByText("习题训练"))
    expect(screen.getByRole("dialog")).toHaveTextContent("习题训练")
    expect(onOpenResource).not.toHaveBeenCalled()
  })

  it("toggles an incomplete node to complete from its detail dialog", () => {
    const onToggleNode = vi.fn()
    render(
      <LearningPathGraph
        nodes={nodes}
        onOpenResource={vi.fn()}
        onToggleNode={onToggleNode}
      />,
    )

    fireEvent.click(screen.getByText("基础补全"))
    fireEvent.click(screen.getByRole("button", { name: "未完成" }))

    expect(onToggleNode).toHaveBeenCalledWith("n1", "基础补全", true)
  })

  it("toggles a completed node to incomplete from its detail dialog", () => {
    const onToggleNode = vi.fn()
    render(
      <LearningPathGraph
        nodes={[{ ...nodes[0], completed_at: "2026-07-19T08:00:00Z" }]}
        onOpenResource={vi.fn()}
        onToggleNode={onToggleNode}
      />,
    )

    fireEvent.click(screen.getByText("基础补全"))
    fireEvent.click(screen.getByRole("button", { name: "已完成" }))

    expect(onToggleNode).toHaveBeenCalledWith("n1", "基础补全", false)
  })

  it("clamps long stage titles inside a stable-height node", () => {
    const longTitle = "包含足够多文字的学习阶段标题，用于验证路径节点不会被压缩成难以阅读的窄列"
    render(
      <LearningPathGraph
        nodes={[{ ...nodes[0], stage_name: longTitle }]}
        onOpenResource={vi.fn()}
      />,
    )

    expect(screen.getByText(longTitle)).toHaveClass("line-clamp-2")
    expect(screen.getByText(longTitle).closest(".react-flow__node")).toHaveStyle({ height: "148px" })
  })

  it("keeps nodes wide while the second row follows the staggered path", () => {
    render(
      <LearningPathGraph
        nodes={[...nodes, { ...nodes[0], id: "n6", position: 5 }]}
        onOpenResource={vi.fn()}
      />,
    )

    expect(document.querySelector('.react-flow__node[data-id="n1"]')).toHaveStyle({ width: "246px" })
    expect(document.querySelector('.react-flow__node[data-id="n6"]')).toHaveStyle({ transform: "translate(326px,208px)" })
  })

  it("connects consecutive nodes with directional arrows in position order", () => {
    const { edges } = buildGraph([nodes[2], nodes[0], nodes[1]])

    expect(edges).toHaveLength(2)
    expect(edges).toEqual(expect.arrayContaining([
      expect.objectContaining({ source: "n1", target: "n2", markerEnd: expect.objectContaining({ type: "arrowclosed" }) }),
      expect.objectContaining({ source: "n2", target: "n3", markerEnd: expect.objectContaining({ type: "arrowclosed" }) }),
    ]))
  })
})
