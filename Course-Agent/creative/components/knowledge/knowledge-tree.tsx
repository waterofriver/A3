"use client"

import { FileCode2, FileText, Image as ImageIcon, PlaySquare } from "lucide-react"

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
  return (
    <nav aria-label="课程章节" className="h-full overflow-y-auto px-4 py-3">
      <Accordion
        className="w-full"
        defaultValue={chapters.map((chapter) => chapter.path)}
        type="multiple"
      >
        {chapters.map((chapter) => (
          <AccordionItem key={chapter.path} value={chapter.path}>
            <AccordionTrigger className="text-left text-sm font-semibold text-[#344258] hover:no-underline">
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
                      "flex min-h-10 w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-xs text-[#66758b] transition hover:bg-[#f0f4fb] hover:text-[#2457d6]",
                      isSelected && "bg-[#edf3ff] font-semibold text-[#2457d6]",
                    )}
                    key={document.id}
                    onClick={() => onSelect(document.id)}
                    type="button"
                  >
                    <Icon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
                    <span className="min-w-0 flex-1 truncate">{document.filename}</span>
                    <span className="shrink-0 uppercase text-[10px] text-[#99a5b5]">
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
