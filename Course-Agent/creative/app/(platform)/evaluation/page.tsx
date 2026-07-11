"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { BarChart3 } from "lucide-react"
import { useState } from "react"

import { EvaluationPageContent } from "@/components/evaluation/evaluation-page-content"
import { ErrorNotice } from "@/components/shared/error-notice"
import { ApiError, apiFetch } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"
import type { CourseSummary } from "@/lib/api/resource-types"
import { queryKeys } from "@/lib/query/keys"
import { getUserId } from "@/lib/session/user-session"

type EvaluationReport = components["schemas"]["EvaluationReportData"]
type LearningPath = components["schemas"]["LearningPathData"]

export default function EvaluationPage() {
  const queryClient = useQueryClient()
  const userId = getUserId() ?? ""
  const [appliedVersion, setAppliedVersion] = useState<number>()
  const coursesQuery = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"),
  })
  const course = coursesQuery.data?.[0]
  const reportQuery = useQuery({
    queryKey: queryKeys.evaluation(userId, course?.name ?? ""),
    queryFn: () =>
      apiFetch<EvaluationReport>(
        `/api/eval/report?user_id=${encodeURIComponent(userId)}&course_name=${encodeURIComponent(course?.name ?? "")}`,
      ),
    enabled: Boolean(userId && course?.name),
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.code === "EVALUATION_NOT_READY") &&
      failureCount < 2,
  })
  const applyMutation = useMutation({
    mutationFn: (reportId: string) =>
      apiFetch<LearningPath>("/api/eval/apply", {
        method: "POST",
        body: JSON.stringify({ report_id: reportId }),
      }),
    onSuccess: (path) => {
      setAppliedVersion(path.version)
      void queryClient.invalidateQueries({
        queryKey: queryKeys.evaluation(userId, course?.name ?? ""),
      })
      void queryClient.invalidateQueries({
        queryKey: queryKeys.path(userId, course?.name ?? ""),
      })
    },
  })

  const reportError = reportQuery.error
  const notReady =
    reportError instanceof ApiError && reportError.code === "EVALUATION_NOT_READY"
  const displayedError =
    coursesQuery.error ?? (notReady ? null : reportError) ?? applyMutation.error

  return (
    <div className="mx-auto w-full max-w-[1380px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">LEARNING EVALUATION</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">学习效果评估</h1>
        </div>
        <div className="flex items-center gap-2 text-sm font-medium text-[#526279]">
          <BarChart3 aria-hidden="true" className="h-4 w-4 text-[#2457d6]" />
          {course?.name ?? "等待课程"}
        </div>
      </header>

      {displayedError ? (
        <div className="mt-5">
          <ErrorNotice
            error={displayedError instanceof Error ? displayedError : "评估报告加载失败。"}
            onRetry={() => {
              void coursesQuery.refetch()
              void reportQuery.refetch()
            }}
          />
        </div>
      ) : null}

      {coursesQuery.isPending || reportQuery.isPending ? (
        <div className="mt-6 grid h-[440px] place-items-center border bg-white text-sm text-[#718096]" role="status">
          正在计算学习评估
        </div>
      ) : (
        <EvaluationPageContent
          appliedVersion={appliedVersion}
          isApplying={applyMutation.isPending}
          onApply={(reportId) => applyMutation.mutate(reportId)}
          report={notReady ? null : (reportQuery.data ?? null)}
        />
      )}
    </div>
  )
}
