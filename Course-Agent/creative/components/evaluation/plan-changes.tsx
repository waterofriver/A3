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
    <section aria-labelledby="plan-change-title" className="border-t pt-6">
      <div className="flex items-start justify-between gap-8">
        <div>
          <p className="text-xs font-semibold text-[#2457d6]">PLAN UPDATE</p>
          <h2 className="mt-2 text-lg font-semibold text-[#243149]" id="plan-change-title">
            学习计划优化建议
          </h2>
        </div>
        {applied ? (
          <span className="inline-flex h-10 items-center gap-2 rounded-md bg-[#eef7e4] px-4 text-sm font-semibold text-[#567820]">
            <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
            {appliedVersion ? `已更新至路径 v${appliedVersion}` : "学习计划已更新"}
          </span>
        ) : (
          <Button
            className="bg-[#2457d6] hover:bg-[#1d48b5]"
            disabled={isApplying || !changes.length}
            onClick={onApply}
            type="button"
          >
            {isApplying ? (
              <LoaderCircle aria-hidden="true" className="animate-spin" />
            ) : (
              <RefreshCw aria-hidden="true" />
            )}
            一键更新学习计划
          </Button>
        )}
      </div>

      {changes.length ? (
        <ol className="mt-5 divide-y border-y">
          {changes.map((change, index) => (
            <li className="grid grid-cols-[36px_minmax(220px,0.7fr)_32px_minmax(0,1.3fr)] items-center gap-3 py-4" key={`${change.stage_name}-${index}`}>
              <span className="text-xs font-semibold tabular-nums text-[#8b98aa]">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <p className="text-sm font-semibold text-[#344258]">{change.stage_name}</p>
                <p className="mt-1 text-xs text-[#7a8799]">难度 · {change.difficulty}</p>
              </div>
              <ArrowRight aria-hidden="true" className="h-4 w-4 text-[#9aa7b8]" />
              <p className="text-sm leading-6 text-[#66758b]">{change.reason}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p className="mt-5 border-y py-5 text-sm text-[#748196]">当前没有需要新增的路径节点。</p>
      )}
    </section>
  )
}
