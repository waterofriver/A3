"use client"

import { AlertTriangle, LoaderCircle } from "lucide-react"
import { useCallback, useEffect, useId, useRef, useState } from "react"

type MermaidDiagramProps = {
  code: string
}

type RenderState =
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "ready"; svg: string }

/**
 * Renders a Mermaid diagram from raw Mermaid syntax.
 *
 * Uses dynamic import to keep `mermaid` out of the initial bundle;
 * the diagram renders inside a scrollable container with a consistent
 * light theme that matches the app's design tokens.
 */
export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const rawId = useId()
  // Mermaid requires ids that start with a letter and contain no colons.
  const diagramId = `mermaid-${rawId.replace(/[^a-zA-Z0-9-]/g, "")}`
  const containerRef = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<RenderState>({ phase: "loading" })
  const renderedCodeRef = useRef<string | null>(null)

  const renderDiagram = useCallback(
    async (mermaidCode: string) => {
      if (renderedCodeRef.current === mermaidCode) return
      renderedCodeRef.current = mermaidCode
      setState({ phase: "loading" })

      try {
        const mermaid = await import("mermaid")

        mermaid.default.initialize({
          startOnLoad: false,
          theme: "neutral",
          themeVariables: {
            primaryColor: "#edf3ff",
            primaryTextColor: "#27344a",
            primaryBorderColor: "#2457d6",
            lineColor: "#7a8799",
            secondaryColor: "#f4f9ea",
            tertiaryColor: "#fff3d9",
            noteBkgColor: "#edf3ff",
            noteTextColor: "#27344a",
            fontSize: "14px",
          },
          flowchart: { useMaxWidth: true, htmlLabels: true },
          sequence: { useMaxWidth: true, mirrorActors: false },
        })

        const { svg } = await mermaid.default.render(diagramId, mermaidCode)
        setState({ phase: "ready", svg })
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "未知渲染错误"
        setState({ phase: "error", message })
      }
    },
    // diagramId is stable because rawId is stable per component instance.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [diagramId],
  )

  useEffect(() => {
    void renderDiagram(code)
  }, [code, renderDiagram])

  return (
    <div
      className="my-5 overflow-x-auto rounded-lg border border-[#d5dfef] bg-white"
      ref={containerRef}
    >
      {state.phase === "loading" ? (
        <div
          className="flex h-40 items-center justify-center gap-2.5 text-xs text-[#7a8799]"
          role="status"
        >
          <LoaderCircle
            aria-hidden="true"
            className="h-4 w-4 animate-spin"
          />
          正在生成图解
        </div>
      ) : state.phase === "error" ? (
        <div className="rounded-lg border border-[#f9d5c3] bg-[#fef8f5] p-4">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-[#c7463c]">
            <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5" />
            图解渲染失败
          </div>
          <p className="mb-2 text-xs leading-relaxed text-[#8b5a3c]">
            {state.message}
          </p>
          <details className="text-[11px] text-[#a08b7a]">
            <summary className="cursor-pointer">查看原始代码</summary>
            <pre className="mt-2 overflow-x-auto rounded bg-[#fdf0e8] p-2 text-[11px] leading-relaxed">
              {code}
            </pre>
          </details>
        </div>
      ) : (
        <div
          className="flex justify-center p-4 [&_svg]:max-w-full"
          dangerouslySetInnerHTML={{ __html: state.svg }}
        />
      )}
    </div>
  )
}
