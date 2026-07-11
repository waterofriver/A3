"use client"

import {
  Bot,
  FileClock,
  LoaderCircle,
  Send,
  UserRound,
} from "lucide-react"
import { FormEvent, useEffect, useRef, useState } from "react"

import {
  AnswerModeControl,
  type AnswerMode,
} from "@/components/qa/answer-mode-control"
import { MarkdownRenderer } from "@/components/resources/markdown-renderer"
import { MediaCard } from "@/components/resources/media-card"
import { VideoPlayer } from "@/components/resources/video-player"
import { AgentProgress } from "@/components/shared/agent-progress"
import { ErrorNotice } from "@/components/shared/error-notice"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Textarea } from "@/components/ui/textarea"
import { ApiError } from "@/lib/api/client"
import { postEventStream } from "@/lib/sse/post-event-stream"
import {
  type GatewayEvent,
  initialTaskState,
  reduceTaskEvent,
  type TaskState,
} from "@/lib/sse/task-reducer"

type StreamQa = (
  path: string,
  body: unknown,
  onEvent: (event: GatewayEvent) => void,
  signal?: AbortSignal,
) => Promise<string | null>

type QaMedia = {
  mode: Exclude<AnswerMode, "text">
  url: string | null
}

type QaTurn = {
  id: string
  question: string
  answer: string
  media?: QaMedia
}

type QaDrawerProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  userId: string
  streamQa?: StreamQa
}

function QaMediaResult({ media }: { media: QaMedia }) {
  if (!media.url) {
    return (
      <div className="mt-4 flex min-h-28 items-center gap-3 rounded-md border border-dashed border-[#cbd6e6] bg-[#f7f9fc] p-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-white text-[#63738b]">
          <FileClock aria-hidden="true" className="h-5 w-5" />
        </span>
        <div>
          <p className="text-sm font-semibold text-[#344258]">等待真实 Agent 返回素材</p>
          <p className="mt-1 text-xs leading-5 text-[#78869a]">
            当前演示流未提供媒体地址，文本答案仍可正常查看。
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-4">
      <MediaCard mediaUrl={media.url}>
        {media.mode === "video" ? (
          <VideoPlayer src={media.url} />
        ) : (
          // Remote Agent URLs are not known at build time, so the browser renders them directly.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            alt="答疑图解"
            className="max-h-[320px] w-full object-contain"
            src={media.url}
          />
        )}
      </MediaCard>
    </div>
  )
}

export function QaDrawer({
  onOpenChange,
  open,
  streamQa = postEventStream,
  userId,
}: QaDrawerProps) {
  const [answerMode, setAnswerMode] = useState<AnswerMode>("text")
  const [question, setQuestion] = useState("")
  const [turns, setTurns] = useState<QaTurn[]>([])
  const [taskState, setTaskState] = useState<TaskState>(initialTaskState)
  const taskStateRef = useRef<TaskState>(initialTaskState)
  const abortRef = useRef<AbortController | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const submitQuestion = async () => {
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion || isStreaming) return

    const submittedMode = answerMode
    const turnId = `qa-${Date.now()}`
    setTurns((current) => [
      ...current,
      { id: turnId, question: trimmedQuestion, answer: "" },
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
      await streamQa(
        "/api/chat/qa",
        {
          user_id: userId,
          question: trimmedQuestion,
          answer_mode: submittedMode,
        },
        (gatewayEvent) => {
          const nextState = reduceTaskEvent(taskStateRef.current, gatewayEvent)
          taskStateRef.current = nextState
          setTaskState(nextState)

          if (gatewayEvent.event === "content.delta") {
            setTurns((current) =>
              current.map((turn) =>
                turn.id === turnId
                  ? { ...turn, answer: nextState.content }
                  : turn,
              ),
            )
          }
          if (gatewayEvent.event === "media.ready" && submittedMode !== "text") {
            setTurns((current) =>
              current.map((turn) =>
                turn.id === turnId
                  ? {
                      ...turn,
                      media: {
                        mode: submittedMode,
                        url: gatewayEvent.media_url ?? null,
                      },
                    }
                  : turn,
              ),
            )
          }
          if (gatewayEvent.event === "task.completed") setQuestion("")
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
          : new ApiError("UPSTREAM_REJECTED", "答疑生成失败，请稍后重试。", true),
      )
    } finally {
      if (!controller.signal.aborted) setIsStreaming(false)
    }
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void submitQuestion()
  }

  return (
    <Sheet onOpenChange={onOpenChange} open={open}>
      <SheetContent className="flex w-[560px] flex-col gap-0 p-0 sm:max-w-[560px]">
        <SheetHeader className="border-b px-6 py-5 pr-14">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
              <Bot aria-hidden="true" className="h-5 w-5" />
            </span>
            <div>
              <SheetTitle className="text-base text-[#182132]">智能答疑</SheetTitle>
              <SheetDescription className="mt-1 text-xs text-[#748196]">
                当前学生 · {userId}
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <div className="border-b px-6 py-4">
          <AgentProgress
            currentAgent={taskState.currentAgent ?? "智能答疑Agent"}
            demoMode={taskState.demoMode}
            progress={taskState.progress}
            status={taskState.status}
          />
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto bg-[#f7f9fc] px-6 py-5">
          {turns.length === 0 ? (
            <div className="flex h-full min-h-48 flex-col items-center justify-center text-center">
              <span className="flex h-11 w-11 items-center justify-center rounded-md border bg-white text-[#6f7f96]">
                <Bot aria-hidden="true" className="h-5 w-5" />
              </span>
              <p className="mt-3 text-sm font-medium text-[#4c5a70]">还没有答疑记录</p>
            </div>
          ) : (
            <div className="space-y-6" aria-live="polite">
              {turns.map((turn) => (
                <div className="space-y-3" key={turn.id}>
                  <div className="ml-auto flex max-w-[84%] items-start justify-end gap-2">
                    <p className="rounded-md bg-[#2457d6] px-4 py-3 text-sm leading-6 text-white">
                      {turn.question}
                    </p>
                    <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#dbe6fb] text-[#2457d6]">
                      <UserRound aria-hidden="true" className="h-3.5 w-3.5" />
                    </span>
                  </div>
                  <div className="flex max-w-[94%] items-start gap-2">
                    <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
                      <Bot aria-hidden="true" className="h-3.5 w-3.5" />
                    </span>
                    <div className="min-w-0 flex-1 rounded-md border bg-white p-4 shadow-sm">
                      {turn.answer ? (
                        <MarkdownRenderer markdown={turn.answer} />
                      ) : (
                        <div className="flex h-8 items-center gap-2 text-sm text-[#748196]" role="status">
                          <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
                          正在组织答案
                        </div>
                      )}
                      {turn.media ? <QaMediaResult media={turn.media} /> : null}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <form className="border-t bg-white px-6 py-5" onSubmit={handleSubmit}>
          {error ? (
            <div className="mb-4">
              <ErrorNotice
                error={error}
                onRetry={error.retryable ? () => void submitQuestion() : undefined}
              />
            </div>
          ) : null}
          <AnswerModeControl
            disabled={isStreaming}
            onValueChange={setAnswerMode}
            value={answerMode}
          />
          <label className="mt-4 block text-xs font-semibold text-[#4d5c72]" htmlFor="qa-question">
            课程问题
          </label>
          <div className="mt-2 flex items-end gap-2">
            <Textarea
              className="min-h-20 resize-none border-[#cfd9e8] text-sm"
              disabled={isStreaming}
              id="qa-question"
              maxLength={4000}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="输入课程相关问题"
              value={question}
            />
            <Button
              aria-label="发送问题"
              className="h-10 w-10 shrink-0 bg-[#2457d6] p-0 hover:bg-[#1d48b5]"
              disabled={!question.trim() || isStreaming || !userId}
              title="发送问题"
              type="submit"
            >
              {isStreaming ? (
                <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
              ) : (
                <Send aria-hidden="true" className="h-4 w-4" />
              )}
            </Button>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  )
}
