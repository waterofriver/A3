"use client"

import { CheckCircle2, LoaderCircle } from "lucide-react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"

import { ProfileChat, type ProfileMessage } from "@/components/profile/profile-chat"
import {
  EMPTY_PROFILE,
  ProfilePanel,
  type StudentProfile,
} from "@/components/profile/profile-panel"
import { AgentProgress } from "@/components/shared/agent-progress"
import { ErrorNotice } from "@/components/shared/error-notice"
import { ApiError, apiFetch } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"
import { queryKeys } from "@/lib/query/keys"
import { getUserId } from "@/lib/session/user-session"
import { postEventStream } from "@/lib/sse/post-event-stream"
import {
  type GatewayEvent,
  initialTaskState,
  reduceTaskEvent,
  type TaskState,
} from "@/lib/sse/task-reducer"

type UserInfo = components["schemas"]["UserInfoData"]

type ProfilePageProps = {
  loadUser?: (userId: string) => Promise<UserInfo>
  streamProfile?: (
    path: string,
    body: unknown,
    onEvent: (event: GatewayEvent) => void,
    signal?: AbortSignal,
  ) => Promise<string | null>
  confirmProfile?: (userId: string) => Promise<UserInfo>
}

const loadUserFromApi = (userId: string) =>
  apiFetch<UserInfo>(`/api/user/info?user_id=${encodeURIComponent(userId)}`)

const confirmProfileWithApi = (userId: string) =>
  apiFetch<UserInfo>("/api/profile/confirm", {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  })

function isProfileComplete(profile: StudentProfile) {
  const collected = (value: string) => Boolean(value.trim()) && value !== "待采集"
  return (
    collected(profile.knowledge_foundation) &&
    collected(profile.cognitive_style) &&
    Boolean(profile.weak_points?.length) &&
    collected(profile.learning_pace) &&
    Boolean(profile.content_preferences?.length) &&
    collected(profile.short_term_goal)
  )
}

export function ProfilePage({
  loadUser = loadUserFromApi,
  streamProfile = postEventStream,
  confirmProfile = confirmProfileWithApi,
}: ProfilePageProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const userId = getUserId() ?? ""
  const [messages, setMessages] = useState<ProfileMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "你好，我是画像抽取 Agent。请告诉我你正在学习的课程与近期目标。",
    },
  ])
  const [taskState, setTaskState] = useState<TaskState>(initialTaskState)
  const taskStateRef = useRef<TaskState>(initialTaskState)
  const abortRef = useRef<AbortController | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const userQuery = useQuery({
    queryKey: queryKeys.user(userId),
    queryFn: () => loadUser(userId),
    enabled: Boolean(userId),
  })

  useEffect(() => () => abortRef.current?.abort(), [])

  const streamedProfile = taskState.profile as StudentProfile | null
  const profile = streamedProfile ?? userQuery.data?.profile ?? EMPTY_PROFILE

  const handleSend = async (chatText: string) => {
    const userMessageId = `user-${Date.now()}`
    const assistantMessageId = `assistant-${Date.now()}`
    setMessages((current) => [
      ...current,
      { id: userMessageId, role: "user", content: chatText },
      { id: assistantMessageId, role: "assistant", content: "" },
    ])
    const resetState = { ...initialTaskState }
    taskStateRef.current = resetState
    setTaskState(resetState)
    setError(null)
    setIsStreaming(true)
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await streamProfile(
        "/api/chat/profile",
        { user_id: userId, chat_text: chatText },
        (gatewayEvent) => {
          const nextState = reduceTaskEvent(taskStateRef.current, gatewayEvent)
          taskStateRef.current = nextState
          setTaskState(nextState)
          if (gatewayEvent.event === "content.delta") {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, content: nextState.content }
                  : message,
              ),
            )
          }
          if (gatewayEvent.event === "task.failed" && gatewayEvent.error) {
            setError(
              new ApiError(
                gatewayEvent.error.code,
                gatewayEvent.error.message,
                gatewayEvent.error.retryable,
                gatewayEvent.trace_id,
              ),
            )
          }
        },
        controller.signal,
      )
    } catch (caught) {
      if (controller.signal.aborted) return
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("UPSTREAM_REJECTED", "画像生成失败，请稍后重试。", true),
      )
    } finally {
      if (!controller.signal.aborted) setIsStreaming(false)
    }
  }

  const handleConfirm = async () => {
    setError(null)
    setIsConfirming(true)
    try {
      const confirmed = await confirmProfile(userId)
      queryClient.setQueryData(queryKeys.user(userId), confirmed)
      router.push("/workspace")
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("UPSTREAM_REJECTED", "画像确认失败，请稍后重试。", true),
      )
    } finally {
      setIsConfirming(false)
    }
  }

  const queryError = userQuery.error
    ? userQuery.error instanceof ApiError
      ? userQuery.error
      : new ApiError("NETWORK_UNAVAILABLE", "学生画像加载失败。", true)
    : null
  const displayedError = error ?? queryError

  return (
    <div className="mx-auto w-full max-w-[1440px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">LEARNER PROFILE</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">画像采集</h1>
        </div>
        <span className="text-sm text-[#718096]">第 1 步 · 学习画像</span>
      </header>

      <div className="mt-6">
        <AgentProgress
          currentAgent={taskState.currentAgent}
          demoMode={taskState.demoMode}
          progress={taskState.progress}
          status={taskState.status}
        />
      </div>

      {displayedError ? (
        <div className="mt-4">
          <ErrorNotice
            error={displayedError}
            onRetry={displayedError.retryable ? () => userQuery.refetch() : undefined}
          />
        </div>
      ) : null}

      <div className="mt-6 grid grid-cols-[minmax(0,1.08fr)_minmax(480px,0.92fr)] gap-6">
        <ProfileChat
          isStreaming={isStreaming}
          messages={messages}
          onSend={handleSend}
        />

        <section className="flex min-h-[620px] flex-col">
          {userQuery.isPending ? (
            <div className="mb-4 flex h-10 items-center gap-2 text-sm text-[#718096]" role="status">
              <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
              正在读取历史画像
            </div>
          ) : null}
          <ProfilePanel profile={profile} />
          <div className="mt-auto flex items-center justify-between border-t pt-5">
            <p className="text-xs text-[#7a8799]">
              {isProfileComplete(profile) ? "六维画像已完整" : "画像仍在采集中"}
            </p>
            <button
              className="inline-flex h-11 items-center gap-2 rounded-md bg-[#2457d6] px-5 text-sm font-semibold text-white transition hover:bg-[#1d48b5] disabled:cursor-not-allowed disabled:opacity-45"
              disabled={!isProfileComplete(profile) || isStreaming || isConfirming}
              onClick={handleConfirm}
              type="button"
            >
              {isConfirming ? (
                <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
              )}
              画像确认完成
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}
