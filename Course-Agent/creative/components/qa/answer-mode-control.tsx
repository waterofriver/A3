"use client"

import { FileText, Image as ImageIcon, Video } from "lucide-react"

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"

export type AnswerMode = "text" | "image" | "video"

const modes = [
  { value: "text", label: "纯文字", icon: FileText },
  { value: "image", label: "图解配图", icon: ImageIcon },
  { value: "video", label: "短视频讲解", icon: Video },
] as const

export function AnswerModeControl({
  disabled,
  onValueChange,
  value,
}: {
  disabled?: boolean
  onValueChange: (value: AnswerMode) => void
  value: AnswerMode
}) {
  return (
    <RadioGroup
      aria-label="回答形式"
      className="grid grid-cols-3 gap-1 rounded-md bg-[#eef2f7] p-1"
      disabled={disabled}
      onValueChange={(nextValue) => onValueChange(nextValue as AnswerMode)}
      value={value}
    >
      {modes.map((mode) => {
        const Icon = mode.icon
        return (
          <RadioGroupItem
            aria-label={mode.label}
            className="flex h-9 w-auto aspect-auto items-center justify-center gap-1.5 rounded-md border-0 px-2 text-xs font-medium text-[#617086] shadow-none data-[state=checked]:bg-white data-[state=checked]:text-[#2457d6] data-[state=checked]:shadow-sm"
            key={mode.value}
            value={mode.value}
          >
            <Icon aria-hidden="true" className="h-3.5 w-3.5" />
            <span>{mode.label}</span>
          </RadioGroupItem>
        )
      })}
    </RadioGroup>
  )
}
