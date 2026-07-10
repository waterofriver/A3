import ReactMarkdown from "react-markdown"
import rehypeHighlight from "rehype-highlight"
import remarkGfm from "remark-gfm"

import { CodeBlock } from "@/components/resources/code-block"

export function MarkdownRenderer({ markdown }: { markdown: string }) {
  return (
    <div className="max-w-none text-sm leading-7 text-[#46556c] [&_a]:text-[#2457d6] [&_blockquote]:border-l-4 [&_blockquote]:border-[#c9d7ee] [&_blockquote]:pl-4 [&_code]:rounded [&_code]:bg-[#edf1f6] [&_code]:px-1 [&_h1]:mb-5 [&_h1]:text-2xl [&_h1]:font-semibold [&_h1]:text-[#182132] [&_h2]:mb-3 [&_h2]:mt-7 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-[#27344a] [&_h3]:mb-2 [&_h3]:mt-5 [&_h3]:font-semibold [&_li]:ml-5 [&_li]:list-disc [&_ol_li]:list-decimal [&_p]:my-3 [&_table]:my-5 [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:border-[#d8e0eb] [&_td]:p-2 [&_th]:border [&_th]:border-[#d8e0eb] [&_th]:bg-[#f3f6fa] [&_th]:p-2 [&_th]:text-left">
      <ReactMarkdown
        rehypePlugins={[rehypeHighlight]}
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ children }) => <>{children}</>,
          code: ({ children, className }) => {
            const language = /language-(\w+)/.exec(className ?? "")?.[1]
            const code = String(children).replace(/\n$/, "")
            return language ? (
              <CodeBlock code={code} language={language} />
            ) : (
              <code className={className}>{children}</code>
            )
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}
