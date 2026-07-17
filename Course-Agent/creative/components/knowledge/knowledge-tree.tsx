"use client"

import { FileCode2, FileText, Image as ImageIcon, PlaySquare } from "lucide-react"
import { useEffect, useState } from "react"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import type { components } from "@/lib/api/generated"
import { cn } from "@/lib/utils"

type CourseChapter = components["schemas"]["CourseChapterData"]

const codeTypes = new Set([
  "c",
  "cpp",
  "go",
  "h",
  "hpp",
  "java",
  "js",
  "jsx",
  "ps1",
  "py",
  "rs",
  "sh",
  "ts",
  "tsx",
])

function DocumentIcon({ fileType }: { fileType: string }) {
  if (codeTypes.has(fileType)) return FileCode2
  if (["png", "jpg", "jpeg", "gif", "webp", "bmp"].includes(fileType)) {
    return ImageIcon
  }
  if (["mp4", "webm", "mov", "m4v"].includes(fileType)) return PlaySquare
  return FileText
}

export function KnowledgeTree({
  chapters,
  onSelect,
  selectedId,
}: {
  chapters: CourseChapter[]
  onSelect: (documentId: string) => void
  selectedId?: string
}) {
  const [openChapter, setOpenChapter] = useState(chapters[0]?.path ?? "")

  useEffect(() => {
    if (!chapters.some((chapter) => chapter.path === openChapter)) {
      setOpenChapter(chapters[0]?.path ?? "")
    }
  }, [chapters, openChapter])

  return (
    <nav aria-label="课程章节" className="h-full overflow-y-auto px-4 py-3">
      <Accordion
        className="w-full"
        collapsible
        onValueChange={setOpenChapter}
        type="single"
        value={openChapter}
      >
        {chapters.map((chapter) => (
          <AccordionItem key={chapter.path} value={chapter.path} className="border-b border-slate-100">
            <AccordionTrigger className="text-left text-sm font-bold text-slate-700 hover:text-primary hover:no-underline py-3">
              <span className="min-w-0 truncate">{chapter.name}</span>
            </AccordionTrigger>
            <AccordionContent className="space-y-1 pb-3">
              {chapter.documents.map((document) => {
                const Icon = DocumentIcon({ fileType: document.file_type })
                const isSelected = selectedId === document.id
                return (
                  <button
                    aria-current={isSelected ? "page" : undefined}
                    className={cn(
                      "flex min-h-10 w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs font-semibold text-slate-500 transition-all duration-150 hover:bg-slate-100/70 hover:text-primary active:scale-[0.98]",
                      isSelected && "bg-blue-50/60 font-bold text-primary shadow-sm shadow-blue-500/5",
                    )}
                    key={document.id}
                    onClick={() => onSelect(document.id)}
                    type="button"
                  >
                    <Icon aria-hidden="true" className={cn("h-3.5 w-3.5 shrink-0", isSelected ? "text-primary" : "text-slate-400")} />
                    <span className="min-w-0 flex-1 truncate">{document.filename}</span>
                    <span className="shrink-0 uppercase text-[9px] font-bold text-slate-400">
                      {document.file_type}
                    </span>
                  </button>
                )
              })}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </nav>
  )
}
