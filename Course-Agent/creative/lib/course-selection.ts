type CourseSelection = {
  name: string
  content_ready: boolean
}

export const SELECTED_COURSE_KEY = "zhixue_selected_course"

const COURSE_SELECTION_EVENT = "zhixue:course-selected"

export function selectInitialCourse<T extends CourseSelection>(
  courses: T[],
  rememberedName: string | null,
): T | undefined {
  return (
    courses.find(
      (course) => course.name === rememberedName && course.content_ready,
    ) ?? courses.find((course) => course.content_ready) ?? courses[0]
  )
}

export function getRememberedCourse(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(SELECTED_COURSE_KEY)
}

export function rememberSelectedCourse(name: string): void {
  window.localStorage.setItem(SELECTED_COURSE_KEY, name)
  window.dispatchEvent(new CustomEvent<string>(COURSE_SELECTION_EVENT, { detail: name }))
}

export function subscribeToSelectedCourse(
  listener: (name: string) => void,
): () => void {
  const handleChange = (event: Event) => {
    listener((event as CustomEvent<string>).detail)
  }
  window.addEventListener(COURSE_SELECTION_EVENT, handleChange)
  return () => window.removeEventListener(COURSE_SELECTION_EVENT, handleChange)
}
