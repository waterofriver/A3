export const RESOURCE_TYPES = [
  "handout",
  "mindmap",
  "quiz",
  "code",
  "video",
] as const

export type ResourceType = (typeof RESOURCE_TYPES)[number]

export type GatewayError = {
  code: string
  message: string
  retryable: boolean
  details?: unknown
}

export type ResourceGatewayEvent = {
  event:
    | "task.started"
    | "agent.started"
    | "task.progress"
    | "content.delta"
    | "media.ready"
    | "resource.ready"
    | "task.completed"
    | "task.failed"
    | "heartbeat"
  task_id: string
  seq: number
  trace_id: string
  current_agent?: string | null
  progress: number
  resource_type?: ResourceType | null
  content: string
  media_url?: string | null
  finish_flag: boolean
  resource_ids: string[]
  error?: GatewayError | null
  demo_mode: boolean
}

export type MindMapNode = {
  id: string
  label: string
  parent_id: string | null
}

export type QuizQuestion = {
  id: string
  question_type: "choice" | "blank" | "programming"
  prompt: string
  options: string[]
  answer: string
  explanation: string
}

type ResourceBase = {
  id: string
  task_id: string | null
  course_name: string | null
  title: string
  media_url: string | null
  created_at: string | null
}

export type HandoutResourceDetail = ResourceBase & {
  resource_type: "handout"
  payload: { markdown: string }
}

export type MindMapResourceDetail = ResourceBase & {
  resource_type: "mindmap"
  payload: { nodes: MindMapNode[] }
}

export type QuizResourceDetail = ResourceBase & {
  resource_type: "quiz"
  payload: { questions: QuizQuestion[] }
}

export type CodeResourceDetail = ResourceBase & {
  resource_type: "code"
  payload: { language: string; code: string; description: string }
}

export type VideoResourceDetail = ResourceBase & {
  resource_type: "video"
  payload: {
    summary: string
    poster_url: string
    duration_seconds: number
  }
}

export type ResourceDetail =
  | HandoutResourceDetail
  | MindMapResourceDetail
  | QuizResourceDetail
  | CodeResourceDetail
  | VideoResourceDetail

export type ResourceSummary = Omit<ResourceBase, "task_id" | "course_name"> & {
  task_id: string
  course_name: string
  resource_type: ResourceType
}

export type CourseSummary = {
  name: string
  slug: string
  content_ready: boolean
  is_demo: boolean
}

export type ResourceGenerateRequest = {
  user_id: string
  course_name: string
  weak_point: string
  resource_type_list: ResourceType[]
}
