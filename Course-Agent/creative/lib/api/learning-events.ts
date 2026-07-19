import { API_BASE_URL, apiFetch } from "@/lib/api/client"

export type LearningEventType =
  | "resource_opened"
  | "resource_closed"
  | "path_node_completed"
  | "path_node_reset"
  | "question_asked"
  | "video_progress"

export function pathNodeEventType(completed: boolean): "path_node_completed" | "path_node_reset" {
  return completed ? "path_node_completed" : "path_node_reset"
}

export type LearningEventInput = {
  event_type: LearningEventType
  resource_id?: string
  path_node_id?: string
  client_started_at?: string
  client_ended_at?: string
  metadata: Record<string, unknown>
}

type Bucket = {
  userId: string
  courseName: string
  events: LearningEventInput[]
  timer?: number
}

const buckets = new Map<string, Bucket>()
let listenersRegistered = false

const bucketKey = (userId: string, courseName: string) =>
  `${encodeURIComponent(userId)}:${encodeURIComponent(courseName)}`

function ensureLifecycleListeners() {
  if (listenersRegistered || typeof window === "undefined") return
  listenersRegistered = true
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") void flushAllLearningEvents()
  })
  window.addEventListener("beforeunload", flushLearningEventsWithBeacon)
}

export function queueLearningEvent(
  userId: string,
  courseName: string,
  event: LearningEventInput,
) {
  ensureLifecycleListeners()
  const key = bucketKey(userId, courseName)
  const bucket = buckets.get(key) ?? {
    userId,
    courseName,
    events: [],
  }
  bucket.events.push(event)
  buckets.set(key, bucket)

  if (bucket.events.length >= 10) {
    void flushLearningEvents(userId, courseName)
    return
  }
  if (!bucket.timer) {
    bucket.timer = window.setTimeout(() => {
      bucket.timer = undefined
      void flushLearningEvents(userId, courseName)
    }, 10_000)
  }
}

export async function flushLearningEvents(userId: string, courseName: string) {
  const key = bucketKey(userId, courseName)
  const bucket = buckets.get(key)
  if (!bucket?.events.length) return
  if (bucket.timer) window.clearTimeout(bucket.timer)
  bucket.timer = undefined
  const events = bucket.events.splice(0, bucket.events.length)

  try {
    await apiFetch<{ accepted: number }>("/api/learning/events", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, course_name: courseName, events }),
    })
  } catch (error) {
    bucket.events.unshift(...events)
    throw error
  }
}

async function flushAllLearningEvents() {
  await Promise.allSettled(
    [...buckets.values()].map((bucket) =>
      flushLearningEvents(bucket.userId, bucket.courseName),
    ),
  )
}

function flushLearningEventsWithBeacon() {
  if (!navigator.sendBeacon) return
  for (const bucket of buckets.values()) {
    if (!bucket.events.length) continue
    const body = JSON.stringify({
      user_id: bucket.userId,
      course_name: bucket.courseName,
      events: bucket.events,
    })
    navigator.sendBeacon(
      `${API_BASE_URL}/api/learning/events`,
      new Blob([body], { type: "application/json" }),
    )
  }
}
