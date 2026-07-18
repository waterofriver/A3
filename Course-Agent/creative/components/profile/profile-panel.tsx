import {
  BookOpenCheck,
  Brain,
  Gauge,
  ListChecks,
  Shapes,
  Target,
} from "lucide-react"

import type { components } from "@/lib/api/generated"

export type StudentProfile = components["schemas"]["StudentProfileData"]

export const EMPTY_PROFILE: StudentProfile = {
  knowledge_foundation: "待采集",
  cognitive_style: "待采集",
  weak_points: [],
  learning_pace: "待采集",
  content_preferences: [],
  short_term_goal: "待采集",
}

const dimensions = [
  {
    key: "knowledge_foundation",
    label: "知识基础",
    icon: BookOpenCheck,
    tone: "bg-blue-50 border border-blue-100 text-blue-600",
  },
  {
    key: "cognitive_style",
    label: "认知风格",
    icon: Brain,
    tone: "bg-emerald-50 border border-emerald-100 text-emerald-600",
  },
  {
    key: "weak_points",
    label: "薄弱知识点",
    icon: ListChecks,
    tone: "bg-rose-50 border border-rose-100 text-rose-600",
  },
  {
    key: "learning_pace",
    label: "学习节奏",
    icon: Gauge,
    tone: "bg-amber-50 border border-amber-100 text-amber-600",
  },
  {
    key: "content_preferences",
    label: "内容偏好",
    icon: Shapes,
    tone: "bg-lime-50 border border-lime-100 text-lime-600",
  },
  {
    key: "short_term_goal",
    label: "短期学习目标",
    icon: Target,
    tone: "bg-violet-50 border border-violet-100 text-violet-600",
  },
] as const

function ProfileValue({ value }: { value: string | string[] | undefined }) {
  if (Array.isArray(value)) {
    if (!value.length) return <span className="text-slate-400 font-medium">待采集</span>
    return (
      <div className="flex flex-wrap gap-1.5">
        {value.map((item) => (
          <span
            className="rounded-lg border border-slate-200 bg-slate-50/50 px-2.5 py-1 text-xs font-semibold text-slate-600"
            key={item}
          >
            {item}
          </span>
        ))}
      </div>
    )
  }
  return <span className={value === "待采集" ? "text-slate-400 font-medium" : "text-slate-600 font-medium"}>{value}</span>
}

export function ProfilePanel({ profile }: { profile: StudentProfile }) {
  return (
    <section aria-label="六维学生画像">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-700">实时学生画像</p>
          <p className="mt-0.5 text-xs text-slate-400">当前修订内容</p>
        </div>
        <span className="rounded-full bg-blue-50 border border-blue-100/60 px-3 py-0.5 text-xs font-semibold text-blue-600 shadow-sm shadow-blue-500/5">
          6 个维度
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        {dimensions.map((dimension) => {
          const Icon = dimension.icon
          return (
            <article className="min-h-[152px] rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:border-slate-300 hover:shadow" key={dimension.key}>
              <div className="flex items-center gap-3">
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${dimension.tone}`}>
                  <Icon aria-hidden="true" className="h-5 w-5" />
                </span>
                <h3 className="text-sm font-bold text-slate-700">{dimension.label}</h3>
              </div>
              <div className="mt-5 text-sm leading-relaxed">
                <ProfileValue value={profile[dimension.key]} />
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
