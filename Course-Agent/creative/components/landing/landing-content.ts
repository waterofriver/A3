export type LandingChapter = {
  id: "intro" | "profile" | "resources" | "path" | "memory"
  index: string
  title: string
  eyebrow: string
  description: string
  detail: string
}

export const landingChapters: LandingChapter[] = [
  {
    id: "intro",
    index: "00",
    title: "智学引擎",
    eyebrow: "ZHIXUE ENGINE / LEARNING INTELLIGENCE",
    description: "从学习数据到个性化成长路径",
    detail: "让理解、资源、路径与复习在同一套学习系统中持续联动。",
  },
  {
    id: "profile",
    index: "01",
    title: "学习画像",
    eyebrow: "LEARNER SIGNALS",
    description: "从每一次表达中，看见更清晰的学习状态。",
    detail: "理解目标、基础、偏好与当下的学习节奏，让后续决策有所依据。",
  },
  {
    id: "resources",
    index: "02",
    title: "智能资源",
    eyebrow: "ADAPTIVE MATERIALS",
    description: "围绕当前需要，组织恰当的学习内容。",
    detail: "用清晰的信息网络连接解释、练习、示例与延伸内容，减少无效浏览。",
  },
  {
    id: "path",
    index: "03",
    title: "成长路径",
    eyebrow: "NEXT BEST ACTION",
    description: "把学习目标拆解为可执行的下一步。",
    detail: "让每个阶段都具备方向、节奏与反馈，持续向更完整的能力结构推进。",
  },
  {
    id: "memory",
    index: "04",
    title: "评估与记忆",
    eyebrow: "REFLECT AND RETAIN",
    description: "让评估成为下一次成长的起点。",
    detail: "识别需要回顾的内容，建立更自然的复习节奏，并沉淀每一步成长。",
  },
]
