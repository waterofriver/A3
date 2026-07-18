"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { FileQuestion, History } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import { ErrorNotebook } from "@/components/quiz/error-notebook"
import { QuizGenerator } from "@/components/quiz/quiz-generator"
import { QuizPlayer } from "@/components/resources/quiz-player"
import { AgentProgress } from "@/components/shared/agent-progress"
import { ErrorNotice } from "@/components/shared/error-notice"
import { ApiError, apiFetch } from "@/lib/api/client"
import type { CourseSummary, QuizResourceDetail } from "@/lib/api/resource-types"
import {
  applyResourceEvent,
  clearActiveResourceTask,
  createResourceTaskState,
  rememberActiveResourceTask,
  type ResourceTaskState,
} from "@/lib/query/resource-cache"
import { getUserId } from "@/lib/session/user-session"
import {
  subscribeToResourceTask,
  type ResourceConnectionState,
} from "@/lib/sse/resource-event-source"

type ErrorData = {
  questions: {
    question_id: string; attempt_id: string; quiz_title: string
    prompt: string; question_type: string; options: string[]
    user_answer: string; correct_answer: string; explanation: string
    concept: string; created_at: string
  }[]
  total_errors: number
  unique_concepts: number
}

export default function QuizPage() {
  const queryClient = useQueryClient()
  const userId = getUserId() ?? ""
  const [tab, setTab] = useState<"generate" | "errors">("generate")
  const [task, setTask] = useState<ResourceTaskState>(() => createResourceTaskState())
  const [latestQuizId, setLatestQuizId] = useState<string | null>(null)
  const [quizError, setQuizError] = useState<ApiError | null>(null)

  const coursesQuery = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"),
  })
  const courses = useMemo(() => coursesQuery.data ?? [], [coursesQuery.data])

  const errorsQuery = useQuery({
    queryKey: ["quiz-errors", userId],
    queryFn: () =>
      apiFetch<ErrorData>(
        `/api/quiz/errors?user_id=${encodeURIComponent(userId)}`,
      ),
    enabled: tab === "errors" && Boolean(userId),
  })

  // Fetch quiz resource detail after generation
  const quizDetailQuery = useQuery({
    queryKey: ["resource", latestQuizId],
    queryFn: () =>
      apiFetch<QuizResourceDetail>(
        `/api/resource/detail/${encodeURIComponent(latestQuizId ?? "")}`,
      ),
    enabled: Boolean(latestQuizId),
  })

  // SSE streaming
  useEffect(() => {
    if (!task.taskId) return
    return subscribeToResourceTask(
      task.taskId,
      (event) => {
        setTask((cur) => applyResourceEvent(cur, event))
        if (event.event === "task.completed") {
          clearActiveResourceTask(userId, "quiz-practice")
          if (event.resource_ids?.length) {
            setLatestQuizId(event.resource_ids[0])
            void queryClient.invalidateQueries({ queryKey: ["quiz-errors", userId] })
          }
        }
        if (event.event === "task.failed") {
          clearActiveResourceTask(userId, "quiz-practice")
          if (event.error) {
            setQuizError(
              new ApiError(event.error.code, event.error.message, event.error.retryable, event.trace_id),
            )
          }
        }
      },
      () => {},
      0,
    )
  }, [task.taskId, queryClient, userId])

  const handleTaskCreated = useCallback(
    (newTaskId: string) => {
      setLatestQuizId(null)
      setQuizError(null)
      rememberActiveResourceTask(userId, "quiz-practice", newTaskId)
      const next = createResourceTaskState(newTaskId)
      next.status = "running"
      setTask(next)
    },
    [userId],
  )

  const progressStatus = task.status === "partial_success" ? "failed" : task.status

  return (
    <div className="mx-auto w-full max-w-[1200px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">QUIZ PRACTICE</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">题库练习</h1>
        </div>
        <div className="flex gap-1 rounded-md bg-[#eef2f7] p-1">
          <button
            className={`flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition ${
              tab === "generate"
                ? "bg-white text-[#2457d6] shadow-sm"
                : "text-[#617086] hover:text-[#2457d6]"
            }`}
            onClick={() => setTab("generate")}
            type="button"
          >
            <FileQuestion aria-hidden className="h-4 w-4" />
            智能出题
          </button>
          <button
            className={`flex items-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition ${
              tab === "errors"
                ? "bg-white text-[#2457d6] shadow-sm"
                : "text-[#617086] hover:text-[#2457d6]"
            }`}
            onClick={() => setTab("errors")}
            type="button"
          >
            <History aria-hidden className="h-4 w-4" />
            错题本
          </button>
        </div>
      </header>

      {tab === "generate" ? (
        <div className="mt-6">
          {task.taskId ? (
            <div className="mb-5">
              <AgentProgress
                currentAgent={task.currentAgent ?? "题库Agent"}
                demoMode={task.demoMode}
                progress={task.globalProgress}
                status={progressStatus}
              />
            </div>
          ) : null}

          {quizError ? (
            <div className="mb-5">
              <ErrorNotice error={quizError} onRetry={() => setQuizError(null)} />
            </div>
          ) : null}

          {latestQuizId && quizDetailQuery.data ? (
            <div className="space-y-4">
              <div className="flex items-center gap-2 rounded-md border border-[#c9dda9] bg-[#f4f9ea] px-4 py-3 text-sm font-semibold text-[#55741f]" role="status">
                题库已生成，开始作答！
              </div>
              <QuizPlayer
                resource={quizDetailQuery.data}
                userId={userId}
              />
            </div>
          ) : latestQuizId && quizDetailQuery.isPending ? (
            <div className="grid h-48 place-items-center text-sm text-[#718096]" role="status">
              正在加载题目...
            </div>
          ) : (
            <QuizGenerator
              courses={courses}
              onTaskCreated={handleTaskCreated}
              userId={userId}
            />
          )}
        </div>
      ) : (
        <div className="mt-6">
          <ErrorNotebook
            data={errorsQuery.data ?? undefined}
            error={errorsQuery.error}
            isLoading={errorsQuery.isPending}
            onRetry={() => void errorsQuery.refetch()}
          />
        </div>
      )}
    </div>
  )
}
