"use client"

import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react"
import { useMemo } from "react"

import type { MindMapNode } from "@/lib/api/resource-types"

function layoutMindMap(nodes: MindMapNode[]) {
  const nodeById = new Map(nodes.map((node) => [node.id, node]))
  const depthById = new Map<string, number>()

  const getDepth = (node: MindMapNode, trail = new Set<string>()): number => {
    const cached = depthById.get(node.id)
    if (cached !== undefined) return cached
    if (!node.parent_id || trail.has(node.id)) return 0
    const parent = nodeById.get(node.parent_id)
    if (!parent) return 0
    const nextTrail = new Set(trail)
    nextTrail.add(node.id)
    const depth = Math.min(8, getDepth(parent, nextTrail) + 1)
    depthById.set(node.id, depth)
    return depth
  }

  const siblings = new Map<number, number>()
  const flowNodes: Node[] = nodes.map((node) => {
    const depth = getDepth(node)
    const siblingIndex = siblings.get(depth) ?? 0
    siblings.set(depth, siblingIndex + 1)
    return {
      id: node.id,
      data: { label: node.label },
      position: { x: depth * 240, y: siblingIndex * 104 },
      draggable: false,
      selectable: true,
      style: {
        width: 176,
        minHeight: 52,
        border: depth === 0 ? "1px solid #2457d6" : "1px solid #cbd6e5",
        borderRadius: 6,
        background: depth === 0 ? "#17243d" : "#ffffff",
        color: depth === 0 ? "#ffffff" : "#344158",
        fontSize: 13,
        fontWeight: 600,
        padding: "12px 14px",
      },
    }
  })
  const flowEdges: Edge[] = nodes
    .filter((node) => node.parent_id && nodeById.has(node.parent_id))
    .map((node) => ({
      id: `${node.parent_id}-${node.id}`,
      source: node.parent_id as string,
      target: node.id,
      animated: false,
      style: { stroke: "#9aabc2", strokeWidth: 1.5 },
    }))

  return { flowNodes, flowEdges }
}

export function MindMapViewer({ nodes }: { nodes: MindMapNode[] }) {
  const { flowEdges, flowNodes } = useMemo(() => layoutMindMap(nodes), [nodes])

  return (
    <div
      aria-label="思维导图"
      className="h-[420px] min-h-[420px] w-full overflow-hidden border bg-[#f7f9fc]"
    >
      <ReactFlow
        edges={flowEdges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodes={flowNodes}
        nodesConnectable={false}
        nodesDraggable={false}
        nodesFocusable={false}
        panOnScroll
        proOptions={{ hideAttribution: true }}
        selectNodesOnDrag={false}
      >
        <Background color="#d7dfeb" gap={20} size={1} variant={BackgroundVariant.Dots} />
        <Controls position="bottom-right" showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
