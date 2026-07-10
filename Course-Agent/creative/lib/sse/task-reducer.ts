import type { components } from "@/lib/api/generated"

export type GatewayEvent = components["schemas"]["GatewayEvent"]
type GatewayError = components["schemas"]["GatewayError"]

export type TaskState = {
  taskId?: string
  lastSeq: number
  progress: number
  currentAgent?: string
  content: string
  profile: Record<string, unknown> | null
  resourceIds: string[]
  status: "idle" | "running" | "succeeded" | "failed"
  error?: GatewayError
  demoMode: boolean
  lastEvent?: GatewayEvent
}

export const initialTaskState: TaskState = {
  lastSeq: 0,
  progress: 0,
  content: "",
  profile: null,
  resourceIds: [],
  status: "idle",
  demoMode: false,
}

export function reduceTaskEvent(
  state: TaskState,
  event: GatewayEvent,
): TaskState {
  if (event.seq <= state.lastSeq) return state

  const isTerminal = state.status === "succeeded" || state.status === "failed"
  let status = isTerminal ? state.status : "running"
  if (!isTerminal && event.event === "task.completed") status = "succeeded"
  if (!isTerminal && event.event === "task.failed") status = "failed"

  return {
    ...state,
    taskId: event.task_id,
    lastSeq: event.seq,
    progress: event.progress,
    currentAgent: event.current_agent ?? state.currentAgent,
    content:
      event.event === "content.delta"
        ? state.content + event.content
        : state.content,
    profile: event.profile_patch
      ? { ...(state.profile ?? {}), ...event.profile_patch }
      : state.profile,
    resourceIds:
      event.resource_ids?.length ? event.resource_ids : state.resourceIds,
    status,
    error: event.error ?? state.error,
    demoMode: state.demoMode || event.demo_mode,
    lastEvent: event,
  }
}
