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
      <div className="overflow-hidden rounded-md border bg-[#111827]">{children}</div>
      <div className="mt-3 flex justify-end gap-2">
        <a
          aria-label="新窗口预览素材"
          className="flex h-9 w-9 items-center justify-center rounded-md border text-[#526279] hover:bg-[#f4f7fb] hover:text-[#2457d6]"
          href={mediaUrl}
          rel="noreferrer"
          target="_blank"
          title="新窗口预览素材"
        >
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
        <a
          aria-label="下载素材"
          className="flex h-9 w-9 items-center justify-center rounded-md border text-[#526279] hover:bg-[#f4f7fb] hover:text-[#2457d6]"
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
