"use client"

import { LoaderCircle, Play, Sparkles } from "lucide-react"
import { FormEvent, useState } from "react"

import { ErrorNotice } from "@/components/shared/error-notice"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ApiError, apiFetch } from "@/lib/api/client"

type CourseSummary = { name: string; slug: string }

type QuizGeneratorProps = {
  userId: string
  courses: CourseSummary[]
  onTaskCreated: (taskId: string) => void
}

export function QuizGenerator({ userId, courses, onTaskCreated }: QuizGeneratorProps) {
  const [courseName, setCourseName] = useState(courses[0]?.name ?? "")
  const [weakPoint, setWeakPoint] = useState("")
  const [count, setCount] = useState(5)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!courseName || !userId) return
    setError(null)
    setIsSubmitting(true)
    try {
      const result = await apiFetch<{ task_id: string; status: string }>(
        "/api/quiz/generate",
        {
          method: "POST",
          headers: { "Idempotency-Key": crypto.randomUUID() },
          body: JSON.stringify({
            user_id: userId,
            course_name: courseName,
            weak_point: weakPoint,
            count,
          }),
        },
      )
      onTaskCreated(result.task_id)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError("UPSTREAM_REJECTED", "出题失败，请稍后重试。", true),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-[640px]">
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#edf3ff] text-[#2457d6]">
          <Sparkles aria-hidden className="h-5 w-5" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-[#182132]">智能出题</h2>
          <p className="text-xs text-[#7a8799]">
            Agent 根据薄弱点生成针对性练习题
          </p>
        </div>
      </div>

      {error ? (
        <div className="mb-4">
          <ErrorNotice error={error} onRetry={() => setError(null)} />
        </div>
      ) : null}

      <form className="space-y-4 rounded-lg border bg-white p-5" onSubmit={handleSubmit}>
        <div>
          <label className="text-xs font-semibold text-[#4d5c72]" htmlFor="qz-course">
            目标课程
          </label>
          <select
            className="mt-2 block w-full rounded-md border border-[#cfd9e8] px-3 py-2.5 text-sm text-[#344258]"
            disabled={courses.length === 0 || isSubmitting}
            id="qz-course"
            onChange={(e) => setCourseName(e.target.value)}
            value={courseName}
          >
            {courses.map((c) => (
              <option key={c.slug} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-[#4d5c72]" htmlFor="qz-weak">
            薄弱知识点（选填）
          </label>
          <Input
            className="mt-2 border-[#cfd9e8] text-sm"
            disabled={isSubmitting}
            id="qz-weak"
            onChange={(e) => setWeakPoint(e.target.value)}
            placeholder="如：ARP 欺骗、ROS 通信，留空则由 Agent 自动判定"
            value={weakPoint}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-[#4d5c72]" htmlFor="qz-count">
            题目数量
          </label>
          <select
            className="mt-2 block w-full rounded-md border border-[#cfd9e8] px-3 py-2.5 text-sm text-[#344258]"
            disabled={isSubmitting}
            id="qz-count"
            onChange={(e) => setCount(Number(e.target.value))}
            value={count}
          >
            {[3, 5, 8, 10, 15, 20].map((n) => (
              <option key={n} value={n}>{n} 题</option>
            ))}
          </select>
        </div>

        <Button
          className="w-full bg-[#2457d6] hover:bg-[#1d48b5]"
          disabled={!courseName || isSubmitting || !userId}
          type="submit"
        >
          {isSubmitting ? (
            <LoaderCircle aria-hidden className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Play aria-hidden className="mr-2 h-4 w-4" />
          )}
          {isSubmitting ? "正在生成题目..." : "开始出题"}
        </Button>
      </form>
    </div>
  )
}
