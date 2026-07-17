import type { StudentProfile } from "@/components/profile/profile-panel"

const fields: { key: keyof StudentProfile; label: string }[] = [
  { key: "knowledge_foundation", label: "知识基础" },
  { key: "cognitive_style", label: "认知风格" },
  { key: "weak_points", label: "薄弱知识点" },
  { key: "learning_pace", label: "学习节奏" },
  { key: "content_preferences", label: "内容偏好" },
  { key: "short_term_goal", label: "短期目标" },
]

export function ProfileSummary({ profile }: { profile: StudentProfile | null }) {
  return (
    <section aria-label="学生画像摘要" className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div className="grid grid-cols-6 divide-x divide-slate-100">
        {fields.map((field) => {
          const value = profile?.[field.key]
          const text = Array.isArray(value) ? value.join("、") : value || "待采集"
          return (
            <div className="min-w-0 px-4 py-3.5 bg-white transition hover:bg-slate-50/50" key={field.key}>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{field.label}</p>
              <p className="mt-1 line-clamp-2 text-xs font-semibold leading-relaxed text-slate-600">{text}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
