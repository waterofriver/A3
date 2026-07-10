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
    tone: "bg-[#edf3ff] text-[#2457d6]",
  },
  {
    key: "cognitive_style",
    label: "认知风格",
    icon: Brain,
    tone: "bg-[#e8f7f3] text-[#237964]",
  },
  {
    key: "weak_points",
    label: "薄弱知识点",
    icon: ListChecks,
    tone: "bg-[#fff0ed] text-[#bd4d43]",
  },
  {
    key: "learning_pace",
    label: "学习节奏",
    icon: Gauge,
    tone: "bg-[#fff5d9] text-[#9a6706]",
  },
  {
    key: "content_preferences",
    label: "内容偏好",
    icon: Shapes,
    tone: "bg-[#eef6da] text-[#55741f]",
  },
  {
    key: "short_term_goal",
    label: "短期学习目标",
    icon: Target,
    tone: "bg-[#f1eefb] text-[#6553a1]",
  },
] as const

function ProfileValue({ value }: { value: string | string[] | undefined }) {
  if (Array.isArray(value)) {
    if (!value.length) return <span className="text-[#98a3b3]">待采集</span>
    return (
      <div className="flex flex-wrap gap-1.5">
        {value.map((item) => (
          <span
            className="rounded-md border bg-[#f8fafc] px-2 py-1 text-xs text-[#526279]"
            key={item}
          >
            {item}
          </span>
        ))}
      </div>
    )
  }
  return <span className={value === "待采集" ? "text-[#98a3b3]" : "text-[#46556c]"}>{value}</span>
}

export function ProfilePanel({ profile }: { profile: StudentProfile }) {
  return (
    <section aria-label="六维学生画像">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-[#27344a]">实时学生画像</p>
          <p className="mt-1 text-xs text-[#7a8799]">当前修订内容</p>
        </div>
        <span className="rounded-md bg-[#edf3ff] px-2.5 py-1 text-xs font-semibold text-[#2457d6]">
          6 个维度
        </span>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        {dimensions.map((dimension) => {
          const Icon = dimension.icon
          return (
            <article className="min-h-[142px] rounded-lg border bg-white p-4" key={dimension.key}>
              <div className="flex items-center gap-2.5">
                <span className={`flex h-8 w-8 items-center justify-center rounded-md ${dimension.tone}`}>
                  <Icon aria-hidden="true" className="h-4 w-4" />
                </span>
                <h3 className="text-sm font-semibold text-[#27344a]">{dimension.label}</h3>
              </div>
              <div className="mt-4 text-sm leading-6">
                <ProfileValue value={profile[dimension.key]} />
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
