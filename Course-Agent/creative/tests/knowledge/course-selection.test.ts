import { describe, expect, it, vi } from "vitest"

import {
  rememberSelectedCourse,
  selectInitialCourse,
  subscribeToSelectedCourse,
} from "@/lib/course-selection"

const demoCourse = {
  name: "Demo course",
  slug: "demo",
  content_ready: false,
  is_demo: true,
}

const readyCourse = {
  name: "Ready course",
  slug: "ready",
  content_ready: true,
  is_demo: false,
}

describe("selectInitialCourse", () => {
  it("prefers a ready course over a remembered empty demo course", () => {
    expect(selectInitialCourse([demoCourse, readyCourse], demoCourse.name)).toEqual(
      readyCourse,
    )
  })

  it("notifies the app shell when the selected course changes", () => {
    const listener = vi.fn()
    const unsubscribe = subscribeToSelectedCourse(listener)

    rememberSelectedCourse(readyCourse.name)

    expect(listener).toHaveBeenCalledWith(readyCourse.name)
    expect(localStorage.getItem("zhixue_selected_course")).toBe(readyCourse.name)
    unsubscribe()
  })
})
