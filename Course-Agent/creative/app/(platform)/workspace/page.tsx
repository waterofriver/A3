"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useMemo, useState } from "react"

import { GenerationForm, type GenerationValues } from "@/components/resources/generation-form"
import { ResourceGrid } from "@/components/resources/resource-grid"
import { TaskRail } from "@/components/resources/task-rail"
import { AgentProgress } from "@/components/shared/agent-progress"
import { ErrorNotice } from "@/components/shared/error-notice"
import { ApiError, apiFetch } from "@/lib/api/client"
import type {
  CourseSummary,
  ResourceSummary,
  ResourceType,
} from "@/lib/api/resource-types"
import { queryKeys } from "@/lib/query/keys"
import {
  applyResourceEvent,
  clearActiveResourceTask,
  createResourceTaskState,
  readActiveResourceTask,
  rememberActiveResourceTask,
  type ResourceTaskState,
} from "@/lib/query/resource-cache"
import { getUserId } from "@/lib/session/user-session"
import {
  subscribeToResourceTask,
  type ResourceConnectionState,
} from "@/lib/sse/resource-event-source"

type TaskAccepted = { task_id: string; status: string }
type TaskSnapshot = {
  task_id: string
  status: "queued" | "running" | "succeeded" | "failed" | "partial_success"
  progress: number
  current_agent?: string | null
  request: { resource_type_list?: ResourceType[] }
  error?: { code: string; message: string; retryable: boolean } | null
}

export default function WorkspacePage() {
  const queryClient = useQueryClient()
  const userId = getUserId() ?? ""
  const [courseName, setCourseName] = useState("")
  const [selectedTypes, setSelectedTypes] = useState<ResourceType[]>([])
  const [task, setTask] = useState<ResourceTaskState>(() => createResourceTaskState())
  const [connectionState, setConnectionState] = useState<ResourceConnectionState>("closed")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const coursesQuery = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"),
  })
  const courses = useMemo(() => coursesQuery.data ?? [], [coursesQuery.data])

  useEffect(() => {
    if (!courseName && courses[0]) setCourseName(courses[0].name)
  }, [courseName, courses])

  const historyQuery = useQuery({
    queryKey: queryKeys.resources(userId, courseName),
    queryFn: () =>
      apiFetch<{ resources: ResourceSummary[] }>(
        `/api/resource/list?user_id=${encodeURIComponent(userId)}&course_name=${encodeURIComponent(courseName)}`,
      ),
    enabled: Boolean(userId && courseName),
  })
  const resources = historyQuery.data?.resources ?? []

  const reconcileTask = useCallback(
    async (taskId: string, activeCourse: string) => {
      try {
        const snapshot = await apiFetch<TaskSnapshot>(`/api/task/${taskId}`)
        setSelectedTypes(snapshot.request.resource_type_list ?? [])
        setTask((current) => ({
          ...current,
          taskId,
          globalProgress: snapshot.progress,
          currentAgent: snapshot.current_agent ?? current.currentAgent,
          status:
            snapshot.status === "queued" ? "running" : snapshot.status,
          error: snapshot.error ?? current.error,
        }))
        if (["succeeded", "failed", "partial_success"].includes(snapshot.status)) {
          clearActiveResourceTask(userId, activeCourse)
          void queryClient.invalidateQueries({
            queryKey: queryKeys.resources(userId, activeCourse),
          })
        }
      } catch (caught) {
        setError(
          caught instanceof ApiError
            ? caught
            : new ApiError("NETWORK_UNAVAILABLE", "任务状态恢复失败。", true),
        )
      }
    },
    [queryClient, userId],
  )

  useEffect(() => {
    if (!userId || !courseName || task.taskId) return
    const remembered = readActiveResourceTask(userId, courseName)
    if (remembered) {
      setTask(createResourceTaskState(remembered))
      void reconcileTask(remembered, courseName)
    }
  }, [courseName, reconcileTask, task.taskId, userId])

  useEffect(() => {
    if (!task.taskId || !courseName) return
    const taskId = task.taskId
    return subscribeToResourceTask(
      taskId,
      (event) => {
        setTask((current) => applyResourceEvent(current, event))
        if (event.event === "task.completed" || event.event === "task.failed") {
          clearActiveResourceTask(userId, courseName)
          void queryClient.invalidateQueries({
            queryKey: queryKeys.resources(userId, courseName),
          })
        }
      },
      (state) => {
        setConnectionState(state)
        if (state === "error") void reconcileTask(taskId, courseName)
      },
      0,
    )
  }, [courseName, queryClient, reconcileTask, task.taskId, userId])

  const handleGenerate = async (values: GenerationValues) => {
    setError(null)
    setIsSubmitting(true)
    setCourseName(values.course_name)
    setSelectedTypes(values.resource_type_list)
    try {
      const accepted = await apiFetch<TaskAccepted>("/api/resource/generate", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ user_id: userId, ...values }),
      })
      rememberActiveResourceTask(userId, values.course_name, accepted.task_id)
      const nextTask = createResourceTaskState(accepted.task_id)
      nextTask.status = "running"
      setTask(nextTask)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("UPSTREAM_REJECTED", "资源任务提交失败。", true),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRetry = async () => {
    if (!task.taskId) return
    setError(null)
    try {
      const accepted = await apiFetch<TaskAccepted>(`/api/task/${task.taskId}/retry`, {
        method: "POST",
      })
      rememberActiveResourceTask(userId, courseName, accepted.task_id)
      const nextTask = createResourceTaskState(accepted.task_id)
      nextTask.status = "running"
      setTask(nextTask)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("UPSTREAM_REJECTED", "任务重试失败。", true),
      )
    }
  }

  const progressStatus =
    task.status === "partial_success" ? "failed" : task.status

  return (
    <div className="mx-auto w-full max-w-[1480px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">RESOURCE STUDIO</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">资源工作台</h1>
        </div>
        <div className="text-right">
          <p className="text-xs text-[#7a8799]">当前课程</p>
          <p className="mt-1 text-sm font-semibold text-[#344158]">{courseName || "等待选择"}</p>
        </div>
      </header>

      {task.taskId ? (
        <div className="mt-5">
          <AgentProgress
            currentAgent={task.currentAgent}
            demoMode={task.demoMode}
            progress={task.globalProgress}
            status={progressStatus}
          />
        </div>
      ) : null}

      {task.status === "succeeded" ? (
        <div
          className="mt-4 border border-[#c9dda9] bg-[#f4f9ea] px-4 py-3 text-sm font-semibold text-[#55741f]"
          role="status"
        >
          全部资源已生成
        </div>
      ) : null}

      {error || coursesQuery.error || historyQuery.error ? (
        <div className="mt-4">
          <ErrorNotice
            error={error ?? (coursesQuery.error as Error) ?? (historyQuery.error as Error)}
            onRetry={() => {
              void coursesQuery.refetch()
              void historyQuery.refetch()
            }}
          />
        </div>
      ) : null}

      <div
        className={`mt-6 grid items-start gap-6 ${
          task.taskId
            ? "grid-cols-[330px_minmax(520px,1fr)_280px]"
            : "grid-cols-[330px_minmax(560px,1fr)]"
        }`}
      >
        <GenerationForm
          courses={courses}
          isSubmitting={isSubmitting}
          onCourseChange={(course) => setCourseName(course.name)}
          onGenerate={handleGenerate}
        />
        <ResourceGrid
          isLoading={historyQuery.isPending || coursesQuery.isPending}
          resources={resources}
        />
        {task.taskId ? (
          <TaskRail
            connectionState={connectionState}
            onRetry={handleRetry}
            selectedTypes={selectedTypes}
            task={task}
          />
        ) : null}
      </div>
    </div>
  )
}
