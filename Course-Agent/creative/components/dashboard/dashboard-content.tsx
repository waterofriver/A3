"use client"

import {
  BarChart3,
  BookOpenText,
  Brain,
  CalendarCheck,
  Flame,
  Gauge,
  NotebookTabs,
  Route,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { useMemo } from "react"

import { cn } from "@/lib/utils"

// ── 类型（与后端 /api/dashboard 返回对齐）──

type DashboardProfile = {
  cognitive_style: string
  learning_pace: string
  short_term_goal: string
  profile_text: string
}

type DashboardPath = {
  total_nodes: number
  completed_nodes: number
  percent: number
  course_name: string
}

type DashboardQuiz = {
  total_attempts: number
  avg_score: number
}

type RecentResource = {
  id: string
  title: string
  resource_type: string
  created_at: string
}

type DashboardActivity = {
  total_events: number
  this_week_events: number
  streak_days: number
}

type WeakPoint = {
  name: string
  frequency: number
}

export type DashboardData = {
  user_id: string
  display_name: string | null
  profile: DashboardProfile
  path: DashboardPath
  quiz: DashboardQuiz
  recent_resources: RecentResource[]
  activity: DashboardActivity
  weak_points: WeakPoint[]
}

// ── 子组件 ──

const resourceLabels: Record<string, string> = {
  handout: "讲义",
  mindmap: "思维导图",
  quiz: "题库",
  code: "拓展阅读",
  video: "视频",
}

function ProgressRing({ pct, size = 96 }: { pct: number; size?: number }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct / 100)
  const color = pct >= 80 ? "#55741f" : pct >= 40 ? "#2457d6" : "#8a5b05"
  return (
    <svg
      aria-label={`学习路径完成 ${pct}%`}
      className="shrink-0"
      height={size}
      role="img"
      width={size}
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        fill="none"
        r={r}
        stroke="#e6edf6"
        strokeWidth="8"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        fill="none"
        r={r}
        stroke={color}
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        strokeWidth="8"
        style={{ transition: "stroke-dashoffset 0.6s ease" }}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        dominantBaseline="central"
        fill="#182132"
        fontSize="22"
        fontWeight="700"
        textAnchor="middle"
        x="50%"
        y="50%"
      >
        {pct}%
      </text>
    </svg>
  )
}

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  colorClass = "bg-[#edf3ff] text-[#2457d6]",
}: {
  label: string
  value: string | number
  sub?: string
  icon: React.ElementType
  colorClass?: string
}) {
  return (
    <article className="flex items-start gap-4 rounded-lg border bg-white p-4">
      <span className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-md", colorClass)}>
        <Icon aria-hidden={true} className="h-5 w-5" />
      </span>
      <div className="min-w-0">
        <p className="text-xs text-[#7a8799]">{label}</p>
        <p className="mt-1 text-xl font-bold text-[#182132]">{value}</p>
        {sub ? <p className="mt-0.5 text-xs text-[#96a2b1]">{sub}</p> : null}
      </div>
    </article>
  )
}

// ── 主组件 ──

export function DashboardContent({ data }: { data: DashboardData }) {
  const displayName = data.display_name || data.user_id

  const recentTimeLabels = useMemo(() => {
    return data.recent_resources.map((r) => {
      try {
        const d = new Date(r.created_at)
        const now = new Date()
        const diffH = Math.round((now.getTime() - d.getTime()) / 3600000)
        if (diffH < 1) return "刚刚"
        if (diffH < 24) return `${diffH}h前`
        return `${Math.round(diffH / 24)}d前`
      } catch {
        return ""
      }
    })
  }, [data.recent_resources])

  return (
    <div className="mx-auto w-full max-w-[1380px] space-y-6">
      {/* ── 欢迎横幅 ── */}
      <header className="flex flex-wrap items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">DASHBOARD</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">
            欢迎回来，{displayName}
          </h1>
        </div>
        <div className="flex items-center gap-3 text-xs text-[#7a8799]">
          {data.activity.streak_days > 0 ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#fff3d9] px-3 py-1.5 font-semibold text-[#9a6706]">
              <Flame aria-hidden={true} className="h-3.5 w-3.5" />
              连续学习 {data.activity.streak_days} 天
            </span>
          ) : null}
          <span className="inline-flex items-center gap-1.5 rounded-full bg-[#edf3ff] px-3 py-1.5 font-semibold text-[#2457d6]">
            <CalendarCheck aria-hidden={true} className="h-3.5 w-3.5" />
            本周 {data.activity.this_week_events} 次活动
          </span>
        </div>
      </header>

      {/* ── 第一行：数据概览卡片 ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href="/path" className="group">
          <StatCard
            colorClass="bg-[#edf3ff] text-[#2457d6] group-hover:bg-[#dce6fa]"
            icon={Route}
            label="学习路径进度"
            sub={data.path.total_nodes > 0 ? `${data.path.completed_nodes}/${data.path.total_nodes} 节点 · ${data.path.course_name}` : "尚未生成"}
            value={data.path.total_nodes > 0 ? `${data.path.percent}%` : "—"}
          />
        </Link>

        <Link href="/evaluation" className="group">
          <StatCard
            colorClass="bg-[#e8f7f3] text-[#237964] group-hover:bg-[#d2f0e8]"
            icon={TrendingUp}
            label="题库平均分"
            sub={data.quiz.total_attempts > 0 ? `${data.quiz.total_attempts} 次测验` : "暂无测验记录"}
            value={data.quiz.total_attempts > 0 ? `${data.quiz.avg_score}分` : "—"}
          />
        </Link>

        <Link href="/workspace" className="group">
          <StatCard
            colorClass="bg-[#f4f0fb] text-[#6553a1] group-hover:bg-[#e8e1f5]"
            icon={Sparkles}
            label="生成资源数"
            sub="前往资源工作台"
            value={data.recent_resources.length > 0 ? data.recent_resources.length : "—"}
          />
        </Link>

        <Link href="/profile" className="group">
          <StatCard
            colorClass="bg-[#fff0ed] text-[#bd4d43] group-hover:bg-[#fde4df]"
            icon={Brain}
            label="薄弱知识点"
            sub={data.weak_points.length > 0 ? `${data.weak_points.length} 项待强化` : "暂无记录"}
            value={data.weak_points.length || "—"}
          />
        </Link>
      </div>

      {/* ── 第二行：画像 + 路径环 + 薄弱点 ── */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_200px_1fr]">
        {/* 画像摘要 */}
        <section className="rounded-lg border bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#edf3ff] text-[#2457d6]">
              <BookOpenText aria-hidden={true} className="h-3.5 w-3.5" />
            </span>
            <h2 className="text-sm font-semibold text-[#27344a]">学习画像</h2>
          </div>
          {data.profile.profile_text && data.profile.profile_text !== "画像待采集" ? (
            <div className="space-y-2.5">
              <ProfileRow icon={Brain} label="认知风格" value={data.profile.cognitive_style} />
              <ProfileRow icon={Gauge} label="学习节奏" value={data.profile.learning_pace} />
              {data.profile.short_term_goal ? (
                <ProfileRow icon={Target} label="短期目标" value={data.profile.short_term_goal} />
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-[#98a3b3]">
              尚未采集学习画像，
              <Link className="font-semibold text-[#2457d6] underline" href="/profile">去采集 →</Link>
            </p>
          )}
        </section>

        {/* 路径进度环 */}
        <div className="flex flex-col items-center justify-center rounded-lg border bg-white p-5">
          <ProgressRing pct={data.path.percent} />
          <p className="mt-3 text-center text-xs text-[#7a8799]">
            {data.path.course_name}
          </p>
        </div>

        {/* 薄弱点 */}
        <section className="rounded-lg border bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#fff0ed] text-[#bd4d43]">
              <BarChart3 aria-hidden={true} className="h-3.5 w-3.5" />
            </span>
            <h2 className="text-sm font-semibold text-[#27344a]">待强化知识点</h2>
          </div>
          {data.weak_points.length > 0 ? (
            <ul className="space-y-2">
              {data.weak_points.map((wp) => (
                <li
                  className="flex items-center justify-between rounded-md bg-[#fef8f5] px-3 py-2 text-sm"
                  key={wp.name}
                >
                  <span className="font-medium text-[#6b3a2e] truncate">{wp.name}</span>
                  <span className="ml-2 shrink-0 rounded bg-[#f9e0d0] px-2 py-0.5 text-xs font-semibold text-[#a85532]">
                    ×{wp.frequency}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[#98a3b3]">
              暂无薄弱点记录，
              <Link className="font-semibold text-[#2457d6] underline" href="/evaluation">去评估 →</Link>
            </p>
          )}
        </section>
      </div>

      {/* ── 第三行：最近资源 ── */}
      <section className="rounded-lg border bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-[#f4f9ea] text-[#55741f]">
              <NotebookTabs aria-hidden={true} className="h-3.5 w-3.5" />
            </span>
            <h2 className="text-sm font-semibold text-[#27344a]">最近学习资源</h2>
          </div>
          <Link
            className="text-xs font-semibold text-[#2457d6] hover:underline"
            href="/workspace"
          >
            查看全部 →
          </Link>
        </div>
        {data.recent_resources.length > 0 ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {data.recent_resources.map((r, i) => (
              <Link
                className="flex items-center gap-3 rounded-md border p-3 transition hover:bg-[#f8fafc] hover:border-[#b5c8ed]"
                href={`/resources/${r.id}`}
                key={r.id}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#edf3ff] text-[11px] font-bold text-[#2457d6]">
                  {resourceLabels[r.resource_type]?.charAt(0) || "?"}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-[#344258]">{r.title}</p>
                  <p className="text-xs text-[#96a2b1]">
                    {resourceLabels[r.resource_type] || r.resource_type}
                    {" · "}
                    {recentTimeLabels[i]}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-sm text-[#98a3b3]">
            尚未生成学习资源，
            <Link className="font-semibold text-[#2457d6] underline" href="/workspace">去生成 →</Link>
          </p>
        )}
      </section>
    </div>
  )
}

function ProfileRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-2.5 text-sm">
      <Icon aria-hidden={true} className="h-3.5 w-3.5 shrink-0 text-[#7a8799]" />
      <span className="shrink-0 text-[#7a8799]">{label}</span>
      <span className="font-medium text-[#27344a] truncate">{value}</span>
    </div>
  )
}
