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
    <div className="text-left">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm font-semibold">{data.stageName}</span>
        <span className="rounded bg-[#edf3ff] px-1.5 py-0.5 text-[10px] font-semibold text-[#2457d6]">
          {data.difficulty}
        </span>
      </div>
      <p className="mt-3 text-[11px] font-normal text-[#718096]">
        {data.completed
          ? "阶段已完成"
          : data.resourceId
            ? "打开绑定资源"
            : "暂无绑定资源"}
      </p>
    </div>
  )
}

const nodeTypes = { pathStage: PathStageNode }

function buildGraph(nodes: LearningPathNode[]) {
  const flowNodes: PathFlowNode[] = nodes.map((node) => ({
    id: node.id,
    type: "pathStage",
    position: { x: node.position * 236, y: 132 },
    data: {
      resourceId: node.resource_id,
      stageName: node.stage_name,
      difficulty: node.difficulty,
      completed: Boolean(node.completed_at),
    },
    draggable: false,
    selectable: Boolean(node.resource_id),
    style: {
      width: 196,
      minHeight: 96,
      border: node.resource_id ? "1px solid #8ca8dc" : "1px dashed #c8d2df",
      borderRadius: 6,
      background: node.completed_at ? "#f3f9e9" : "#ffffff",
      color: node.resource_id ? "#27344a" : "#8a96a8",
      cursor: node.resource_id ? "pointer" : "not-allowed",
      fontSize: 13,
      fontWeight: 600,
      padding: "14px",
    },
  }))
  const edges: Edge[] = nodes.slice(1).map((node, index) => ({
    id: `${nodes[index].id}-${node.id}`,
    source: nodes[index].id,
    target: node.id,
    style: { stroke: "#91a6c5", strokeWidth: 1.5 },
  }))
  return { flowNodes, edges }
}

export function LearningPathGraph({
  nodes,
  onOpenResource,
}: {
  nodes: LearningPathNode[]
  onOpenResource: (resourceId: string) => void
}) {
  const { edges, flowNodes } = useMemo(() => buildGraph(nodes), [nodes])

  return (
    <section aria-label="个性化学习路径" className="h-[400px] min-h-[400px] border bg-[#f7f9fc]">
      <ReactFlow
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.16 }}
        nodes={flowNodes}
        nodeTypes={nodeTypes}
        nodesConnectable={false}
        nodesDraggable={false}
        onNodeClick={(_, node) => {
          const resourceId = node.data.resourceId
          if (resourceId) onOpenResource(resourceId)
        }}
        panOnScroll
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#d8e1ee" gap={20} size={1} variant={BackgroundVariant.Dots} />
        <Controls position="bottom-right" showInteractive={false} />
      </ReactFlow>
    </section>
  )
}
