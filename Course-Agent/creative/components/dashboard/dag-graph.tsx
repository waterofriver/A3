"use client"

import {
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  type Node,
  ReactFlow,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import {
  CheckCircle2,
  Circle,
  CircleDot,
  LoaderCircle,
  ShieldAlert,
} from "lucide-react"
import { useCallback, useMemo } from "react"

// ── 类型 ──

type DagNodeData = {
  kp_id: string
  kp_name: string
  difficulty: number
  category: string
  prerequisites: string[]
  status: "untouched" | "learning" | "weak" | "mastered"
}

// ── 位置计算：拓扑分层 ──

function computeLayout(nodes: DagNodeData[]) {
  const kpMap = new Map(nodes.map((n) => [n.kp_id, n]))

  // 计算每个节点的深度（最长前置链长度）
  function depth(kpId: string, memo: Map<string, number>): number {
    if (memo.has(kpId)) return memo.get(kpId)!
    const kp = kpMap.get(kpId)
    if (!kp || kp.prerequisites.length === 0) {
      memo.set(kpId, 0)
      return 0
    }
    const maxPrereq = Math.max(
      ...kp.prerequisites.map((pid) => depth(pid, memo)),
    )
    const d = maxPrereq + 1
    memo.set(kpId, d)
    return d
  }

  const memo = new Map<string, number>()
  nodes.forEach((n) => depth(n.kp_id, memo))

  // 按层分组
  const layers = new Map<number, DagNodeData[]>()
  for (const n of nodes) {
    const d = memo.get(n.kp_id) ?? 0
    if (!layers.has(d)) layers.set(d, [])
    layers.get(d)!.push(n)
  }

  const layerXs: Record<number, number> = {}
  let x = 0
  const sorted = [...layers.keys()].sort((a, b) => a - b)
  for (const layer of sorted) {
    layerXs[layer] = x
    x += 300
  }

  // 节点位置
  const H_SPACING = 140
  const positions: Record<string, { x: number; y: number }> = {}
  for (const [layer, kps] of layers) {
    const totalHeight = (kps.length - 1) * H_SPACING
    kps.forEach((kp, i) => {
      positions[kp.kp_id] = {
        x: layerXs[layer],
        y: i * H_SPACING - totalHeight / 2,
      }
    })
  }

  return { positions, layers, memo }
}

// ── 状态 → 颜色映射 ──

const STATUS_STYLE: Record<
  string,
  { bg: string; border: string; icon: React.ReactNode }
> = {
  mastered: {
    bg: "#eef6da",
    border: "#55741f",
    icon: <CheckCircle2 className="h-4 w-4 text-[#55741f]" />,
  },
  learning: {
    bg: "#edf3ff",
    border: "#2457d6",
    icon: <CircleDot className="h-4 w-4 text-[#2457d6]" />,
  },
  weak: {
    bg: "#fef2ed",
    border: "#bd4d43",
    icon: <ShieldAlert className="h-4 w-4 text-[#bd4d43]" />,
  },
  untouched: {
    bg: "#f5f6f8",
    border: "#cdd6e3",
    icon: <Circle className="h-4 w-4 text-[#98a3b3]" />,
  },
}

function DagNode({ data }: { data: DagNodeData }) {
  const style = STATUS_STYLE[data.status] ?? STATUS_STYLE.untouched
  const difficulty = "●".repeat(data.difficulty) + "○".repeat(5 - data.difficulty)

  return (
    <div
      className="flex min-w-[200px] max-w-[220px] flex-col gap-1 rounded-lg border-2 bg-white p-3 shadow-sm"
      style={{ borderColor: style.border }}
    >
      <div className="flex items-start gap-2">
        <span className="mt-0.5 shrink-0">{style.icon}</span>
        <span className="text-sm font-semibold text-[#182132] leading-snug">
          {data.kp_name}
        </span>
      </div>
      <div className="flex items-center gap-2 text-[11px] text-[#7a8799]">
        <span>{data.category}</span>
        <span className="text-[10px] tracking-widest">{difficulty}</span>
      </div>
    </div>
  )
}

// ── Legend ──

function Legend() {
  const items = [
    { status: "mastered", label: "已掌握" },
    { status: "learning", label: "学习中" },
    { status: "weak", label: "薄弱点" },
    { status: "untouched", label: "未开始" },
  ] as const
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs">
      {items.map((item) => {
        const style = STATUS_STYLE[item.status]
        return (
          <span className="flex items-center gap-1.5" key={item.status}>
            <span
              className="inline-block h-3 w-3 rounded-sm border"
              style={{ backgroundColor: style.bg, borderColor: style.border }}
            />
            {item.label}
          </span>
        )
      })}
    </div>
  )
}

// ── 主组件 ──

export function DagGraph({
  data,
  isLoading,
}: {
  data: DagNodeData[] | undefined
  isLoading: boolean
}) {
  const { reactFlowNodes, reactFlowEdges, graphHeight } = useMemo(() => {
    if (!data || data.length === 0) {
      return { reactFlowNodes: [], reactFlowEdges: [], graphHeight: 400 }
    }

    const { positions, memo } = computeLayout(data)

    const rfn: Node[] = data.map((kp) => ({
      id: kp.kp_id,
      type: "default",
      position: positions[kp.kp_id] ?? { x: 0, y: 0 },
      data: kp,
    }))

    const rfe: Edge[] = []
    for (const kp of data) {
      for (const pid of kp.prerequisites) {
        rfe.push({
          id: `${pid}->${kp.kp_id}`,
          source: pid,
          target: kp.kp_id,
          type: "smoothstep",
          animated: kp.status === "learning",
          style: {
            stroke: kp.status === "learning" ? "#2457d6" : "#cdd6e3",
            strokeWidth: 2,
          },
        })
      }
    }

    const maxLayer = Math.max(...Object.values(memo))
    const maxY = Math.max(...Object.values(positions).map((p) => Math.abs(p.y)))
    const graphHeight = Math.max(520, maxY * 2 + 140)

    return { reactFlowNodes: rfn, reactFlowEdges: rfe, graphHeight }
  }, [data])

  const nodeTypes = useMemo(() => ({ default: DagNode }), [])

  const defaultViewport = useMemo(
    () => ({ x: 30, y: graphHeight / 2 - 250, zoom: 0.9 }),
    [graphHeight],
  )

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center border bg-white text-sm text-[#718096]" role="status">
        <LoaderCircle aria-hidden className="mr-2 h-4 w-4 animate-spin" />
        正在加载知识点图谱
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center border bg-white text-sm text-[#98a3b3]">
        暂无知识点数据
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <Legend />
        <span className="text-xs text-[#98a3b3]">
          拖拽/滚轮缩放 · {data.length} 个知识点
        </span>
      </div>
      <div
        className="overflow-hidden rounded-lg border bg-white"
        style={{ height: graphHeight }}
      >
        <ReactFlow
          defaultViewport={defaultViewport}
          edges={reactFlowEdges}
          fitView={false}
          nodeTypes={nodeTypes}
          nodes={reactFlowNodes}
          nodesDraggable={false}
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#eef2f6" gap={20} variant={BackgroundVariant.Dots} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  )
}
