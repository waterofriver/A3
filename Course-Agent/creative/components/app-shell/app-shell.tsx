"use client"

import {
  BarChart3,
  BookOpenText,
  BrainCircuit,
  LibraryBig,
  LogOut,
  MessageCircleQuestion,
  Route,
  Sparkles,
  UserRoundSearch,
} from "lucide-react"
import Link from "next/link"
import { ReactNode, useState } from "react"
import { usePathname, useRouter } from "next/navigation"

import { QaDrawer } from "@/components/qa/qa-drawer"
import { clearUserId, getUserId } from "@/lib/session/user-session"
import { cn } from "@/lib/utils"

const navigation = [
  { href: "/profile", label: "画像采集", icon: UserRoundSearch },
  { href: "/workspace", label: "资源工作台", icon: Sparkles },
  { href: "/path", label: "学习路径", icon: Route },
  { href: "/evaluation", label: "学习评估", icon: BarChart3 },
  { href: "/knowledge", label: "课程知识库", icon: LibraryBig },
]

const isNavigationActive = (pathname: string, href: string) =>
  pathname.startsWith(href) ||
  (href === "/workspace" && pathname.startsWith("/resources/"))

export function AppShell({ children }: { children: ReactNode }) {
  const [qaOpen, setQaOpen] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const current = navigation.find((item) =>
    isNavigationActive(pathname, item.href),
  )
  const userId = getUserId() ?? "未登录"

  const handleLogout = () => {
    clearUserId()
    router.push("/login")
  }

  return (
    <div className="grid min-h-screen grid-cols-[248px_minmax(0,1fr)] bg-background">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-[248px] flex-col border-r bg-white">
        <div className="flex h-[72px] items-center gap-3 border-b px-6">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
            <BrainCircuit aria-hidden="true" className="h-6 w-6" />
          </span>
          <span>
            <span className="block text-base font-semibold text-[#182132]">智学引擎</span>
            <span className="block text-xs text-[#69778c]">ZHIXUE ENGINE</span>
          </span>
        </div>

        <nav aria-label="主导航" className="flex-1 space-y-1 px-3 py-5">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = isNavigationActive(pathname, item.href)
            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex h-11 items-center gap-3 rounded-md px-3 text-sm font-medium text-[#59677d] transition-colors hover:bg-[#f0f4fb] hover:text-[#2457d6]",
                  isActive && "bg-[#edf3ff] text-[#2457d6]",
                )}
                href={item.href}
                key={item.href}
              >
                <Icon aria-hidden="true" className="h-[18px] w-[18px]" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t p-4">
          <div className="flex items-center gap-3 rounded-md bg-[#f5f7fa] p-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-[#d8ff72] text-sm font-bold text-[#17243d]">
              {userId.slice(0, 1).toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-[#27344a]">{userId}</span>
              <span className="block text-xs text-[#7a8799]">学生账号</span>
            </span>
            <button
              aria-label="退出登录"
              className="flex h-8 w-8 items-center justify-center rounded-md text-[#6f7c90] transition hover:bg-white hover:text-[#c7463c]"
              onClick={handleLogout}
              title="退出登录"
              type="button"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <div className="col-start-2 min-w-0">
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b bg-white/95 px-8 backdrop-blur">
          <div>
            <p className="text-sm font-semibold text-[#27344a]">
              {current?.label ?? "学习中心"}
            </p>
            <p className="mt-1 text-xs text-[#7a8799]">多智能体个性化学习系统</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              aria-label="打开智能答疑"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-[#cdd8e8] bg-white text-[#526279] transition hover:border-[#9bb3dd] hover:bg-[#edf3ff] hover:text-[#2457d6]"
              onClick={() => setQaOpen(true)}
              title="智能答疑"
              type="button"
            >
              <MessageCircleQuestion aria-hidden="true" className="h-4 w-4" />
            </button>
            <span className="inline-flex h-8 items-center gap-2 rounded-md border border-[#d5dfef] bg-[#f7f9fc] px-3 text-xs font-medium text-[#526279]">
              <BookOpenText aria-hidden="true" className="h-3.5 w-3.5" />
              课程未选择
            </span>
            <span className="inline-flex h-8 items-center rounded-md bg-[#fff3d9] px-3 text-xs font-semibold text-[#8a5b05]">
              演示模式
            </span>
          </div>
        </header>
        <main className="min-h-[calc(100vh-72px)] px-8 py-7">{children}</main>
      </div>
      <QaDrawer onOpenChange={setQaOpen} open={qaOpen} userId={userId} />
    </div>
  )
}
