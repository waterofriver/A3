"use client"

import { useQuery } from "@tanstack/react-query"
import { Route } from "lucide-react"
import { useRouter } from "next/navigation"

import { ProfileSummary } from "@/components/learning-path/profile-summary"
import { LearningPathGraph } from "@/components/learning-path/learning-path-graph"
import { ErrorNotice } from "@/components/shared/error-notice"
import { apiFetch } from "@/lib/api/client"
import type { LearningPathData } from "@/lib/api/learning-path-types"
import type { CourseSummary } from "@/lib/api/resource-types"
import { getUserId } from "@/lib/session/user-session"
import type { components } from "@/lib/api/generated"

type UserInfo = components["schemas"]["UserInfoData"]

export default function LearningPathPage() {
  const router = useRouter()
  const userId = getUserId() ?? ""
  const coursesQuery = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"),
  })
  const course = coursesQuery.data?.[0]
  const userQuery = useQuery({
    queryKey: ["user", userId],
    queryFn: () =>
      apiFetch<UserInfo>(`/api/user/info?user_id=${encodeURIComponent(userId)}`),
    enabled: Boolean(userId),
  })
  const pathQuery = useQuery({
    queryKey: ["path", userId, course?.name],
    queryFn: () =>
      apiFetch<LearningPathData>(
        `/api/path/get?user_id=${encodeURIComponent(userId)}&course_name=${encodeURIComponent(course?.name ?? "")}`,
      ),
    enabled: Boolean(userId && course?.name && userQuery.data?.profile_confirmed),
  })

  const error = coursesQuery.error ?? userQuery.error ?? pathQuery.error

  return (
    <div className="mx-auto w-full max-w-[1480px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">LEARNING PATH</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">个性化学习路径</h1>
        </div>
        <div className="flex items-center gap-2 text-sm font-medium text-[#526279]">
          <Route aria-hidden="true" className="h-4 w-4 text-[#2457d6]" />
          {course?.name ?? "等待课程"}
        </div>
      </header>

      <div className="mt-6">
        <ProfileSummary profile={userQuery.data?.profile ?? null} />
      </div>

      {error ? (
        <div className="mt-5">
          <ErrorNotice error={error instanceof Error ? error : "学习路径加载失败。"} />
        </div>
      ) : pathQuery.isPending || coursesQuery.isPending || userQuery.isPending ? (
        <div className="mt-6 grid h-[400px] place-items-center border bg-white text-sm text-[#718096]" role="status">
          正在生成学习路径
        </div>
      ) : pathQuery.data ? (
        <div className="mt-6">
          <LearningPathGraph
            nodes={pathQuery.data.nodes}
            onOpenResource={(resourceId) => router.push(`/resources/${resourceId}`)}
          />
        </div>
      ) : (
        <div className="mt-6 grid h-[400px] place-items-center border border-dashed bg-white text-sm text-[#718096]">
          完成画像采集后即可生成学习路径。
        </div>
      )}
    </div>
  )
}
