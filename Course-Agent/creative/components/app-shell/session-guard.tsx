"use client"

import { BrainCircuit, LoaderCircle } from "lucide-react"
import { ReactNode, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { getUserId } from "@/lib/session/user-session"

export function SessionGuard({ children }: { children: ReactNode }) {
  const router = useRouter()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    if (!getUserId()) {
      router.replace("/login")
      return
    }
    setIsReady(true)
  }, [router])

  if (!isReady) {
    return (
      <div className="grid min-h-screen place-items-center bg-background" role="status">
        <div className="flex items-center gap-4 text-foreground">
          <span className="flex h-11 w-11 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
            <BrainCircuit aria-hidden="true" className="h-6 w-6" />
          </span>
          <span className="flex items-center gap-2 text-sm text-muted-foreground">
            <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
            正在恢复学习空间
          </span>
        </div>
      </div>
    )
  }

  return children
}
