"use client"

import { AlertTriangle } from "lucide-react"
import { Component, type ErrorInfo, type ReactNode } from "react"

type Props = {
  children: ReactNode
  traceId?: string
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

type State = { failed: boolean }

export class ResourceErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.props.onError?.(error, errorInfo)
  }

  render() {
    if (!this.state.failed) return this.props.children
    return (
      <div className="grid min-h-[320px] place-items-center border border-[#efc7c2] bg-[#fff7f5] text-center" role="alert">
        <div>
          <AlertTriangle aria-hidden="true" className="mx-auto h-7 w-7 text-[#c7463c]" />
          <p className="mt-3 text-sm font-semibold text-[#8d3029]">该资源暂时无法显示</p>
          <p className="mt-1 text-xs text-[#8f6965]">其他资源与学习记录不受影响。</p>
          {this.props.traceId ? (
            <p className="mt-2 text-xs text-[#9a6f6a]">追踪号：{this.props.traceId}</p>
          ) : null}
        </div>
      </div>
    )
  }
}
