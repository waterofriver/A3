"use client"

import { Check, Copy } from "lucide-react"
import { useState } from "react"

export function CodeBlock({
  code,
  language,
}: {
  code: string
  language: string
}) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    if (navigator.clipboard) await navigator.clipboard.writeText(code)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1200)
  }

  return (
    <div className="overflow-hidden rounded-md border border-[#26334a] bg-[#111827] text-[#dbe5f4]">
      <div className="flex h-10 items-center justify-between border-b border-white/10 bg-[#17243d] px-3">
        <span className="text-xs font-semibold text-[#d8ff72]">{language}</span>
        <button
          aria-label="复制代码"
          className="flex h-8 w-8 items-center justify-center rounded-md text-[#b8c4d5] hover:bg-white/10 hover:text-white"
          onClick={copy}
          title="复制代码"
          type="button"
        >
          {copied ? <Check aria-hidden="true" className="h-4 w-4" /> : <Copy aria-hidden="true" className="h-4 w-4" />}
        </button>
      </div>
      <pre className="max-h-[480px] overflow-auto p-4 text-sm leading-6">
        <code className={`language-${language}`}>{code}</code>
      </pre>
    </div>
  )
}
