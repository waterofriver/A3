"use client"

import { ArrowRight, BrainCircuit, LoaderCircle } from "lucide-react"
import { FormEvent, useState } from "react"
import { useRouter } from "next/navigation"

import { ApiError, apiFetch } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"
import { setUserId } from "@/lib/session/user-session"

type UserInfo = components["schemas"]["UserInfoData"]

export function LoginPanel() {
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
    <main className="grid min-h-screen place-items-center bg-slate-50 px-10 py-8 text-slate-800">
      <section className="grid min-h-[620px] w-full max-w-[1080px] grid-cols-[0.9fr_1.1fr] overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/10">
        <div className="relative flex flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-slate-850 p-12 text-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.08),transparent_50%)]" />
          <div className="relative z-10">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-400/20">
              <BrainCircuit aria-hidden="true" className="h-6 w-6" />
            </div>
            <p className="mt-8 text-xs font-bold tracking-widest text-emerald-400 uppercase">ZHIXUE ENGINE</p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-tight leading-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">智学引擎</h1>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-slate-400">
              多智能体个性化学习系统
            </p>
          </div>
          <div className="relative z-10 border-t border-white/10 pt-6">
            <div className="flex items-center gap-3 text-xs font-medium text-slate-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow shadow-emerald-400/50" />
              教学网关已连接
            </div>
          </div>
        </div>

        <div className="flex items-center px-16 py-12 bg-white">
          <div className="w-full max-w-md">
            <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">学生入口</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-800">进入学习空间</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-500">
              使用你的用户 ID 恢复画像、资源与学习记录。
            </p>

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
          </div>
        </div>
      </section>
    </main>
  )
}
