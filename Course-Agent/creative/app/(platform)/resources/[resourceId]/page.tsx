"use client"

import { useQuery } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useRef } from "react"

import { ResourceCard } from "@/components/resources/resource-card"
import { ErrorNotice } from "@/components/shared/error-notice"
import { apiFetch } from "@/lib/api/client"
import { queueLearningEvent } from "@/lib/api/learning-events"
import type { ResourceDetail } from "@/lib/api/resource-types"
import { getUserId } from "@/lib/session/user-session"

export default function ResourceDetailPage() {
  const params = useParams<{ resourceId: string }>()
  const resourceId = params.resourceId
  const userId = getUserId() ?? ""
  const openedAt = useRef<string | null>(null)
  const resourceQuery = useQuery({
    queryKey: ["resource", resourceId],
    queryFn: () =>
      apiFetch<ResourceDetail>(`/api/resource/detail/${encodeURIComponent(resourceId)}`),
    enabled: Boolean(resourceId),
  })

  useEffect(() => {
    const resource = resourceQuery.data
    if (!resource?.course_name || !userId) return
    const startedAt = new Date().toISOString()
    openedAt.current = startedAt
    queueLearningEvent(userId, resource.course_name, {
      event_type: "resource_opened",
      resource_id: resource.id,
      client_started_at: startedAt,
      metadata: { resource_type: resource.resource_type },
    })
    return () => {
      queueLearningEvent(userId, resource.course_name as string, {
        event_type: "resource_closed",
        resource_id: resource.id,
        client_started_at: openedAt.current ?? startedAt,
        client_ended_at: new Date().toISOString(),
        metadata: { resource_type: resource.resource_type },
      })
    }
  }, [resourceQuery.data, userId])

  return (
    <div className="mx-auto w-full max-w-[1120px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">RESOURCE DETAIL</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">学习资源详情</h1>
        </div>
        <Link
          className="inline-flex h-10 items-center gap-2 rounded-md border px-4 text-sm font-semibold text-[#526279] hover:bg-[#f4f7fb] hover:text-[#2457d6]"
          href="/workspace"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          返回工作台
        </Link>
      </header>

      {resourceQuery.error ? (
        <div className="mt-6">
          <ErrorNotice
            error={resourceQuery.error as Error}
            onRetry={() => void resourceQuery.refetch()}
          />
        </div>
      ) : resourceQuery.isPending ? (
        <div className="mt-6 grid min-h-[480px] place-items-center border bg-white text-sm text-[#718096]" role="status">
          正在加载学习资源
        </div>
      ) : resourceQuery.data ? (
        <div className="mt-6">
          <ResourceCard resource={resourceQuery.data} />
        </div>
      ) : null}
    </div>
  )
}
