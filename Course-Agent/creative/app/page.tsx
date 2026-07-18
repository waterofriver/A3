"use client"

import { BrainCircuit, LoaderCircle } from "lucide-react"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

import { getUserId } from "@/lib/session/user-session"

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace(getUserId() ? "/dashboard" : "/login")
  }, [router])

  return (
    <main className="grid min-h-screen place-items-center bg-[#f3f6fb] text-[#182132]">
      <div className="flex min-h-24 items-center gap-4" role="status">
        <span className="flex h-11 w-11 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
          <BrainCircuit aria-hidden="true" className="h-6 w-6" />
        </span>
        <span>
          <span className="block text-sm font-semibold">智学引擎</span>
          <span className="mt-1 flex items-center gap-2 text-xs text-[#66758c]">
            <LoaderCircle aria-hidden="true" className="h-3.5 w-3.5 animate-spin" />
            正在恢复学习空间
          </span>
        </span>
      </div>
    </main>
  )
}
