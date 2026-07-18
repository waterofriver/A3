"use client"

import {
  BookOpenCheck,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  LoaderCircle,
  XCircle,
} from "lucide-react"
import { useMemo, useState } from "react"

import type { ApiError } from "@/lib/api/client"

type ErrorQuestion = {
  question_id: string
  attempt_id: string
  quiz_title: string
  prompt: string
  question_type: string
  options: string[]
  user_answer: string
  correct_answer: string
  explanation: string
  concept: string
  created_at: string
}

type ErrorNotebookData = {
  questions: ErrorQuestion[]
  total_errors: number
  unique_concepts: number
}

type Props = {
  data: ErrorNotebookData | undefined
  isLoading: boolean
  error: Error | ApiError | null
  onRetry: () => void
}

const typeLabels: Record<string, string> = {
  choice: "选择题",
  blank: "填空题",
  programming: "编程题",
}

function ErrorCard({ item }: { item: ErrorQuestion }) {
  const [expanded, setExpanded] = useState(false)
  const fmtTime = useMemo(() => {
    try {
      return new Date(item.created_at).toLocaleString("zh-CN", {
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
      })
    } catch {
      return ""
    }
  }, [item.created_at])

  return (
    <article className="rounded-lg border bg-white">
      <button
        className="flex w-full items-start gap-3 p-4 text-left"
        onClick={() => setExpanded(!expanded)}
        type="button"
      >
        <span className="mt-0.5 shrink-0">
          <XCircle aria-hidden className="h-4 w-4 text-[#c7463c]" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="rounded bg-[#fef0f0] px-1.5 py-0.5 text-[11px] font-semibold text-[#c7463c]">
              {typeLabels[item.question_type] ?? item.question_type}
            </span>
            <span className="rounded bg-[#edf3ff] px-1.5 py-0.5 text-[11px] font-medium text-[#2457d6]">
              {item.concept}
            </span>
            <span className="ml-auto shrink-0 text-[11px] text-[#96a2b1]">{fmtTime}</span>
          </div>
          <p className="mt-2 text-sm font-medium text-[#27344a] leading-relaxed">
            {item.prompt}
          </p>
        </div>
        <ChevronDown
          aria-hidden
          className={`mt-0.5 h-4 w-4 shrink-0 text-[#98a3b3] transition ${expanded ? "rotate-180" : ""}`}
        />
      </button>

      {expanded ? (
        <div className="border-t bg-[#fbfcfd] px-4 py-3 space-y-2 text-sm">
          {item.options.length > 0 ? (
            <div>
              <span className="text-xs text-[#7a8799]">选项：</span>
              <div className="mt-1 flex flex-wrap gap-2">
                {item.options.map((opt, i) => (
                  <span
                    className={`rounded-md border px-2 py-1 text-xs ${
                      opt === item.correct_answer
                        ? "border-[#a3c97b] bg-[#f4f9ea] text-[#55741f] font-semibold"
                        : opt === item.user_answer
                          ? "border-[#f3a5a5] bg-[#fef5f5] text-[#ba4242]"
                          : "border-[#dfe4eb] text-[#6f7c8e]"
                    }`}
                    key={i}
                  >
                    {opt}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-md border border-[#f3a5a5] bg-[#fef5f5] p-2.5">
              <p className="text-xs text-[#ba4242] font-semibold">你的答案</p>
              <p className="mt-1 text-sm text-[#6b3a2e]">{item.user_answer || "（未作答）"}</p>
            </div>
            <div className="rounded-md border border-[#a3c97b] bg-[#f4f9ea] p-2.5">
              <p className="text-xs text-[#55741f] font-semibold">正确答案</p>
              <p className="mt-1 text-sm text-[#435c1a]">{item.correct_answer}</p>
            </div>
          </div>
          {item.explanation ? (
            <div className="rounded-md bg-[#edf3ff] p-2.5">
              <p className="text-xs text-[#2457d6] font-semibold">解析</p>
              <p className="mt-1 text-sm text-[#46556c] leading-relaxed">{item.explanation}</p>
            </div>
          ) : null}
          <p className="text-xs text-[#98a3b3]">来源：{item.quiz_title}</p>
        </div>
      ) : null}
    </article>
  )
}

export function ErrorNotebook({ data, isLoading, error: queryError, onRetry }: Props) {
  const groups = useMemo(() => {
    const questions = data?.questions ?? []
    const map = new Map<string, ErrorQuestion[]>()
    for (const question of questions) {
      const list = map.get(question.concept) ?? []
      list.push(question)
      map.set(question.concept, list)
    }
    return [...map.entries()]
  }, [data?.questions])

  if (isLoading) {
    return (
      <div className="flex h-[360px] items-center justify-center text-sm text-[#718096]" role="status">
        <LoaderCircle aria-hidden className="mr-2 h-4 w-4 animate-spin" />
        正在加载错题本
      </div>
    )
  }

  if (queryError) {
    return (
      <div className="flex h-[360px] flex-col items-center justify-center text-center">
        <CircleAlert aria-hidden className="mb-3 h-8 w-8 text-[#c7463c]" />
        <p className="text-sm font-semibold text-[#4b4750]">加载失败</p>
        <p className="mt-1 text-xs text-[#7a8799]">
          {queryError instanceof Error ? queryError.message : "无法加载错题记录"}
        </p>
        <button
          className="mt-4 rounded-md bg-[#2457d6] px-4 py-2 text-xs font-semibold text-white hover:bg-[#1d48b5]"
          onClick={onRetry}
          type="button"
        >
          重试
        </button>
      </div>
    )
  }

  if (!data || data.questions.length === 0) {
    return (
      <div className="flex h-[360px] flex-col items-center justify-center text-center">
        <BookOpenCheck aria-hidden className="mb-3 h-8 w-8 text-[#98a3b3]" />
        <p className="text-sm font-semibold text-[#4b4750]">暂无错题记录</p>
        <p className="mt-1 text-xs text-[#7a8799]">
          完成题库练习后，错题会自动汇总到这里
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* 统计栏 */}
      <div className="mb-5 flex items-center gap-4 rounded-lg border bg-white px-4 py-3 text-sm">
        <span className="flex items-center gap-1.5">
          <CheckCircle2 aria-hidden className="h-4 w-4 text-[#c7463c]" />
          <span className="font-semibold text-[#27344a]">{data.total_errors} 道错题</span>
        </span>
        <span className="text-[#cdd6e3]">|</span>
        <span className="text-[#7a8799]">
          涉及 <span className="font-semibold text-[#27344a]">{data.unique_concepts}</span> 个知识点
        </span>
      </div>

      {/* 按概念分组 */}
      {groups.map(([concept, questions]) => (
        <div className="mb-6" key={concept}>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#344258]">
            <span className="inline-block h-2 w-2 rounded-full bg-[#2457d6]" />
            {concept}
            <span className="text-xs font-normal text-[#96a2b1]">
              {questions.length} 题
            </span>
          </h3>
          <div className="space-y-3">
            {questions.map((q) => (
              <ErrorCard item={q} key={`${q.attempt_id}-${q.question_id}`} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
