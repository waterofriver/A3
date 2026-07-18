import { Braces, FileText, FolderOpen, Network, Video } from "lucide-react"
import Link from "next/link"

import { EmptyState } from "@/components/shared/empty-state"
import type { ResourceSummary, ResourceType } from "@/lib/api/resource-types"

const resourceMeta: Partial<
  Record<ResourceType, { label: string; icon: typeof FileText; tone: string }>
> = {
  handout: { label: "讲义文档", icon: FileText, tone: "bg-blue-50 border border-blue-100 text-blue-600" },
  mindmap: { label: "思维导图", icon: Network, tone: "bg-emerald-50 border border-emerald-100 text-emerald-600" },
  code: { label: "代码案例", icon: Braces, tone: "bg-violet-50 border border-violet-100 text-violet-600" },
  video: { label: "教学视频", icon: Video, tone: "bg-rose-50 border border-rose-100 text-rose-600" },
}

export function ResourceGrid({
  resources,
  isLoading = false,
}: {
  resources: ResourceSummary[]
  isLoading?: boolean
}) {
  return (
    <section aria-label="课程资源">
      <div className="flex h-11 items-center justify-between border-b border-slate-200">
        <div>
          <h2 className="text-sm font-semibold text-slate-700">课程资源</h2>
          <p className="mt-0.5 text-[11px] text-slate-400">历史结果直接从后端恢复</p>
        </div>
        <span className="text-xs font-semibold tabular-nums text-slate-400">{resources.length} 项</span>
      </div>

      {isLoading ? (
        <div className="grid min-h-[420px] place-items-center text-sm font-medium text-slate-400" role="status">
          正在读取资源历史
        </div>
      ) : resources.length ? (
        <div className="mt-4 grid grid-cols-2 gap-4">
          {resources.map((resource) => {
            const meta = resourceMeta[resource.resource_type]
            if (!meta) return null
            const Icon = meta.icon
            return (
              <article className="min-h-[166px] rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200" key={resource.id}>
                <div className="flex items-start justify-between gap-4">
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${meta.tone}`}>
                    <Icon aria-hidden="true" className="h-4.5 w-4.5" />
                  </span>
                  {resource.title.includes("演示资源") ? (
                    <span className="rounded-full bg-amber-50 border border-amber-200/60 px-2 py-0.5 text-[10px] font-semibold text-amber-700 shadow-sm">
                      演示模式
                    </span>
                  ) : null}
                </div>
                <p className="mt-4 text-xs font-semibold text-slate-400 tracking-wider uppercase">{meta.label}</p>
                <h3 className="mt-1 line-clamp-2 text-sm font-bold leading-relaxed text-slate-700">
                  {resource.title}
                </h3>
                <Link
                  aria-label={`查看${meta.label}：${resource.title}`}
                  className="mt-4 inline-flex text-xs font-bold text-primary hover:text-blue-600 active:scale-95 transition-all duration-150"
                  href={`/resources/${resource.id}`}
                >
                  查看资源
                </Link>
              </article>
            )
          })}
        </div>
      ) : (
        <EmptyState
          className="mt-4 min-h-[420px] border border-dashed border-slate-300 bg-white px-8 rounded-xl"
          description="选择资源类型并启动生成任务。"
          icon={FolderOpen}
          title="当前课程暂无资源"
        />
      )}
    </section>
  )
}
