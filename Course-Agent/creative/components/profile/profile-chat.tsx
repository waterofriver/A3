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
    <section className="flex min-h-[620px] flex-col overflow-hidden rounded-lg border bg-white" aria-label="画像对话">
      <header className="flex h-16 shrink-0 items-center justify-between border-b px-5">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#17243d] text-[#d8ff72]">
            <Bot aria-hidden="true" className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-[#27344a]">画像抽取 Agent</h2>
            <p className="mt-0.5 text-xs text-[#7a8799]">在线</p>
          </div>
        </div>
        <span className="h-2 w-2 rounded-full bg-[#79a936]" />
      </header>

      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto bg-[#f8fafc] px-5 py-6">
        {messages.map((message) => {
          const isUser = message.role === "user"
          return (
            <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`} key={message.id}>
              {!isUser ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border bg-white text-[#2457d6]">
                  <Bot aria-hidden="true" className="h-4 w-4" />
                </span>
              ) : null}
              <div
                className={`max-w-[76%] rounded-lg px-4 py-3 text-sm leading-6 ${
                  isUser
                    ? "bg-[#2457d6] text-white"
                    : "border bg-white text-[#46556c]"
                }`}
              >
                {message.content || (
                  <span className="inline-flex items-center gap-1 text-[#8290a4]">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:120ms]" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current [animation-delay:240ms]" />
                  </span>
                )}
              </div>
              {isUser ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[#d8ff72] text-[#17243d]">
                  <UserRound aria-hidden="true" className="h-4 w-4" />
                </span>
              ) : null}
            </div>
          )
        })}
        <div ref={endRef} />
      </div>

      <form className="flex shrink-0 items-end gap-3 border-t bg-white p-4" onSubmit={submit}>
        <textarea
          aria-label="画像对话输入"
          className="min-h-[48px] max-h-32 flex-1 resize-none rounded-md border border-[#cdd6e3] px-3 py-3 text-sm leading-5 outline-none transition focus:border-[#2457d6] focus:ring-4 focus:ring-[#2457d6]/10"
          disabled={isStreaming}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="介绍你的专业、基础或学习目标"
          rows={1}
          value={input}
        />
        <button
          aria-label="发送"
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-[#2457d6] text-white transition hover:bg-[#1d48b5] disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isStreaming || !input.trim()}
          title="发送"
          type="submit"
        >
          <Send aria-hidden="true" className="h-5 w-5" />
        </button>
      </form>
    </section>
  )
}
