"use client"

import { Copy, Download, Film, NotebookTabs } from "lucide-react"

import { CodeBlock } from "@/components/resources/code-block"
import { MarkdownRenderer } from "@/components/resources/markdown-renderer"
import { MediaCard } from "@/components/resources/media-card"
import { MindMapViewer } from "@/components/resources/mind-map-viewer"
import { QuizPlayer } from "@/components/resources/quiz-player"
import { VideoPlayer } from "@/components/resources/video-player"
import { resolveApiUrl } from "@/lib/api/client"
import type { ResourceDetail, ResourceType } from "@/lib/api/resource-types"
import { getUserId } from "@/lib/session/user-session"

const labels: Record<ResourceType, string> = {
  handout: "讲义文档",
  mindmap: "思维导图",
  quiz: "习题题库",
  code: "拓展阅读",
  video: "教学图文视频",
}

function downloadText(filename: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "text/markdown;charset=utf-8" }))
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

function ResourceBody({ resource }: { resource: ResourceDetail }) {
  if (resource.resource_type === "handout") {
    return <MarkdownRenderer markdown={resource.payload.markdown} />
  }
  if (resource.resource_type === "code") {
    return (
      <div>
        <p className="mb-4 text-sm leading-6 text-[#59677d]">{resource.payload.description}</p>
        <CodeBlock code={resource.payload.code} language={resource.payload.language} />
      </div>
    )
  }
  if (resource.resource_type === "video") {
    return resource.media_url ? (
      <MediaCard mediaUrl={resolveApiUrl(resource.media_url)}>
        <VideoPlayer poster={resource.payload.poster_url} src={resolveApiUrl(resource.media_url)} />
      </MediaCard>
    ) : (
      <div className="grid min-h-[280px] place-items-center border border-dashed border-[#cbd5e3] bg-[#f8fafc] text-center">
        <div>
          <Film aria-hidden="true" className="mx-auto h-7 w-7 text-[#98a3b3]" />
          <p className="mt-3 text-sm font-semibold text-[#46556c]">等待 Agent 返回视频素材</p>
          <p className="mt-1 max-w-sm text-xs leading-5 text-[#7a8799]">{resource.payload.summary}</p>
        </div>
      </div>
    )
  }
  if (resource.resource_type === "mindmap") {
    return <MindMapViewer nodes={resource.payload.nodes} />
  }
  return <QuizPlayer resource={resource} userId={getUserId() ?? ""} />
}

export function ResourceCard({ resource }: { resource: ResourceDetail }) {
  const copyContent = async () => {
    const content =
      resource.resource_type === "handout"
        ? resource.payload.markdown
        : resource.resource_type === "code"
          ? resource.payload.code
          : JSON.stringify(resource.payload, null, 2)
    if (navigator.clipboard) await navigator.clipboard.writeText(content)
  }

  return (
    <article className="rounded-lg border bg-white">
      <header className="flex items-start justify-between gap-5 border-b px-6 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <NotebookTabs aria-hidden="true" className="h-4 w-4 text-[#2457d6]" />
            <span className="text-xs font-semibold text-[#2457d6]">{labels[resource.resource_type]}</span>
          </div>
          <h2 className="mt-2 text-lg font-semibold text-[#182132]">{resource.title}</h2>
        </div>
        {resource.resource_type === "handout" ? (
          <div className="flex shrink-0 gap-2">
            <button
              aria-label="复制内容"
              className="flex h-9 w-9 items-center justify-center rounded-md border text-[#526279] hover:bg-[#f4f7fb] hover:text-[#2457d6]"
              onClick={copyContent}
              title="复制内容"
              type="button"
            >
              <Copy aria-hidden="true" className="h-4 w-4" />
            </button>
            <button
              aria-label="下载文档"
              className="flex h-9 w-9 items-center justify-center rounded-md border text-[#526279] hover:bg-[#f4f7fb] hover:text-[#2457d6]"
              onClick={() =>
                downloadText(`${resource.title}.md`, resource.payload.markdown)
              }
              title="下载文档"
              type="button"
            >
              <Download aria-hidden="true" className="h-4 w-4" />
            </button>
          </div>
        ) : null}
      </header>
      <div className="p-6">
        <ResourceBody resource={resource} />
      </div>
    </article>
  )
}
