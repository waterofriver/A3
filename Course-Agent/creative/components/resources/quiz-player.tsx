"use client"

import { CheckCircle2, LoaderCircle, Send, XCircle } from "lucide-react"
import { FormEvent, useState } from "react"

import { ApiError, apiFetch } from "@/lib/api/client"
import type { QuizResourceDetail } from "@/lib/api/resource-types"

type QuizResult = {
  question_id: string
  correct: boolean
  submitted_answer: string
  expected_answer: string
  explanation: string
}

type QuizSubmitData = {
  attempt_id: string
  score: number
  results: QuizResult[]
}

type QuizPlayerProps = {
  resource: QuizResourceDetail
  userId: string
  submitQuiz?: (answers: Record<string, string>) => Promise<QuizSubmitData>
}

export function QuizPlayer({ resource, userId, submitQuiz }: QuizPlayerProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<QuizSubmitData | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState("")

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)
    setError("")
    try {
      const data = submitQuiz
        ? await submitQuiz(answers)
        : await apiFetch<QuizSubmitData>("/api/quiz/submit", {
            method: "POST",
            body: JSON.stringify({
              user_id: userId,
              resource_id: resource.id,
              answers,
            }),
          })
      setResult(data)
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : "答案提交失败，请稍后重试。",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form className="space-y-6" onSubmit={submit}>
      {resource.payload.questions.map((question, index) => {
        const questionResult = result?.results.find(
          (item) => item.question_id === question.id,
        )
        return (
          <fieldset className="border-b pb-6" key={question.id}>
            <legend className="text-sm font-semibold leading-6 text-[#344158]">
              {index + 1}. {question.prompt}
            </legend>
            {question.question_type === "choice" ? (
              <div className="mt-3 grid grid-cols-2 gap-2">
                {question.options.map((option) => {
                  // 提取选项前缀字母（"A. xxx" → "A"）
                  const letter = option.match(/^([A-Z]+)[.\s、]/)?.[1] || option
                  // 多选题用 checkbox，单选题用 radio
                  const isMulti = question.answer.length > 1 && /^[A-Z]+$/.test(question.answer)

                  const currentAnswers = (answers[question.id] || "").split("")
                  const isChecked = isMulti
                    ? currentAnswers.includes(letter)
                    : answers[question.id] === letter

                  const handleChange = () => {
                    setAnswers((current) => {
                      if (isMulti) {
                        const prev = (current[question.id] || "").split("").filter(Boolean)
                        const next = prev.includes(letter)
                          ? prev.filter((l) => l !== letter)
                          : [...prev, letter]
                        return { ...current, [question.id]: next.sort().join("") }
                      }
                      return { ...current, [question.id]: letter }
                    })
                  }

                  return (
                    <label
                      className="flex min-h-10 cursor-pointer items-center gap-3 rounded-md border px-3 text-sm text-[#526279] has-[:checked]:border-[#2457d6] has-[:checked]:bg-[#edf3ff]"
                      key={option}
                    >
                      <input
                        checked={isChecked}
                        disabled={isSubmitting || Boolean(result)}
                        name={question.id}
                        onChange={handleChange}
                        type={isMulti ? "checkbox" : "radio"}
                      />
                      {option}
                    </label>
                  )
                })}
              </div>
            ) : question.question_type === "blank" ? (
              <div className="mt-3">
                <label className="sr-only" htmlFor={`answer-${question.id}`}>
                  {question.prompt}
                </label>
                <input
                  className="h-11 w-full rounded-md border border-[#cdd6e3] px-3 text-sm outline-none focus:border-[#2457d6] focus:ring-4 focus:ring-[#2457d6]/10"
                  disabled={isSubmitting || Boolean(result)}
                  id={`answer-${question.id}`}
                  onChange={(event) =>
                    setAnswers((current) => ({
                      ...current,
                      [question.id]: event.target.value,
                    }))
                  }
                  value={answers[question.id] ?? ""}
                />
              </div>
            ) : (
              <div className="mt-3">
                <label className="sr-only" htmlFor={`answer-${question.id}`}>
                  {question.prompt}
                </label>
                <textarea
                  className="min-h-28 w-full resize-y rounded-md border border-[#cdd6e3] p-3 font-mono text-sm outline-none focus:border-[#2457d6] focus:ring-4 focus:ring-[#2457d6]/10"
                  disabled={isSubmitting || Boolean(result)}
                  id={`answer-${question.id}`}
                  onChange={(event) =>
                    setAnswers((current) => ({
                      ...current,
                      [question.id]: event.target.value,
                    }))
                  }
                  value={answers[question.id] ?? ""}
                />
              </div>
            )}

            {questionResult ? (
              <div
                className={`mt-4 flex items-start gap-3 rounded-md border p-3 ${
                  questionResult.correct
                    ? "border-[#c9dda9] bg-[#f4f9ea]"
                    : "border-[#efc7c2] bg-[#fff7f5]"
                }`}
              >
                {questionResult.correct ? (
                  <CheckCircle2 aria-hidden="true" className="mt-0.5 h-4 w-4 text-[#648d28]" />
                ) : (
                  <XCircle aria-hidden="true" className="mt-0.5 h-4 w-4 text-[#c7463c]" />
                )}
                <div>
                  <p className="text-xs font-semibold text-[#46556c]">
                    {questionResult.correct ? "回答正确" : `正确答案：${questionResult.expected_answer}`}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-[#66758c]">
                    {questionResult.explanation}
                  </p>
                </div>
              </div>
            ) : null}
          </fieldset>
        )
      })}

      <div className="flex items-center justify-between">
        <div aria-live="polite">
          {result ? (
            <p className="text-lg font-semibold text-[#2457d6]">得分 {result.score}</p>
          ) : error ? (
            <p className="text-sm text-[#c7463c]">{error}</p>
          ) : null}
        </div>
        <button
          className="inline-flex h-11 items-center gap-2 rounded-md bg-[#2457d6] px-5 text-sm font-semibold text-white hover:bg-[#1d48b5] disabled:cursor-not-allowed disabled:opacity-50"
          disabled={isSubmitting || Boolean(result)}
          type="submit"
        >
          {isSubmitting ? <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" /> : <Send aria-hidden="true" className="h-4 w-4" />}
          提交答案
        </button>
      </div>
    </form>
  )
}
