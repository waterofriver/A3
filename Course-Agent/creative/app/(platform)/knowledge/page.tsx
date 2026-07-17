"use client"

import { useQuery } from "@tanstack/react-query"
import { LibraryBig } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"

import { KnowledgePageContent } from "@/components/knowledge/knowledge-page-content"
import { ErrorNotice } from "@/components/shared/error-notice"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { apiFetch } from "@/lib/api/client"
import {
  getRememberedCourse,
  rememberSelectedCourse,
  selectInitialCourse,
} from "@/lib/course-selection"
import type { components } from "@/lib/api/generated"

type CourseSummary = components["schemas"]["CourseSummary"]
type CourseBase = components["schemas"]["CourseBaseData"]

export default function KnowledgePage() {
  const [courseName, setCourseName] = useState("")
  const coursesQuery = useQuery({
    queryKey: ["courses"],
    queryFn: () => apiFetch<CourseSummary[]>("/api/course/list"),
  })
  const courses = useMemo(() => coursesQuery.data ?? [], [coursesQuery.data])

  const selectCourse = useCallback((name: string) => {
    setCourseName(name)
    rememberSelectedCourse(name)
  }, [])

  useEffect(() => {
    if (courseName || !courses.length) return
    const remembered = getRememberedCourse()
    const selected = selectInitialCourse(courses, remembered)
    if (selected) selectCourse(selected.name)
  }, [courseName, courses, selectCourse])

  const selectedSummary = courses.find((course) => course.name === courseName)
  const courseQuery = useQuery({
    queryKey: ["course-base", courseName],
    queryFn: () =>
      apiFetch<CourseBase>(
        `/api/course/base?course_name=${encodeURIComponent(courseName)}`,
      ),
    enabled: Boolean(courseName && selectedSummary?.content_ready),
  })
  const course = selectedSummary
    ? selectedSummary.content_ready
      ? courseQuery.data
      : { ...selectedSummary, chapters: [] }
    : undefined
  const error = coursesQuery.error ?? courseQuery.error

  return (
    <div className="mx-auto w-full max-w-[1480px]">
      <header className="flex items-end justify-between border-b pb-5">
        <div>
          <p className="text-sm font-medium text-[#2457d6]">COURSE KNOWLEDGE</p>
          <h1 className="mt-2 text-2xl font-semibold text-[#182132]">课程知识库</h1>
        </div>
        <div className="flex items-center gap-3">
          <LibraryBig aria-hidden="true" className="h-4 w-4 text-[#2457d6]" />
          <Select onValueChange={selectCourse} value={courseName}>
            <SelectTrigger aria-label="选择课程" className="w-[240px] bg-white">
              <SelectValue placeholder="等待课程" />
            </SelectTrigger>
            <SelectContent>
              {courses.map((item) => (
                <SelectItem key={item.slug} value={item.name}>
                  {item.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </header>

      {error ? (
        <div className="mt-5">
          <ErrorNotice
            error={error instanceof Error ? error : "课程知识库加载失败。"}
            onRetry={() => {
              void coursesQuery.refetch()
              void courseQuery.refetch()
            }}
          />
        </div>
      ) : null}

      {coursesQuery.isPending || (selectedSummary?.content_ready && courseQuery.isPending) ? (
        <div className="mt-6 grid h-[480px] place-items-center border bg-white text-sm text-[#718096]" role="status">
          正在读取课程资料
        </div>
      ) : course ? (
        <KnowledgePageContent course={course} />
      ) : (
        <div className="mt-6 grid h-[480px] place-items-center border border-dashed bg-white text-sm text-[#718096]">
          暂无可浏览课程
        </div>
      )}
    </div>
  )
}
