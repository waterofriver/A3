import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import { MindMapViewer } from "@/components/resources/mind-map-viewer"

describe("MindMapViewer", () => {
  it("renders every mind map node", () => {
    render(
      <MindMapViewer
        nodes={[
          { id: "root", label: "ROS2", parent_id: null },
          { id: "topic", label: "节点通信", parent_id: "root" },
        ]}
      />,
    )

    expect(screen.getByText("ROS2")).toBeInTheDocument()
    expect(screen.getByText("节点通信")).toBeInTheDocument()
  })
})
