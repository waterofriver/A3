import { Download, ExternalLink } from "lucide-react"
import { ReactNode } from "react"

export function MediaCard({
  children,
  mediaUrl,
}: {
  children: ReactNode
  mediaUrl: string
}) {
  return (
    <div>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-950 shadow-md">{children}</div>
      <div className="mt-3 flex justify-end gap-2">
        <a
          aria-label="新窗口预览素材"
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm transition-all duration-150 hover:border-slate-300 hover:bg-slate-50 hover:text-primary active:scale-95"
          href={mediaUrl}
          rel="noreferrer"
          target="_blank"
          title="新窗口预览素材"
        >
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
        <a
          aria-label="下载素材"
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm transition-all duration-150 hover:border-slate-300 hover:bg-slate-50 hover:text-primary active:scale-95"
          download
          href={mediaUrl}
          title="下载素材"
        >
          <Download aria-hidden="true" className="h-4 w-4" />
        </a>
      </div>
    </div>
  )
}
