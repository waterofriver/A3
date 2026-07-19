"use client"

import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react"
import { BookOpen, CheckCircle2, Circle } from "lucide-react"
import { useMemo, useState } from "react"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { LearningPathNode } from "@/lib/api/learning-path-types"

type PathNodeData = {
  resourceId: string | null
  stageName: string
  difficulty: string
  completed: boolean
}

type PathFlowNode = Node<PathNodeData, "pathStage">

function PathStageNode({ data }: NodeProps<PathFlowNode>) {
  const StateIcon = data.completed ? CheckCircle2 : Circle

  return (
    <div className="flex h-full min-w-0 flex-col text-left">
      <Handle className="!h-2 !w-2 !border-2 !border-white !bg-slate-500" position={Position.Left} type="target" />
      <Handle className="!h-2 !w-2 !border-2 !border-white !bg-slate-500" position={Position.Right} type="source" />
      <div className="flex items-start justify-between gap-3">
        <span className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-700">
          {data.difficulty}
        </span>
        <StateIcon
          aria-label={data.completed ? "已完成" : "未完成"}
          className={data.completed ? "h-4 w-4 shrink-0 text-emerald-600" : "h-4 w-4 shrink-0 text-slate-400"}
        />
      </div>
      <p className="mt-4 line-clamp-2 text-base font-bold leading-6 text-slate-900">
        {data.stageName}
      </p>
      <p className={data.completed ? "mt-auto text-xs font-semibold text-emerald-700" : "mt-auto text-xs font-semibold text-slate-600"}>
        {data.completed ? "已完成" : "未完成"}
      </p>
    </div>
  )
}

const nodeTypes = { pathStage: PathStageNode }

const staggeredOffsets = [
  { x: 0, y: 36 },
  { x: 34, y: 0 },
  { x: -18, y: 58 },
  { x: 22, y: 18 },
]

export function buildGraph(nodes: LearningPathNode[]) {
  const orderedNodes = [...nodes].sort((left, right) => left.position - right.position)
  const flowNodes: PathFlowNode[] = orderedNodes.map((node, index) => {
    const offset = staggeredOffsets[index % staggeredOffsets.length]
    const row = Math.floor(index / staggeredOffsets.length)
    const completed = Boolean(node.completed_at)

    return {
      id: node.id,
      type: "pathStage",
      position: {
        x: (index % staggeredOffsets.length) * 292 + offset.x,
        y: row * 208 + offset.y,
      },
      data: {
        resourceId: node.resource_id,
        stageName: node.stage_name,
        difficulty: node.difficulty,
        completed,
      },
      draggable: false,
      selectable: true,
      style: {
        width: 246,
        height: 148,
        border: completed ? "1px solid #86efac" : "1px solid #bfdbfe",
        borderRadius: 8,
        background: completed ? "#f0fdf4" : "#ffffff",
        boxShadow: completed
          ? "0 12px 24px -18px rgba(22, 163, 74, 0.55)"
          : "0 12px 24px -18px rgba(37, 99, 235, 0.45)",
        cursor: "pointer",
        padding: "18px",
      },
    }
  })
  const edges: Edge[] = orderedNodes.slice(1).map((node, index) => ({
    id: `${orderedNodes[index].id}-${node.id}`,
    source: orderedNodes[index].id,
    target: node.id,
    animated: false,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#64748b",
      width: 18,
      height: 18,
    },
    style: { stroke: "#64748b", strokeWidth: 2 },
  }))
  return { flowNodes, edges }
}

function nodeRecommendation(node: PathFlowNode) {
  return node.data.resourceId
    ? "建议先完成绑定资源中的核心练习，再回到学习路径确认掌握情况。"
    : "建议结合前序阶段的内容进行复盘，并用一次练习确认理解。"
}

export function LearningPathGraph({
  nodes,
  onOpenResource,
  onToggleNode,
}: {
  nodes: LearningPathNode[]
  onOpenResource: (resourceId: string) => void
  onToggleNode?: (nodeId: string, stageName: string, completed: boolean) => boolean | Promise<boolean>
}) {
  const { edges, flowNodes } = useMemo(() => buildGraph(nodes), [nodes])
  const [selectedNode, setSelectedNode] = useState<PathFlowNode | null>(null)

  const handleToggle = async () => {
    if (!selectedNode || !onToggleNode) return
    const succeeded = await onToggleNode(
      selectedNode.id,
      selectedNode.data.stageName,
      !selectedNode.data.completed,
    )
    if (succeeded !== false) setSelectedNode(null)
  }

  return (
    <section aria-label="个性化学习路径" className="h-[560px] min-h-[560px] overflow-hidden rounded-lg border border-slate-300 bg-[#f8fbff] shadow-sm">
      <ReactFlow
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        minZoom={0.65}
        nodes={flowNodes}
        nodeTypes={nodeTypes}
        nodesConnectable={false}
        nodesDraggable={false}
        nodesFocusable={false}
        onNodeClick={(_, node) => setSelectedNode(node as PathFlowNode)}
        panOnScroll
        proOptions={{ hideAttribution: true }}
        selectNodesOnDrag={false}
      >
        <Background color="#94a3b8" gap={22} size={1.25} variant={BackgroundVariant.Dots} />
        <Controls position="bottom-right" showInteractive={false} />
      </ReactFlow>

      <Dialog open={Boolean(selectedNode)} onOpenChange={(open) => !open && setSelectedNode(null)}>
        {selectedNode ? (
          <DialogContent className="w-[min(92vw,440px)] rounded-lg border-slate-200 bg-white p-6 shadow-2xl">
            <DialogHeader>
              <div className="flex items-center gap-2 text-xs font-bold text-blue-700">
                <span className="rounded-full border border-blue-200 bg-blue-50 px-2 py-1">{selectedNode.data.difficulty}</span>
                <span className={selectedNode.data.completed ? "text-emerald-700" : "text-slate-500"}>
                  {selectedNode.data.completed ? "已完成" : "未完成"}
                </span>
              </div>
              <DialogTitle className="pt-2 text-xl leading-8 text-slate-950">{selectedNode.data.stageName}</DialogTitle>
              <DialogDescription className="pt-2 leading-6 text-slate-600">
                {nodeRecommendation(selectedNode)}
              </DialogDescription>
            </DialogHeader>
            {selectedNode.data.resourceId ? (
              <button
                className="flex items-center gap-2 text-left text-sm font-semibold text-blue-700 transition-colors hover:text-blue-900"
                onClick={() => onOpenResource(selectedNode.data.resourceId!)}
                type="button"
              >
                <BookOpen aria-hidden="true" className="h-4 w-4" />
                打开绑定资源
              </button>
            ) : null}
            <button
              className={selectedNode.data.completed
                ? "mt-2 h-10 rounded-md border border-emerald-300 bg-emerald-50 px-4 text-sm font-bold text-emerald-800 transition-colors hover:bg-emerald-100"
                : "mt-2 h-10 rounded-md bg-blue-700 px-4 text-sm font-bold text-white transition-colors hover:bg-blue-800"}
              onClick={handleToggle}
              type="button"
            >
              {selectedNode.data.completed ? "已完成" : "未完成"}
            </button>
          </DialogContent>
        ) : null}
      </Dialog>
    </section>
  )
}
