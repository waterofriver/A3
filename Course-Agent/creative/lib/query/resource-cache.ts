import {
  RESOURCE_TYPES,
  type GatewayError,
  type ResourceGatewayEvent,
  type ResourceType,
} from "@/lib/api/resource-types"

export type ResourceProgressState = {
  progress: number
  status: "idle" | "running" | "succeeded" | "failed"
  content: string
  resourceIds: string[]
  mediaUrl?: string
  error?: GatewayError
}

export type ResourceTaskState = {
  taskId?: string
  lastSeq: number
  globalProgress: number
  currentAgent?: string
  demoMode: boolean
  status: "idle" | "running" | "partial_success" | "succeeded" | "failed"
  byType: Record<ResourceType, ResourceProgressState>
  resourceIds: string[]
  error?: GatewayError
}

const emptyProgress = (): ResourceProgressState => ({
  progress: 0,
  status: "idle",
  content: "",
  resourceIds: [],
})

const emptyByType = () =>
  Object.fromEntries(
    RESOURCE_TYPES.map((resourceType) => [resourceType, emptyProgress()]),
  ) as Record<ResourceType, ResourceProgressState>

export const emptyResourceTask: ResourceTaskState = {
  lastSeq: 0,
  globalProgress: 0,
  demoMode: false,
  status: "idle",
  byType: emptyByType(),
  resourceIds: [],
}

export function createResourceTaskState(taskId?: string): ResourceTaskState {
  return {
    ...emptyResourceTask,
    taskId,
    byType: emptyByType(),
    resourceIds: [],
  }
}

const activeTaskKey = (userId: string, courseName: string) =>
  `zhixue_resource_task:${encodeURIComponent(userId)}:${encodeURIComponent(courseName)}`

export function rememberActiveResourceTask(
  userId: string,
  courseName: string,
  taskId: string,
) {
  window.localStorage.setItem(activeTaskKey(userId, courseName), taskId)
}

export function readActiveResourceTask(userId: string, courseName: string) {
  return window.localStorage.getItem(activeTaskKey(userId, courseName))
}

export function clearActiveResourceTask(userId: string, courseName: string) {
  window.localStorage.removeItem(activeTaskKey(userId, courseName))
}

const appendUnique = (current: string[], incoming?: string[]) => [
  ...current,
  ...(incoming ?? []).filter((id) => !current.includes(id)),
]

export function applyResourceEvent(
  state: ResourceTaskState,
  event: ResourceGatewayEvent,
): ResourceTaskState {
  if (event.seq <= state.lastSeq && event.event !== "heartbeat") return state

  const resourceIds = appendUnique(state.resourceIds, event.resource_ids)
  const hasCompletedType = Object.values(state.byType).some(
    (item) => item.status === "succeeded",
  )
  const status: ResourceTaskState["status"] =
    event.event === "task.completed"
      ? "succeeded"
      : event.event === "task.failed"
        ? hasCompletedType
          ? "partial_success"
          : "failed"
        : event.event === "heartbeat"
          ? state.status
          : "running"

  if (!event.resource_type) {
    return {
      ...state,
      taskId: event.task_id,
      lastSeq: Math.max(state.lastSeq, event.seq),
      globalProgress: event.progress || state.globalProgress,
      currentAgent: event.current_agent ?? state.currentAgent,
      demoMode: event.demo_mode || state.demoMode,
      status,
      resourceIds,
      error: event.error ?? state.error,
    }
  }

  const current = state.byType[event.resource_type]
  const typeStatus: ResourceProgressState["status"] =
    event.event === "resource.ready"
      ? "succeeded"
      : event.event === "task.failed"
        ? "failed"
        : "running"

  return {
    ...state,
    taskId: event.task_id,
    lastSeq: Math.max(state.lastSeq, event.seq),
    globalProgress: event.progress,
    currentAgent: event.current_agent ?? state.currentAgent,
    demoMode: event.demo_mode || state.demoMode,
    status,
    byType: {
      ...state.byType,
      [event.resource_type]: {
        ...current,
        progress: event.progress,
        status: typeStatus,
        content:
          event.event === "content.delta"
            ? current.content + event.content
            : current.content,
        resourceIds: appendUnique(current.resourceIds, event.resource_ids),
        mediaUrl: event.media_url ?? current.mediaUrl,
        error: event.error ?? current.error,
      },
    },
    resourceIds,
    error: event.error ?? state.error,
  }
}
