"use client"

import { BrainCircuit, CircleAlert, Clock3, PencilLine, RefreshCw, Sparkles, Target } from "lucide-react"
import { useState } from "react"
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { components } from "@/lib/api/generated"

export type MemoryReport = components["schemas"]["MemoryReportData"]

const riskStyle = {
  stable: { label: "状态稳定", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  review_soon: { label: "建议复习", className: "border-amber-200 bg-amber-50 text-amber-700" },
  urgent: { label: "优先复习", className: "border-rose-200 bg-rose-50 text-rose-700" },
}

const actionLabel = { recall: "回忆要点", quiz: "完成测验", practice: "动手练习" }

export function MemoryDashboard({ report }: { report: MemoryReport }) {
  const [selectedId, setSelectedId] = useState(report.knowledge_points[0]?.id ?? "")
  const selected = report.knowledge_points.find((point) => point.id === selectedId) ?? report.knowledge_points[0]

  if (!selected) return <Card className="mt-6 border-dashed shadow-none"><CardContent className="grid min-h-72 place-items-center text-center"><div><BrainCircuit aria-hidden="true" className="mx-auto h-8 w-8 text-slate-400" /><h2 className="mt-3 text-base font-semibold text-slate-800">还没有记忆数据</h2><p className="mt-1 text-sm text-slate-500">完成一次练习或复习后，这里会生成你的记忆变化和复习建议。</p></div></CardContent></Card>

  const risk = riskStyle[selected.risk_level]
  const actions = report.today_actions.slice(0, 3)
  return <div className="mt-6 space-y-5">
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card className="border-slate-200 shadow-sm"><CardContent className="flex min-h-44 flex-col justify-between p-5 sm:flex-row sm:items-center sm:gap-8"><div className="flex items-center gap-4"><div className="grid h-20 w-20 shrink-0 place-items-center rounded-full border-8 border-blue-100 bg-blue-50 text-2xl font-bold tabular-nums text-blue-700">{Math.round(report.memory_health)}</div><div><p className="text-sm font-semibold text-slate-500">总体记忆健康分</p><p className="mt-2 max-w-xl text-sm leading-6 text-slate-700">{report.summary}</p></div></div><div className="mt-4 flex items-center gap-2 text-xs text-slate-500 sm:mt-0"><Sparkles aria-hidden="true" className="h-4 w-4 text-amber-500" />{report.has_personal_evidence ? "按当前学习记录动态更新" : "等待你的学习记录校正"}</div></CardContent></Card>
      <Card className="border-slate-200 shadow-sm"><CardHeader className="pb-2"><CardTitle className="text-sm font-semibold text-slate-800">当前优先处理</CardTitle></CardHeader><CardContent className="flex items-center gap-3 pb-5"><CircleAlert aria-hidden="true" className="h-8 w-8 shrink-0 text-rose-500" /><div className="min-w-0"><p className="truncate font-semibold text-slate-800">{selected.name}</p><p className="mt-1 text-sm text-slate-500">现在保持度 {selected.retention}%</p></div></CardContent></Card>
    </section>
    <section className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.85fr)]">
      <Card className="min-w-0 border-slate-200 shadow-sm"><CardHeader className="gap-3 pb-2 sm:flex-row sm:items-start sm:justify-between"><div><CardTitle className="text-base font-semibold text-slate-800">预计记忆保持度</CardTitle><p className="mt-1 text-sm text-slate-500">根据学习、练习和复习记录估计，帮助你抓住复习窗口。</p></div><Badge className={risk.className} variant="outline">{risk.label}</Badge></CardHeader><CardContent className="pb-5"><div aria-label="选择知识点" className="mb-4 flex gap-2 overflow-x-auto pb-1">{report.knowledge_points.map((point) => <Button aria-pressed={point.id === selected.id} className="shrink-0" key={point.id} onClick={() => setSelectedId(point.id)} size="sm" type="button" variant={point.id === selected.id ? "default" : "outline"}>{point.name}</Button>)}</div><div aria-label={`${selected.name}的预计记忆保持度曲线`} className="h-64 min-w-0" role="img"><ResponsiveContainer height="100%" width="100%"><LineChart data={selected.curve} margin={{ top: 10, right: 12, bottom: 2, left: -18 }}><CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" fontSize={12} stroke="#64748b" tickFormatter={(day) => `第 ${day} 天`} tickLine={false} /><YAxis domain={[0, 100]} fontSize={12} stroke="#64748b" tickFormatter={(value) => `${value}%`} tickLine={false} /><Tooltip formatter={(value) => [`${value}%`, "预计保持度"]} labelFormatter={(day) => `学习后第 ${day} 天`} /><Line dataKey="retention" dot={{ fill: "#2563eb", r: 4 }} name="预计保持度" stroke="#2563eb" strokeWidth={3} type="monotone" /></LineChart></ResponsiveContainer></div><div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-slate-100 pt-3 text-xs text-slate-500"><span>初始掌握度 {selected.base_mastery}%</span><span>距上次复习 {selected.days_since_review} 天</span><span className="font-medium text-slate-700">{selected.recommendation}</span></div></CardContent></Card>
      <Card className="border-slate-200 shadow-sm"><CardHeader className="pb-2"><CardTitle className="flex items-center gap-2 text-base font-semibold text-slate-800"><Target aria-hidden="true" className="h-4 w-4 text-blue-600" />先补什么</CardTitle></CardHeader><CardContent className="pb-5">{selected.blockage ? <div className="rounded-lg border border-amber-100 bg-amber-50/60 p-4"><p className="text-xs font-medium text-amber-700">先巩固基础，再回到 {selected.name}</p><p className="mt-2 font-semibold text-slate-800">{selected.blockage.name}</p><p className="mt-2 text-sm leading-6 text-slate-600">{selected.blockage.reason}</p></div> : <div className="rounded-lg border border-emerald-100 bg-emerald-50/60 p-4 text-sm leading-6 text-emerald-800">基础知识较稳，可以直接复习这个知识点。</div>}<div className="mt-4 flex items-center gap-2 text-xs text-slate-500"><RefreshCw aria-hidden="true" className="h-3.5 w-3.5" />复测后会重新安排下一步</div></CardContent></Card>
    </section>
    <Card className="border-slate-200 shadow-sm"><CardHeader className="pb-2"><h2 className="text-base font-semibold text-slate-800">今日复习建议</h2><p className="text-sm text-slate-500">短时、明确的任务，完成后可让记忆曲线回升。</p></CardHeader><CardContent className="pb-5">{actions.length ? <div className="grid gap-3 md:grid-cols-3">{actions.map((action) => <div className="flex min-w-0 flex-col rounded-lg border border-slate-200 bg-slate-50/50 p-4" key={`${action.knowledge_point_id}-${action.action_type}`}><div className="flex items-center justify-between gap-3"><Badge className="border-blue-100 bg-blue-50 text-blue-700" variant="outline">{actionLabel[action.action_type]}</Badge><span className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-slate-500"><Clock3 aria-hidden="true" className="h-3.5 w-3.5" />{action.minutes} 分钟</span></div><p className="mt-3 font-semibold leading-6 text-slate-800">{action.title}</p><p className="mt-2 text-sm leading-6 text-slate-500">{action.reason}</p></div>)}</div> : <div className="flex min-h-28 items-center gap-3 rounded-lg border border-dashed border-slate-200 px-4 text-sm text-slate-500"><PencilLine aria-hidden="true" className="h-5 w-5 text-slate-400" />今天暂时没有需要优先处理的复习任务。</div>}</CardContent></Card>
  </div>
}
