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
      <div className="grid h-[280px] place-items-center border border-dashed bg-white text-sm text-[#748196]">
        暂未识别薄弱知识点
      </div>
    )
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)_250px] gap-6">
      <ChartContainer
        className="h-[280px] w-full aspect-auto"
        config={{ frequency: { label: "出现频次", color: "#c9e84d" } }}
      >
        <BarChart
          accessibilityLayer
          data={weakPoints}
          layout="vertical"
          margin={{ left: 8, right: 18, top: 8, bottom: 8 }}
        >
          <CartesianGrid horizontal={false} stroke="#e4e9f1" />
          <XAxis allowDecimals={false} axisLine={false} tickLine={false} type="number" />
          <YAxis dataKey="name" hide type="category" />
          <ChartTooltip content={<ChartTooltipContent hideLabel />} cursor={false} />
          <Bar dataKey="frequency" fill="var(--color-frequency)" radius={[0, 3, 3, 0]} />
        </BarChart>
      </ChartContainer>
      <ol className="divide-y border-y" aria-label="薄弱知识点排名">
        {weakPoints.map((point, index) => (
          <li className="flex min-h-14 items-center gap-3 py-3" key={point.name}>
            <span className="w-5 text-xs font-semibold tabular-nums text-[#8b98aa]">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="min-w-0 flex-1 text-sm font-medium text-[#344258]">
              {point.name}
            </span>
            <span className="text-xs font-semibold tabular-nums text-[#2457d6]">
              {point.frequency} 次
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
