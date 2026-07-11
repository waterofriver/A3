"use client"

import { WifiOff } from "lucide-react"
import { useEffect, useState } from "react"

export function OfflineBanner({ online }: { online?: boolean }) {
  const [detectedOnline, setDetectedOnline] = useState(true)

  useEffect(() => {
    if (online !== undefined) return
    const update = () => setDetectedOnline(window.navigator.onLine)
    update()
    window.addEventListener("online", update)
    window.addEventListener("offline", update)
    return () => {
      window.removeEventListener("online", update)
      window.removeEventListener("offline", update)
    }
  }, [online])

  if (online ?? detectedOnline) return null

  return (
    <div
      className="flex h-9 items-center justify-center gap-2 border-b border-[#e4c16e] bg-[#fff8df] px-4 text-xs font-semibold text-[#7d5b0c]"
      role="status"
    >
      <WifiOff aria-hidden="true" className="h-3.5 w-3.5" />
      当前离线，正在显示已缓存内容
    </div>
  )
}
