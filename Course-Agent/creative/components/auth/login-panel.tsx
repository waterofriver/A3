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
    <main className="grid min-h-screen place-items-center bg-[#f3f6fb] px-10 py-8 text-[#182132]">
      <section className="grid min-h-[620px] w-full max-w-[1080px] grid-cols-[0.9fr_1.1fr] overflow-hidden rounded-lg border border-[#dce3ed] bg-white shadow-[0_24px_70px_rgba(27,42,70,0.12)]">
        <div className="relative flex flex-col justify-between bg-[#17243d] p-12 text-white">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-md bg-[#d8ff72] text-[#17243d]">
              <BrainCircuit aria-hidden="true" className="h-7 w-7" />
            </div>
            <p className="mt-8 text-sm font-semibold text-[#d8ff72]">ZHIXUE ENGINE</p>
            <h1 className="mt-3 text-4xl font-semibold leading-tight">智学引擎</h1>
            <p className="mt-4 max-w-sm text-base leading-7 text-[#c7d0df]">
              多智能体个性化学习系统
            </p>
          </div>
          <div className="border-t border-white/15 pt-6">
            <div className="flex items-center gap-3 text-sm text-[#c7d0df]">
              <span className="h-2 w-2 rounded-full bg-[#d8ff72]" />
              教学网关已连接
            </div>
          </div>
        </div>

        <div className="flex items-center px-16 py-12">
          <div className="w-full max-w-md">
            <p className="text-sm font-medium text-[#53637b]">学生入口</p>
            <h2 className="mt-2 text-3xl font-semibold text-[#182132]">进入学习空间</h2>
            <p className="mt-3 text-sm leading-6 text-[#66758c]">
              使用你的用户 ID 恢复画像、资源与学习记录。
            </p>

            <form className="mt-10" onSubmit={handleSubmit}>
              <label className="text-sm font-medium text-[#27344a]" htmlFor="user-id">
                用户 ID
              </label>
              <input
                id="user-id"
                autoComplete="username"
                className="mt-3 h-12 w-full rounded-md border border-[#cdd6e3] bg-white px-4 text-base outline-none transition focus:border-[#2457d6] focus:ring-4 focus:ring-[#2457d6]/10"
                onChange={(event) => setUserIdInput(event.target.value)}
                placeholder="例如 student-001"
                value={userId}
              />
              <div className="mt-3 min-h-6" aria-live="polite">
                {error ? <p className="text-sm text-[#c7463c]">{error}</p> : null}
              </div>
              <button
                className="mt-5 flex h-12 w-full items-center justify-center gap-2 rounded-md bg-[#2457d6] px-5 text-sm font-semibold text-white transition hover:bg-[#1d48b5] focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-[#2457d6]/25 disabled:cursor-not-allowed disabled:opacity-60"
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
