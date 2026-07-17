"use client"

import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react"
import { useMemo } from "react"

import type { LearningPathNode } from "@/lib/api/learning-path-types"

type PathNodeData = {
  resourceId: string | null
  stageName: string
  difficulty: string
  completed: boolean
}

type PathFlowNode = Node<PathNodeData, "pathStage">

function PathStageNode({ data }: NodeProps<PathFlowNode>) {
  return (
    <div className="text-left py-1">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-bold leading-none tracking-tight">{data.stageName}</span>
        <span className="rounded-full bg-blue-50 border border-blue-100/50 px-1.5 py-0.5 text-[9px] font-bold text-blue-600 shrink-0">
          {data.difficulty}
        </span>
      </div>
      <p className="mt-4 text-[9px] font-bold tracking-wider uppercase text-slate-400">
        {data.completed
          ? "✅ 阶段已完成"
          : data.resourceId
            ? "🔗 打开绑定资源"
            : "👆 点击标记完成"}
      </p>
    </div>
  )
}

const nodeTypes = { pathStage: PathStageNode }

function buildGraph(nodes: LearningPathNode[]) {
  const flowNodes: PathFlowNode[] = nodes.map((node) => {
    const isCompleted = Boolean(node.completed_at)
    const hasResource = Boolean(node.resource_id)
    
    // Premium theme variables mapped inline for ReactFlow inline node style
    let border = "1px dashed #e2e8f0"
    let background = "#f8fafc"
    let color = "#64748b"
    let shadow = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    
    if (isCompleted) {
      border = "1px solid #bbf7d0"
      background = "#f0fdf4"
      color = "#166534"
      shadow = "0 4px 6px -1px rgba(240, 253, 244, 0.5), 0 2px 4px -2px rgba(240, 253, 244, 0.5)"
    } else if (hasResource) {
      border = "1px solid #bfdbfe"
      background = "#ffffff"
      color = "#1e40af"
      shadow = "0 4px 6px -1px rgba(59, 130, 246, 0.05), 0 2px 4px -2px rgba(59, 130, 246, 0.05)"
    }

    return {
      id: node.id,
      type: "pathStage",
      position: { x: node.position * 236, y: 132 },
      data: {
        resourceId: node.resource_id,
        stageName: node.stage_name,
        difficulty: node.difficulty,
        completed: isCompleted,
      },
      draggable: false,
      selectable: true,
      style: {
        width: 196,
        minHeight: 96,
        border,
        borderRadius: 12,
        background,
        color,
        boxShadow: shadow,
        cursor: "pointer",
        fontSize: 12,
        fontWeight: 600,
        padding: "14px 16px",
      },
    }
  })
  const edges: Edge[] = nodes.slice(1).map((node, index) => ({
    id: `${nodes[index].id}-${node.id}`,
    source: nodes[index].id,
    target: node.id,
    style: { stroke: "#cbd5e1", strokeWidth: 2 },
  }))
  return { flowNodes, edges }
}

export function LearningPathGraph({
  nodes,
  onOpenResource,
  onCompleteNode,
}: {
  nodes: LearningPathNode[]
  onOpenResource: (resourceId: string) => void
  onCompleteNode?: (nodeId: string, stageName: string) => void
}) {
  const { edges, flowNodes } = useMemo(() => buildGraph(nodes), [nodes])

  return (
    <section aria-label="个性化学习路径" className="h-[400px] min-h-[400px] rounded-2xl border border-slate-200 bg-slate-50/50 shadow-sm overflow-hidden">
      <ReactFlow
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.16 }}
        nodes={flowNodes}
        nodeTypes={nodeTypes}
        nodesConnectable={false}
        nodesDraggable={false}
        nodesFocusable={false}
        onNodeClick={(_, node) => {
          if (node.data.resourceId) {
            onOpenResource(node.data.resourceId)
          } else if (onCompleteNode) {
            onCompleteNode(node.id, node.data.stageName)
          }
        }}
        panOnScroll
        proOptions={{ hideAttribution: true }}
        selectNodesOnDrag={false}
      >
        <Background color="#cbd5e1" gap={20} size={1} variant={BackgroundVariant.Dots} />
        <Controls position="bottom-right" showInteractive={false} />
      </ReactFlow>
    </section>
  )
}
