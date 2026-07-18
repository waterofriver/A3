"use client"

import { ArrowRight, LoaderCircle } from "lucide-react"
import { FormEvent, useState } from "react"
import { useRouter } from "next/navigation"

import { ApiError, apiFetch } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"
import { setUserId } from "@/lib/session/user-session"

type UserInfo = components["schemas"]["UserInfoData"]

type UserIdLoginFormProps = {
  onSuccess?: () => void
}

export function UserIdLoginForm({ onSuccess }: UserIdLoginFormProps) {
  const router = useRouter()
  const [userId, setUserIdInput] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const normalizedUserId = userId.trim()

    if (!normalizedUserId) {
      setError("请输入用户 ID。")
      return
    }

    setError(null)
    setIsSubmitting(true)

    try {
      const info = await apiFetch<UserInfo>(
        `/api/user/info?user_id=${encodeURIComponent(normalizedUserId)}`,
      )
      setUserId(normalizedUserId)
      onSuccess?.()
      router.push(info.profile_confirmed ? "/workspace" : "/profile")
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "登录初始化失败，请稍后重试。",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="mt-8" onSubmit={handleSubmit}>
      <label className="text-xs font-semibold tracking-wide text-slate-500 uppercase" htmlFor="user-id">
        用户 ID
      </label>
      <input
        id="user-id"
        autoComplete="username"
        className="mt-3 h-12 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-4 text-base text-slate-700 placeholder-slate-400 outline-none transition-all duration-200 hover:border-slate-300 focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
        onChange={(event) => setUserIdInput(event.target.value)}
        placeholder="例如 student-001"
        value={userId}
      />
      <div className="mt-3 min-h-6" aria-live="polite">
        {error ? <p className="text-sm font-medium text-rose-500">{error}</p> : null}
      </div>
      <button
        className="mt-4 flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 text-sm font-semibold text-white shadow-md shadow-primary/10 transition-all duration-200 hover:bg-blue-600 hover:shadow-lg hover:shadow-primary/20 hover:-translate-y-[0.5px] active:translate-y-0 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/25 disabled:cursor-not-allowed disabled:opacity-60 disabled:transform-none disabled:shadow-none"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? (
          <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowRight aria-hidden="true" className="h-4 w-4" />
        )}
        {isSubmitting ? "正在连接" : "进入学习平台"}
      </button>
    </form>
  )
}
