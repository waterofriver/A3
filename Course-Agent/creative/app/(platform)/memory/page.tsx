"use client"

import { useQuery } from "@tanstack/react-query"
import { BrainCircuit } from "lucide-react"
import { useEffect, useState } from "react"

import { MemoryDashboard, type MemoryReport } from "@/components/memory/memory-dashboard"
import { ErrorNotice } from "@/components/shared/error-notice"
import { apiFetch } from "@/lib/api/client"
import type { CourseSummary } from "@/lib/api/resource-types"
import { getRememberedCourse, selectInitialCourse, subscribeToSelectedCourse } from "@/lib/course-selection"
import { getUserId } from "@/lib/session/user-session"

export default function MemoryPage() {
  const userId = getUserId() ?? ""
  const [selectedCourseName, setSelectedCourseName] = useState<string | null>(null)
  const [coursePreferenceHydrated, setCoursePreferenceHydrated] = useState(false)
  useEffect(() => {
    setSelectedCourseName(getRememberedCourse())
    setCoursePreferenceHydrated(true)
    return subscribeToSelectedCourse(setSelectedCourseName)
  }, [])
  const coursesQuery = useQuery({ queryKey: ["courses"], queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"), enabled: Boolean(userId) })
  const course = coursePreferenceHydrated ? selectInitialCourse(coursesQuery.data ?? [], selectedCourseName) : undefined
  const reportQuery = useQuery({ queryKey: ["memory-report", userId, course?.name], queryFn: () => apiFetch<MemoryReport>(`/api/memory/report?user_id=${encodeURIComponent(userId)}&course_name=${encodeURIComponent(course?.name ?? "")}`), enabled: Boolean(userId && coursePreferenceHydrated && course?.name) })
  const error = coursesQuery.error ?? reportQuery.error
  const loading = Boolean(userId && course?.name) && (coursesQuery.isPending || reportQuery.isPending)
  const content = error ? null : !userId ? "请先登录后查看你的记忆地图。" : !coursePreferenceHydrated || coursesQuery.isPending ? "正在读取可用课程" : !course?.name ? "暂时没有可用课程，选择课程后即可生成记忆地图。" : loading ? "正在生成你的记忆地图" : null
  return <div className="mx-auto w-full max-w-[1380px]"><header className="flex flex-col gap-4 border-b pb-5 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm font-medium text-[#2457d6]">MEMORY MAP</p><h1 className="mt-2 text-2xl font-semibold text-[#182132]">学习记忆助手</h1><p className="mt-2 text-sm text-[#526279]">用记忆曲线找到该复习什么，以及应该先补哪一部分基础。</p></div><div className="flex items-center gap-2 text-sm font-medium text-[#526279]"><BrainCircuit aria-hidden="true" className="h-4 w-4 text-[#2457d6]" />{course?.name ?? "等待课程"}</div></header>{error ? <div className="mt-5"><ErrorNotice error={error instanceof Error ? error : "学习记忆报告加载失败。"} onRetry={() => { void coursesQuery.refetch(); void reportQuery.refetch() }} /></div> : null}{content ? <div className="mt-6 grid min-h-80 place-items-center rounded-lg border border-dashed bg-white px-6 text-center text-sm text-slate-500" role={loading || coursesQuery.isPending ? "status" : undefined}>{content}</div> : reportQuery.data ? <MemoryDashboard report={reportQuery.data} /> : !error ? <div className="mt-6 grid min-h-80 place-items-center rounded-lg border border-dashed bg-white px-6 text-center text-sm text-slate-500">完成一次课程练习后，这里会为你生成记忆曲线和复习建议。</div> : null}</div>
}
