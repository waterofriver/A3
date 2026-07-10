export type LearningPathNode = {
  id: string
  position: number
  stage_name: string
  difficulty: string
  resource_id: string | null
  completed_at: string | null
}

export type LearningPathData = {
  id: string
  user_id: string
  course_name: string
  version: number
  nodes: LearningPathNode[]
}
