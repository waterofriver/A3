import { ArrowRight, CheckCircle2, LoaderCircle, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"
import type { components } from "@/lib/api/generated"

type RecommendedChange = components["schemas"]["EvaluationRecommendedChange"]

export function PlanChanges({
  applied,
  appliedVersion,
  changes,
  isApplying,
  onApply,
}: {
  applied: boolean
  appliedVersion?: number
  changes: RecommendedChange[]
  isApplying: boolean
  onApply: () => void
}) {
  return (
    <section aria-labelledby="plan-change-title" className="border-t border-slate-200 pt-6">
      <div className="flex items-start justify-between gap-8">
        <div>
          <p className="text-[10px] font-bold text-primary uppercase tracking-wider">PLAN UPDATE</p>
          <h2 className="mt-1 text-lg font-bold tracking-tight text-slate-800" id="plan-change-title">
            学习计划优化建议
          </h2>
        </div>
        {applied ? (
          <span className="inline-flex h-10 items-center gap-2 rounded-full bg-emerald-50 border border-emerald-100/50 px-4 text-sm font-semibold text-emerald-700 shadow-sm shadow-emerald-500/5">
            <CheckCircle2 aria-hidden="true" className="h-4 w-4 text-emerald-600" />
            {appliedVersion ? `已更新至路径 v${appliedVersion}` : "学习计划已更新"}
          </span>
        ) : (
          <Button
            className="bg-primary hover:bg-blue-600 rounded-xl shadow-md shadow-primary/10 transition-all duration-200 hover:shadow-lg hover:shadow-primary/20 hover:-translate-y-[0.5px] active:translate-y-0 active:scale-[0.98]"
            disabled={isApplying || !changes.length}
            onClick={onApply}
            type="button"
          >
            {isApplying ? (
              <LoaderCircle aria-hidden="true" className="animate-spin h-4 w-4" />
            ) : (
              <RefreshCw aria-hidden="true" className="h-4 w-4" />
            )}
            一键更新学习计划
          </Button>
        )}
      </div>

      {changes.length ? (
        <ol className="mt-5 divide-y divide-slate-100 border-t border-b border-slate-100">
          {changes.map((change, index) => (
            <li className="grid grid-cols-[36px_minmax(220px,0.7fr)_32px_minmax(0,1.3fr)] items-center gap-3 py-4.5 px-3 rounded-xl transition hover:bg-slate-50/50" key={`${change.stage_name}-${index}`}>
              <span className="text-xs font-bold tabular-nums text-slate-400">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="text-sm font-bold text-slate-700">{change.stage_name}</p>
                <p className="mt-1.5 text-xs font-semibold text-slate-400">难度 · {change.difficulty}</p>
              </div>
              <ArrowRight aria-hidden="true" className="h-4 w-4 text-slate-300" />
              <p className="text-sm leading-relaxed text-slate-500">{change.reason}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-5 border-t border-b border-slate-100 py-6 text-sm font-medium text-slate-400">当前没有需要新增的路径节点。</p>
      )}
    </section>
  )
}
