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
      <section className="mt-6 grid min-h-[480px] place-items-center border border-dashed bg-white text-center">
        <div>
          <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-md bg-[#eef2f7] text-[#66758b]">
            <DatabaseZap aria-hidden="true" className="h-5 w-5" />
          </span>
          <h2 className="mt-4 text-base font-semibold text-[#344258]">课程资料未同步</h2>
          <p className="mt-2 text-sm text-[#748196]">挂载真实课程文件后即可在此只读浏览。</p>
        </div>
      </section>
    )
  }

  const selected =
    documents.find((document) => document.id === selectedId) ?? documents[0]

  return (
    <section className="mt-6 grid min-h-[680px] grid-cols-[320px_minmax(0,1fr)] overflow-hidden border bg-white">
      <div className="border-r bg-[#fbfcfe]">
        <div className="flex h-[58px] items-center justify-between border-b px-4">
          <h2 className="text-sm font-semibold text-[#344258]">课程目录</h2>
          <span className="text-xs tabular-nums text-[#8a97a8]">{documents.length} 份文档</span>
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
