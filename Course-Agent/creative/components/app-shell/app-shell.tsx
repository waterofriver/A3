"use client"

import {
  BarChart3,
  BookOpenText,
  BrainCircuit,
  FileQuestion,
  LayoutDashboard,
  LibraryBig,
  LogOut,
  MessageCircleQuestion,
  Route,
  Sparkles,
  UserRoundSearch,
} from "lucide-react"
import Link from "next/link"
import { ReactNode, useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"

import { QaDrawer } from "@/components/qa/qa-drawer"
import { OfflineBanner } from "@/components/shared/offline-banner"
import { clearUserId, getUserId } from "@/lib/session/user-session"
import {
  subscribeToDemoMode,
  wasDemoModeAnnounced,
} from "@/lib/runtime/demo-mode"
import {
  getRememberedCourse,
  subscribeToSelectedCourse,
} from "@/lib/course-selection"
import { cn } from "@/lib/utils"

const navigation = [
  { href: "/dashboard", label: "学习仪表盘", icon: LayoutDashboard },
  { href: "/profile", label: "画像采集", icon: UserRoundSearch },
  { href: "/workspace", label: "资源工作台", icon: Sparkles },
  { href: "/quiz", label: "题库练习", icon: FileQuestion },
  { href: "/path", label: "学习路径", icon: Route },
  { href: "/evaluation", label: "学习评估", icon: BarChart3 },
  { href: "/knowledge", label: "课程知识库", icon: LibraryBig },
]

const isNavigationActive = (pathname: string, href: string) =>
  pathname.startsWith(href) ||
  (href === "/workspace" && pathname.startsWith("/resources/"))

export function AppShell({
  children,
  initialDemoMode = process.env.NEXT_PUBLIC_AGENT_MODE !== "remote",
}: {
  children: ReactNode
  initialDemoMode?: boolean
}) {
  const [qaOpen, setQaOpen] = useState(false)
  const [demoMode, setDemoMode] = useState(initialDemoMode)
  const [selectedCourseName, setSelectedCourseName] = useState<string | null>(null)
  const pathname = usePathname()
  const router = useRouter()
  const current = navigation.find((item) =>
    isNavigationActive(pathname, item.href),
  )
  const userId = getUserId() ?? "未登录"

  useEffect(() => {
    const showDemoMode = () => setDemoMode(true)
    if (wasDemoModeAnnounced()) showDemoMode()
    return subscribeToDemoMode(showDemoMode)
  }, [])

  useEffect(() => {
    setSelectedCourseName(getRememberedCourse())
    return subscribeToSelectedCourse(setSelectedCourseName)
  }, [])

  const handleLogout = () => {
    clearUserId()
    router.push("/login")
  }

  return (
    <div className="grid min-h-screen grid-cols-[248px_minmax(0,1fr)] bg-background">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-[248px] flex-col border-r border-slate-200/80 bg-white shadow-sm">
        <div className="flex h-[72px] items-center gap-3 border-b border-slate-200/80 px-6 bg-slate-50/40">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-emerald-400 shadow-md">
            <BrainCircuit aria-hidden="true" className="h-5.5 w-5.5" />
          </span>
          <span>
            <span className="block text-base font-semibold text-slate-800 tracking-tight">智学引擎</span>
            <span className="block text-[10px] font-medium tracking-wider text-slate-400 uppercase">ZHIXUE ENGINE</span>
          </span>
        </div>

        <nav aria-label="主导航" className="flex-1 space-y-1 px-4 py-6">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = isNavigationActive(pathname, item.href)
            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium text-slate-500 transition-all hover:bg-slate-100/70 hover:text-primary active:scale-[0.98]",
                  isActive && "bg-blue-50/60 text-primary font-semibold shadow-sm shadow-blue-500/5",
                )}
                href={item.href}
                key={item.href}
              >
                <Icon aria-hidden="true" className={cn("h-4.5 w-4.5", isActive ? "text-primary" : "text-slate-400")} />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-slate-200/80 p-4 bg-slate-50/40">
          <div className="flex items-center gap-3 rounded-xl border border-slate-200/60 bg-white p-3 shadow-sm">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-550 bg-emerald-100 text-sm font-bold text-emerald-700 shadow-inner">
              {userId.slice(0, 1).toUpperCase()}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-slate-700">{userId}</span>
              <span className="block text-[10px] font-medium text-slate-400">学生账号</span>
            </span>
            <button
              aria-label="退出登录"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-400 transition hover:bg-rose-50 hover:border-rose-100 hover:text-rose-600 active:scale-95"
              onClick={handleLogout}
              title="退出登录"
              type="button"
            >
              <LogOut aria-hidden="true" className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      <div className="col-start-2 min-w-0">
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-slate-200/80 bg-white/80 px-8 backdrop-blur-md">
          <div>
            <p className="text-sm font-semibold text-slate-800 tracking-tight">
              {current?.label ?? "学习中心"}
            </p>
            <p className="mt-0.5 text-xs text-slate-400">多智能体个性化学习系统</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              aria-label="打开智能答疑"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-blue-200 hover:bg-blue-50/50 hover:text-primary active:scale-95"
              onClick={() => setQaOpen(true)}
              title="智能答疑"
              type="button"
            >
              <MessageCircleQuestion aria-hidden="true" className="h-4 w-4" />
            </button>
            <span className="inline-flex h-8 items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs font-medium text-slate-600 shadow-sm">
              <BookOpenText aria-hidden="true" className="h-3.5 w-3.5 text-slate-400" />
              {selectedCourseName ?? "课程未选择"}
            </span>
            {demoMode && !selectedCourseName ? (
              <span className="inline-flex h-8 items-center rounded-lg bg-amber-50 border border-amber-200/60 px-3 text-xs font-semibold text-amber-700 shadow-sm shadow-amber-500/5">
                演示模式
              </span>
            ) : null}
          </div>
        </header>
        <OfflineBanner />
        <main className="min-h-[calc(100vh-72px)] px-8 py-7 bg-slate-50/30">{children}</main>
      </div>
      <QaDrawer onOpenChange={setQaOpen} open={qaOpen} userId={userId} />
    </div>
  )
}
