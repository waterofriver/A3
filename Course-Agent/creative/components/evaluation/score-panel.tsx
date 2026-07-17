import { BookCheck, CodeXml } from "lucide-react"

function ScoreMetric({
  accent,
  label,
  score,
  summary,
  type,
}: {
  accent: string
  label: string
  score: number
  summary: string
  type: "theory" | "practice"
}) {
  const Icon = type === "theory" ? BookCheck : CodeXml
  const normalized = Math.max(0, Math.min(100, score))

  return (
    <article className="h-[164px] rounded-2xl border border-slate-200 bg-white p-5.5 shadow-sm hover:shadow hover:border-slate-300 transition-all duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</p>
          <div className="mt-2 flex items-baseline gap-1">
            <span className="text-4xl font-extrabold tracking-tight tabular-nums text-slate-800">
              {normalized}
            </span>
            <span className="text-xs font-semibold text-slate-400">/ 100</span>
          </div>
        </div>
        <span
          className="flex h-10 w-10 items-center justify-center rounded-xl shadow-inner border"
          style={{ 
            backgroundColor: `${accent}12`, 
            borderColor: `${accent}20`,
            color: accent 
          }}
        >
          <Icon aria-hidden="true" className="h-5 w-5" />
        </span>
      </div>
      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div
          aria-hidden="true"
          className="h-full rounded-full transition-[width] duration-500"
          style={{ backgroundColor: accent, width: `${normalized}%` }}
        />
      </div>
      <p className="mt-3 text-xs font-medium text-slate-400">{summary}</p>
    </article>
  )
}

export function ScorePanel({
  practiceScore,
  theoryScore,
}: {
  practiceScore: number
  theoryScore: number
}) {
  return (
    <section aria-label="学习评分" className="grid grid-cols-2 gap-4">
      <ScoreMetric
        accent="#3b82f6"
        label="理论掌握度"
        score={theoryScore}
        summary="依据已提交题库的平均得分"
        type="theory"
      />
      <ScoreMetric
        accent="#10b981"
        label="实操能力"
        score={practiceScore}
        summary="依据学习路径实操节点完成率"
        type="practice"
      />
    </section>
  )
}
