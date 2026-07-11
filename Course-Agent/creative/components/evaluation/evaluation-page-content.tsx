import { BarChart3 } from "lucide-react"

import { PlanChanges } from "@/components/evaluation/plan-changes"
import { ScorePanel } from "@/components/evaluation/score-panel"
import { WeaknessChart } from "@/components/evaluation/weakness-chart"
import type { components } from "@/lib/api/generated"

type EvaluationReport = components["schemas"]["EvaluationReportData"]

export function EvaluationPageContent({
  appliedVersion,
  isApplying,
  onApply,
  report,
}: {
  appliedVersion?: number
  isApplying: boolean
  onApply: (reportId: string) => void
  report: EvaluationReport | null
}) {
  if (!report) {
    return (
      <section className="mt-6 grid min-h-[440px] place-items-center border border-dashed bg-white text-center">
        <div>
          <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-md bg-[#eef2f7] text-[#66758b]">
            <BarChart3 aria-hidden="true" className="h-5 w-5" />
          </span>
          <h2 className="mt-4 text-base font-semibold text-[#344258]">评估数据不足</h2>
          <p className="mt-2 text-sm text-[#748196]">完成题库或实操路径节点后生成评估报告。</p>
        </div>
      </section>
    )
  }

  return (
    <div className="mt-6 space-y-8">
      <ScorePanel
        practiceScore={report.practice_score}
        theoryScore={report.theory_score}
      />

      <section aria-labelledby="weakness-title">
        <div className="mb-4 flex items-end justify-between border-b pb-3">
          <div>
            <p className="text-xs font-semibold text-[#2457d6]">WEAKNESS SIGNALS</p>
            <h2 className="mt-2 text-lg font-semibold text-[#243149]" id="weakness-title">
              薄弱知识点统计
            </h2>
          </div>
          <span className="text-xs text-[#7a8799]">按学习证据出现频次排序</span>
        </div>
        <WeaknessChart weakPoints={report.weak_points} />
      </section>

      <PlanChanges
        applied={Boolean(report.applied_path_id)}
        appliedVersion={appliedVersion}
        changes={report.recommended_changes}
        isApplying={isApplying}
        onApply={() => onApply(report.id)}
      />
    </div>
  )
}
