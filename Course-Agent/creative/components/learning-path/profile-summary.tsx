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
    <section aria-label="学生画像摘要" className="border-y bg-white">
      <div className="grid grid-cols-6 divide-x">
        {fields.map((field) => {
          const value = profile?.[field.key]
          const text = Array.isArray(value) ? value.join("、") : value || "待采集"
          return (
            <div className="min-w-0 px-4 py-4" key={field.key}>
              <p className="text-[11px] text-[#7a8799]">{field.label}</p>
              <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#46556c]">{text}</p>
            </div>
          )
        })}
      </div>
    </section>
  )
}
