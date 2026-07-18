"use client"

import {
  FileText,
  LibraryBig,
  Network,
  Sparkles,
  Video,
} from "lucide-react"
import { FormEvent, useEffect, useState } from "react"

import {
  RESOURCE_TYPES,
  type CourseSummary,
  type ResourceType,
} from "@/lib/api/resource-types"

type GenerationValues = {
  course_name: string
  weak_point: string
  resource_type_list: ResourceType[]
}

type GenerationFormProps = {
  courses: CourseSummary[]
  isSubmitting?: boolean
  onCourseChange?: (course: CourseSummary) => void
  onGenerate: (values: GenerationValues) => void | Promise<void>
}

const resourceOptions = [
  { type: "handout", label: "讲义文档", icon: FileText },
  { type: "mindmap", label: "思维导图", icon: Network },
  { type: "code", label: "拓展阅读", icon: LibraryBig },
  { type: "video", label: "教学图文视频", icon: Video },
] as const

export function GenerationForm({
  courses,
  isSubmitting = false,
  onCourseChange,
  onGenerate,
}: GenerationFormProps) {
  const [courseSlug, setCourseSlug] = useState(courses[0]?.slug ?? "")
  const [weakPoint, setWeakPoint] = useState("")
  const [selectedTypes, setSelectedTypes] = useState<ResourceType[]>([])
  const [validationError, setValidationError] = useState("")

  useEffect(() => {
    if (courses.some((course) => course.slug === courseSlug)) return
    setCourseSlug(courses[0]?.slug ?? "")
  }, [courseSlug, courses])

  const handleCourseChange = (slug: string) => {
    setCourseSlug(slug)
    const course = courses.find((item) => item.slug === slug)
    if (course) onCourseChange?.(course)
  }

  const toggleType = (resourceType: ResourceType, checked: boolean) => {
    setSelectedTypes((current) =>
      checked
        ? RESOURCE_TYPES.filter(
            (candidate) =>
              candidate === resourceType || current.includes(candidate),
          )
        : current.filter((candidate) => candidate !== resourceType),
    )
    setValidationError("")
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const course = courses.find((item) => item.slug === courseSlug)
    if (!course) {
      setValidationError("请选择可用课程。")
      return
    }
    if (!selectedTypes.length) {
      setValidationError("至少选择一种资源类型。")
      return
    }
    setValidationError("")
    void onGenerate({
      course_name: course.name,
      weak_point: weakPoint.trim(),
      resource_type_list: selectedTypes,
    })
  }

  return (
    <section className="self-start rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden" aria-label="资源生成参数">
      <header className="border-b border-slate-100 bg-slate-50/50 px-5 py-4">
        <p className="text-sm font-semibold text-slate-700">生成参数</p>
        <p className="mt-0.5 text-xs text-slate-400">画像将自动参与 Agent 上下文</p>
      </header>

      <form className="space-y-6 p-5" onSubmit={handleSubmit}>
        <div>
          <label className="text-xs font-bold tracking-wider text-slate-400 uppercase" htmlFor="course-select">
            课程
          </label>
          <select
            className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3 text-sm text-slate-600 outline-none transition-all duration-200 hover:border-slate-300 focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
            disabled={!courses.length || isSubmitting}
            id="course-select"
            onChange={(event) => handleCourseChange(event.target.value)}
            value={courseSlug}
          >
            {courses.map((course) => (
              <option key={course.slug} value={course.slug}>
                {course.name}{course.is_demo && !course.name.includes("演示") ? "（演示）" : ""}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-bold tracking-wider text-slate-400 uppercase" htmlFor="weak-point">
            薄弱知识点
          </label>
          <textarea
            className="mt-2 min-h-24 w-full resize-none rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-2.5 text-sm leading-relaxed text-slate-600 placeholder-slate-400 outline-none transition-all duration-200 hover:border-slate-300 focus:border-primary focus:bg-white focus:ring-4 focus:ring-primary/10"
            disabled={isSubmitting}
            id="weak-point"
            onChange={(event) => setWeakPoint(event.target.value)}
            placeholder="例如：ROS2 节点通信"
            value={weakPoint}
          />
        </div>

        <fieldset>
          <div className="flex items-center justify-between">
            <legend className="text-xs font-bold tracking-wider text-slate-400 uppercase">资源类型</legend>
            <button
              className="text-xs font-semibold text-primary hover:text-blue-600 active:scale-95 transition-all duration-150"
              disabled={isSubmitting}
              onClick={() => setSelectedTypes([...RESOURCE_TYPES])}
              type="button"
            >
              全选资源
            </button>
          </div>
          <div className="mt-3 space-y-1.5">
            {resourceOptions.map((option) => {
              const Icon = option.icon
              const checked = selectedTypes.includes(option.type)
              return (
                <label
                  className="flex h-11 cursor-pointer items-center gap-3 rounded-xl border border-slate-100 bg-slate-50/30 px-3 text-sm text-slate-600 transition-all duration-150 hover:border-slate-200 hover:bg-slate-50"
                  key={option.type}
                >
                  <input
                    checked={checked}
                    className="h-4 w-4 rounded border-slate-300 text-primary accent-primary focus:ring-primary"
                    disabled={isSubmitting}
                    onChange={(event) => toggleType(option.type, event.target.checked)}
                    type="checkbox"
                  />
                  <Icon aria-hidden="true" className="h-4 w-4 text-slate-400" />
                  <span className="font-medium text-slate-600">{option.label}</span>
                </label>
              )
            })}
          </div>
        </fieldset>

        <div className="min-h-5" aria-live="polite">
          {validationError ? (
            <p className="text-xs font-medium text-rose-500">{validationError}</p>
          ) : null}
        </div>

        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-white shadow-md shadow-primary/10 transition-all duration-200 hover:bg-blue-600 hover:shadow-lg hover:shadow-primary/20 hover:-translate-y-[0.5px] active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:transform-none disabled:shadow-none"
          disabled={isSubmitting || !courses.length}
          type="submit"
        >
          <Sparkles aria-hidden="true" className="h-4 w-4" />
          {isSubmitting ? "正在提交" : "生成学习资源"}
        </button>
      </form>
    </section>
  )
}

export type { GenerationValues }
