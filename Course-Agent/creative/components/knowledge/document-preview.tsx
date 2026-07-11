"use client"

import { Download, FileSearch } from "lucide-react"

import { CodeBlock } from "@/components/resources/code-block"
import { MarkdownRenderer } from "@/components/resources/markdown-renderer"
import { VideoPlayer } from "@/components/resources/video-player"
import { resolveApiUrl } from "@/lib/api/client"
import type { components } from "@/lib/api/generated"

type CourseDocument = components["schemas"]["CourseDocumentData"]

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
const imageTypes = new Set(["bmp", "gif", "jpeg", "jpg", "png", "webp"])
const videoTypes = new Set(["m4v", "mov", "mp4", "webm"])

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function PreviewBody({ document }: { document: CourseDocument }) {
  const mediaUrl = document.media_url
    ? resolveApiUrl(document.media_url)
    : null

  if (document.file_type === "md" && document.preview_text) {
    return <MarkdownRenderer markdown={document.preview_text} />
  }
  if (codeTypes.has(document.file_type) && document.preview_text) {
    return <CodeBlock code={document.preview_text} language={document.file_type} />
  }
  if (document.file_type === "pdf" && mediaUrl) {
    return (
      <object
        aria-label={`${document.filename} PDF 预览`}
        className="h-[620px] w-full border bg-white"
        data={mediaUrl}
        type="application/pdf"
      >
        {document.preview_text ? (
          <pre className="whitespace-pre-wrap text-sm leading-7 text-[#46556c]">
            {document.preview_text}
          </pre>
        ) : null}
      </object>
    )
  }
  if (imageTypes.has(document.file_type) && mediaUrl) {
    return (
      <div className="grid min-h-[480px] place-items-center bg-[#eef2f6] p-4">
        {/* Course URLs are supplied by the local API at runtime. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          alt={document.filename}
          className="max-h-[640px] max-w-full object-contain"
          src={mediaUrl}
        />
      </div>
    )
  }
  if (videoTypes.has(document.file_type) && mediaUrl) {
    return <VideoPlayer src={mediaUrl} />
  }
  if (document.preview_text) {
    return (
      <pre className="max-h-[680px] overflow-auto whitespace-pre-wrap border bg-white p-6 text-sm leading-7 text-[#46556c]">
        {document.preview_text}
      </pre>
    )
  }
  return (
    <div className="grid min-h-[420px] place-items-center border border-dashed bg-white text-center">
      <div>
        <FileSearch aria-hidden="true" className="mx-auto h-7 w-7 text-[#98a4b4]" />
        <p className="mt-3 text-sm font-semibold text-[#4b596e]">暂无可提取的预览内容</p>
        <p className="mt-1 text-xs text-[#7a8799]">可通过右上角下载按钮查看原始文件。</p>
      </div>
    </div>
  )
}

export function DocumentPreview({ document }: { document: CourseDocument }) {
  const mediaUrl = document.media_url
    ? resolveApiUrl(document.media_url)
    : null

  return (
    <article className="min-w-0">
      <header className="flex min-h-[76px] items-center justify-between gap-5 border-b px-6 py-4">
        <div className="min-w-0">
          <h2 className="truncate text-base font-semibold text-[#253248]">
            {document.filename}
          </h2>
          <p className="mt-1 text-xs text-[#7b8899]">
            {document.file_type.toUpperCase()} · {formatBytes(document.size_bytes)} · SHA-256 {document.sha256.slice(0, 10)}
          </p>
        </div>
        {mediaUrl ? (
          <a
            aria-label="下载原始文档"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border text-[#59687e] transition hover:bg-[#edf3ff] hover:text-[#2457d6]"
            download={document.filename}
            href={mediaUrl}
            title="下载原始文档"
          >
            <Download aria-hidden="true" className="h-4 w-4" />
          </a>
        ) : null}
      </header>
      <div className="p-6">
        <PreviewBody document={document} />
      </div>
    </article>
  )
}
