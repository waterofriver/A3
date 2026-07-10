import type { Metadata } from "next"
import { ReactNode } from "react"

import { Providers } from "@/app/providers"

import "./globals.css"

export const metadata: Metadata = {
  title: {
    default: "智学引擎",
    template: "%s | 智学引擎",
  },
  description: "多智能体个性化学习系统",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
