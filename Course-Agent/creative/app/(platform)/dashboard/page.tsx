"use client"

import { useQuery } from "@tanstack/react-query"
import { LoaderCircle, Share2 } from "lucide-react"

import { DagGraph } from "@/components/dashboard/dag-graph"
import { DashboardContent, type DashboardData } from "@/components/dashboard/dashboard-content"
import { ErrorNotice } from "@/components/shared/error-notice"
import { apiFetch } from "@/lib/api/client"
import { getUserId } from "@/lib/session/user-session"

// DAG 节点类型（与后端 /api/knowledge/dag 对齐）
type DagNodeData = {
  kp_id: string
  kp_name: string
  difficulty: number
  category: string
  prerequisites: string[]
  status: "untouched" | "learning" | "weak" | "mastered"
}

export default function DashboardPage() {
  const userId = getUserId() ?? ""

  const dashboardQuery = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () =>
      apiFetch<DashboardData>(
        `/api/dashboard?user_id=${encodeURIComponent(userId)}`,
      ),
    enabled: Boolean(userId),
  })

  const dagQuery = useQuery({
    queryKey: ["dag-status", userId],
    queryFn: () =>
      apiFetch<DagNodeData[]>(
        `/api/knowledge/dag?user_id=${encodeURIComponent(userId)}`,
      ),
    enabled: Boolean(userId),
  })

  const error = dashboardQuery.error ?? dagQuery.error
  const isPending =
    (dashboardQuery.isPending || dagQuery.isPending) && !error

  return (
    <div>
      {error ? (
        <div className="mb-6">
          <ErrorNotice
            error={error as Error}
            onRetry={() => {
              void dashboardQuery.refetch()
              void dagQuery.refetch()
            }}
          />
        </div>
      ) : null}

      {isPending ? (
        <div className="grid min-h-[520px] place-items-center" role="status">
          <span className="flex items-center gap-3 text-sm text-[#718096]">
            <LoaderCircle aria-hidden className="h-5 w-5 animate-spin" />
            正在加载学习仪表盘
          </span>
        </div>
      ) : (
        <div className="space-y-6">
          {dashboardQuery.data ? (
            <DashboardContent data={dashboardQuery.data} />
          ) : null}

          {/* ── 知识点 DAG 着色图 ── */}
          <section className="rounded-lg border bg-white p-5">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#edf3ff] text-[#2457d6]">
                  <Share2 aria-hidden className="h-3.5 w-3.5" />
                </span>
                <h2 className="text-sm font-semibold text-[#27344a]">
                  知识体系掌握总览
                </h2>
              </div>
            </div>
            <DagGraph data={dagQuery.data} isLoading={dagQuery.isPending} />
          </section>
        </div>
      )}
    </div>
  )
}
