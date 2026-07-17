"use client"

import { DatabaseZap } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { DocumentPreview } from "@/components/knowledge/document-preview"
import { KnowledgeTree } from "@/components/knowledge/knowledge-tree"
import type { components } from "@/lib/api/generated"

type CourseBase = components["schemas"]["CourseBaseData"]

export function KnowledgePageContent({ course }: { course: CourseBase }) {
  const documents = useMemo(
    () => course.chapters.flatMap((chapter) => chapter.documents),
    [course.chapters],
  )
  const [selectedId, setSelectedId] = useState<string | undefined>(
    documents[0]?.id,
  )

  useEffect(() => {
    if (!documents.some((document) => document.id === selectedId)) {
      setSelectedId(documents[0]?.id)
    }
  }, [documents, selectedId])

  if (!course.content_ready || documents.length === 0) {
    return (
      <section className="mt-6 grid min-h-[480px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-white shadow-sm text-center">
        <div>
          <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-slate-50 border border-slate-100 text-slate-500 shadow-sm">
            <DatabaseZap aria-hidden="true" className="h-5 w-5" />
          </span>
          <h2 className="mt-4 text-base font-bold text-slate-700">课程资料未同步</h2>
          <p className="mt-2 text-sm text-slate-400">挂载真实课程文件后即可在此只读浏览。</p>
        </div>
      </section>
    )
  }

  const selected =
    documents.find((document) => document.id === selectedId) ?? documents[0]

  return (
    <section className="mt-6 grid min-h-[680px] grid-cols-[320px_minmax(0,1fr)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-r border-slate-200 bg-slate-50/40">
        <div className="flex h-[58px] items-center justify-between border-b border-slate-150 px-4 bg-slate-50/60">
          <h2 className="text-sm font-bold text-slate-700">课程目录</h2>
          <span className="text-xs font-semibold tabular-nums text-slate-400">{documents.length} 份文档</span>
        </div>
        <KnowledgeTree
          chapters={course.chapters}
          onSelect={setSelectedId}
          selectedId={selected.id}
        />
      </div>
      <DocumentPreview document={selected} />
    </section>
  )
}
