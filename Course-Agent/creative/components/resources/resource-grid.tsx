import { Braces, FileText, ListChecks, Network, Video } from "lucide-react"
import Link from "next/link"

import type { ResourceSummary, ResourceType } from "@/lib/api/resource-types"

const resourceMeta: Record<
  ResourceType,
  { label: string; icon: typeof FileText; tone: string }
> = {
  handout: { label: "讲义文档", icon: FileText, tone: "bg-[#edf3ff] text-[#2457d6]" },
  mindmap: { label: "思维导图", icon: Network, tone: "bg-[#e7f5f1] text-[#237964]" },
  quiz: { label: "习题题库", icon: ListChecks, tone: "bg-[#fff3d9] text-[#946405]" },
  code: { label: "代码案例", icon: Braces, tone: "bg-[#f1eefb] text-[#6553a1]" },
  video: { label: "教学视频", icon: Video, tone: "bg-[#fff0ed] text-[#bd4d43]" },
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
      <div className="flex h-11 items-center justify-between border-b">
        <div>
          <h2 className="text-sm font-semibold text-[#27344a]">课程资源</h2>
          <p className="mt-0.5 text-[11px] text-[#7a8799]">历史结果直接从后端恢复</p>
        </div>
        <span className="text-xs tabular-nums text-[#718096]">{resources.length} 项</span>
      </div>

      {isLoading ? (
        <div className="grid min-h-[420px] place-items-center text-sm text-[#718096]" role="status">
          正在读取资源历史
        </div>
      ) : resources.length ? (
        <div className="mt-4 grid grid-cols-2 gap-4">
          {resources.map((resource) => {
            const meta = resourceMeta[resource.resource_type]
            const Icon = meta.icon
            return (
              <article className="min-h-[166px] rounded-lg border bg-white p-5" key={resource.id}>
                <div className="flex items-start justify-between gap-4">
                  <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${meta.tone}`}>
                    <Icon aria-hidden="true" className="h-4 w-4" />
                  </span>
                  {resource.title.includes("演示资源") ? (
                    <span className="rounded-md bg-[#fff3d9] px-2 py-1 text-[10px] font-semibold text-[#8a5b05]">
                      演示模式
                    </span>
                  ) : null}
                </div>
                <p className="mt-4 text-xs font-medium text-[#718096]">{meta.label}</p>
                <h3 className="mt-1 line-clamp-2 text-sm font-semibold leading-6 text-[#27344a]">
                  {resource.title}
                </h3>
                <Link
                  className="mt-4 inline-flex text-xs font-semibold text-[#2457d6] hover:text-[#183fa0]"
                  href={`/resources/${resource.id}`}
                >
                  查看资源
                </Link>
              </article>
            )
          })}
        </div>
      ) : (
        <div className="mt-4 grid min-h-[420px] place-items-center border border-dashed border-[#cbd5e3] bg-white px-8 text-center">
          <div>
            <p className="text-sm font-semibold text-[#344158]">当前课程暂无资源</p>
            <p className="mt-2 text-xs leading-5 text-[#7a8799]">选择需要的资源类型并启动多 Agent 任务。</p>
          </div>
        </div>
      )}
    </section>
  )
}
