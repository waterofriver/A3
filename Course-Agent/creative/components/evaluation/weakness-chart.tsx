"use client"

import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import type { components } from "@/lib/api/generated"

type WeakPoint = components["schemas"]["EvaluationWeakPoint"]

export function WeaknessChart({ weakPoints }: { weakPoints: WeakPoint[] }) {
  if (!weakPoints.length) {
    return (
      <div className="grid h-[280px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-white text-sm text-slate-400 font-medium shadow-sm">
        暂未识别薄弱知识点
      </div>
    )
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_250px] gap-6 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
      <ChartContainer
        className="h-[280px] w-full aspect-auto"
        config={{ frequency: { label: "出现频次", color: "#3b82f6" } }}
      >
        <BarChart
          accessibilityLayer
          data={weakPoints}
          layout="vertical"
          margin={{ left: 8, right: 18, top: 8, bottom: 8 }}
        >
          <CartesianGrid horizontal={false} stroke="#f1f5f9" />
          <XAxis allowDecimals={false} axisLine={false} tickLine={false} type="number" stroke="#94a3b8" />
          <YAxis dataKey="name" hide type="category" />
          <ChartTooltip content={<ChartTooltipContent hideLabel />} cursor={false} />
          <Bar dataKey="frequency" fill="var(--color-frequency)" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ChartContainer>
      <ol className="divide-y divide-slate-100 border-t border-b border-slate-100" aria-label="薄弱知识点排名">
        {weakPoints.map((point, index) => (
          <li className="flex min-h-14 items-center gap-3 py-3 px-2 rounded-lg transition hover:bg-slate-50/50" key={point.name}>
            <span className="w-5 text-xs font-bold tabular-nums text-slate-400">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="min-w-0 flex-1 text-sm font-bold text-slate-700">
              {point.name}
            </span>
            <span className="text-xs font-bold tabular-nums text-primary">
              {point.frequency} 次
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
