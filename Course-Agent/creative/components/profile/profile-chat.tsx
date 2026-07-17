"use client"

import { Bot, Send, UserRound } from "lucide-react"
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react"

export type ProfileMessage = {
  id: string
  role: "user" | "assistant"
  content: string
}

type ProfileChatProps = {
  messages: ProfileMessage[]
  isStreaming: boolean
  onSend: (message: string) => Promise<void>
}

export function ProfileChat({ messages, isStreaming, onSend }: ProfileChatProps) {
  const [input, setInput] = useState("")
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: "end" })
  }, [messages, isStreaming])

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const message = input.trim()
    if (!message || isStreaming) return
    setInput("")
    await onSend(message)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <section className="flex min-h-[620px] flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" aria-label="画像对话">
      <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-100 px-5 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-emerald-400 shadow-sm">
            <Bot aria-hidden="true" className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-slate-700">画像抽取 Agent</h2>
            <p className="mt-0.5 text-[10px] font-medium text-slate-400 uppercase tracking-wider">在线</p>
          </div>
        </div>
        <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50 animate-pulse" />
      </header>

      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto bg-slate-50/50 px-5 py-6">
        {messages.map((message) => {
          const isUser = message.role === "user"
          return (
            <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`} key={message.id}>
              {!isUser ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-primary shadow-sm">
                  <Bot aria-hidden="true" className="h-4 w-4" />
                </span>
              ) : null}
              <div
                className={`max-w-[76%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                  isUser
                    ? "bg-primary text-white rounded-tr-none"
                    : "border border-slate-200 bg-white text-slate-600 rounded-tl-none"
                }`}
              >
                {message.content || (
                  <span className="inline-flex items-center gap-1 text-slate-400">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:120ms]" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:240ms]" />
                  </span>
                )}
              </div>
              {isUser ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-100 border border-emerald-200 text-emerald-700 shadow-sm">
                  <UserRound aria-hidden="true" className="h-4 w-4" />
                </span>
              ) : null}
            </div>
          )
        })}
        <div ref={endRef} />
      </div>

      <form className="flex shrink-0 items-end gap-3 border-t border-slate-100 bg-white p-4" onSubmit={submit}>
        <textarea
          aria-label="画像对话输入"
          className="min-h-[48px] max-h-32 flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-3 text-sm leading-relaxed outline-none transition-all duration-200 hover:border-slate-300 focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
          disabled={isStreaming}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="介绍你的专业、基础或学习目标"
          rows={1}
          value={input}
        />
        <button
          aria-label="发送"
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-md shadow-primary/10 transition-all duration-200 hover:bg-blue-600 hover:shadow-lg hover:shadow-primary/20 hover:-translate-y-[0.5px] active:translate-y-0 active:scale-[0.95] disabled:cursor-not-allowed disabled:opacity-50 disabled:transform-none disabled:shadow-none"
          disabled={isStreaming || !input.trim()}
          title="发送"
          type="submit"
        >
          <Send aria-hidden="true" className="h-4.5 w-4.5" />
        </button>
      </form>
    </section>
  )
}
