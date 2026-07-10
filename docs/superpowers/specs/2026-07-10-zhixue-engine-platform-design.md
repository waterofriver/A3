# 智学引擎平台改造设计规格

- 日期：2026-07-10
- 状态：交互设计已确认，等待书面规格审阅
- 前端基线：`Course-Agent/creative`（Next.js 15、React 19、TypeScript、Tailwind CSS、shadcn/ui）
- 新后端：FastAPI + SQLite
- 产品名称：智学引擎
- 产品副标题：多智能体个性化学习系统

## 1. 背景与目标

现有仓库包含一个 Next.js 创意工作台和一个 Django 论坛/资源后端。现有前端的主要业务集中在约 2400 行的 `components/creative.tsx` 中，并混合了创意应用示例、论坛、Coze 聊天、Coze 自动出题、资源浏览和用户资料等逻辑。该结构无法直接承载七个教学业务页面、统一 SSE 流式事件、多 Agent 进度、任务恢复和跨团队接口接入。

本次改造在原 Next.js 项目中进行模块化重建，保留成熟的 UI 基础组件与技术栈，移除论坛和 Coze 的运行入口，新建 FastAPI 网关和 SQLite 数据层。系统必须在队友的真实 Agent 尚未完成时使用 Mock Provider 独立运行；部署后可通过环境变量切换到真实 Agent 服务，而不修改前端业务代码。

最终目标包括：

1. 完成登录初始化、画像采集、资源生成、学习路径、全局答疑、学习评估和课程知识库七个业务场景。
2. 所有 AI 内容均以流式增量展示；所有生成任务均显示当前 Agent、全局进度和资源独立进度。
3. FastAPI 提供固定契约、SSE、任务恢复、SQLite CRUD、Mock/Remote Agent 适配层。
4. 本地 Windows 可一键启动，Linux 云服务器可通过 Docker Compose 部署。
5. 交付接口文档、组件文档、环境说明、全页面截图和可复现的交互演示材料。

## 2. 已确认约束

### 2.1 必须保留

- 原有 Next.js 工程及其 Tailwind、shadcn/ui、Lucide、Recharts 等基础能力。
- 用户 ID 仅作为简易演示登录标识，存入浏览器 `localStorage`。
- 用户画像、任务、资源、学习记录和评估结果由后端 SQLite 持久化。
- 后端返回媒体 URL，前端只负责展示与下载。
- PC 端优先，验收视口为 1366x768、1440x900 和 1920x1080；不承担移动端适配。

### 2.2 必须移除

- 前端论坛导航、论坛列表、发帖、评论、点赞、搜索和论坛弹窗。
- 新 FastAPI 中不建立任何论坛路由、模型或数据迁移。
- Coze 全局悬浮组件、Coze 自动出题模块、Token 路由、SDK 脚本、环境变量、本地存储键和 `@coze/api` 依赖。
- 当前营销落地页和与教学业务无关的创意应用、文件、项目示例。

### 2.3 旧 Django 的边界

用户选择保留旧 Django 目录作为历史参考，因此本次不把 `mywebsite` 作为运行后端，也不将其加入启动脚本或容器。Django 根路由中的论坛入口将停用，活跃网站无法访问旧论坛。历史模型、迁移和模板可留在遗留目录中用于追溯，但不属于新系统接口或验收范围。

### 2.4 当前外部依赖状态

- A、C 成员的真实 LangGraph/资源 Agent 尚不可调用。
- 正式课程 PDF、DOCX、PPTX、视频等文件尚未提供；仓库仅有 `materials.json` 元数据，且引用文件缺失。
- 本次实现不得伪造正式课程正文。没有真实文件时，知识库展示明确空状态。

## 3. 非目标

本次不实现：

- 真实大模型提示词、LangGraph 工作流或多模态生成算法。
- JWT、密码注册、RBAC、管理员后台或生产级多租户认证。
- 论坛、用户社交、评论、点赞或内容审核。
- 浏览器端图片/视频生成。
- Redis、Celery、Kafka 或分布式任务队列。
- 移动端布局。
- 课程内容编辑器或文件上传后台。
- 对旧 Django 用户和论坛数据做迁移。

## 4. 总体架构

### 4.1 运行组件

```text
Browser
  -> Next.js 15 web
       -> typed API client
       -> SSE/fetch stream client
       -> TanStack Query cache
  -> FastAPI gateway
       -> API routers
       -> Task Manager + SSE Hub
       -> domain services
       -> AgentProvider interface
            -> MockAgentProvider
            -> RemoteAgentProvider
       -> SQLAlchemy repositories
       -> SQLite
       -> local course/media files
```

Next.js 只依赖 FastAPI 的固定接口。`RemoteAgentProvider` 负责把队友服务的事件转换为网关事件，任何上游字段差异都不得泄漏到页面组件。

### 4.2 模式切换

后端使用以下环境变量：

```dotenv
AGENT_MODE=mock
REMOTE_AGENT_BASE_URL=
REMOTE_AGENT_API_KEY=
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
```

- `AGENT_MODE=mock`：本地生成可复现的流式文本、进度、画像和资源结果。
- `AGENT_MODE=remote`：调用队友 Agent 服务并标准化返回事件。
- `ALLOW_MOCK_FALLBACK=false`：远程模式失败时不得静默返回模拟结果。
- 只有显式启用回退时，页面才允许展示模拟结果，并必须标注“演示模式”。

### 4.3 SQLite 运行边界

SQLite 模式使用单个 Uvicorn API worker。该约束足以支持本地开发、答辩演示和单机云部署。任务存储与事件总线通过接口隔离，未来如需多实例，可替换为 PostgreSQL/Redis，而无需改动路由和前端。

## 5. 目录设计

### 5.1 前端

```text
Course-Agent/creative/
  app/
    page.tsx
    (auth)/
      login/page.tsx
    (platform)/
      layout.tsx
      profile/page.tsx
      workspace/page.tsx
      resources/[resourceId]/page.tsx
      learning-path/page.tsx
      evaluation/page.tsx
      knowledge/page.tsx
  components/
    app-shell/
    profile/
    resources/
    learning-path/
    qa/
    evaluation/
    knowledge/
    shared/
    ui/
  lib/
    api/
    sse/
    query/
    schemas/
    session/
  tests/
  e2e/
```

业务组件按领域分组，不再把路由、数据请求和多种页面渲染塞入单个大组件。

### 5.2 后端

```text
backend/
  app/
    main.py
    api/routes/
    agents/
      base.py
      mock.py
      remote.py
    core/
      config.py
      errors.py
      logging.py
    db/
      base.py
      session.py
      models.py
      migrations/
    repositories/
    schemas/
    services/
    tasks/
    media/
  data/
    courses/
  tests/
  pyproject.toml
  alembic.ini
```

## 6. 页面与导航

### 6.1 全站外壳

采用“教学指挥台”布局：固定左侧导航、宽主工作区、顶部课程切换和用户入口。Agent 任务栏只在任务运行或用户主动展开时占用右侧空间，任务结束后收起，主区自动扩展。

固定导航：

1. 画像采集
2. 资源工作台
3. 学习路径
4. 学习评估
5. 课程知识库

智能答疑不是固定页面，而是任意页面均可打开的全局右侧抽屉。

### 6.2 路由职责

| 路由 | 职责 | 关键组件 |
|---|---|---|
| `/login` | 输入 `user_id`，查询新老用户并决定下一路由 | `LoginPanel`, `SessionBootstrap` |
| `/profile` | 流式画像对话、六维画像增量、确认画像 | `ProfileChat`, `ProfilePanel`, `AgentProgress` |
| `/workspace` | 课程选择、资源生成、进度和历史资源 | `GenerationForm`, `TaskRail`, `ResourceGrid` |
| `/resources/[resourceId]` | 资源深链和完整交互 | `ResourceRenderer`, `QuizPlayer`, `MediaViewer` |
| `/learning-path` | 六维摘要、学习路径和节点完成 | `ProfileSummary`, `LearningPathGraph` |
| `/evaluation` | 多维评分、弱项统计、优化计划 | `ScorePanel`, `WeaknessChart`, `PlanChanges` |
| `/knowledge` | 只读课程目录和原文件预览 | `KnowledgeTree`, `DocumentPreview` |
| 全局抽屉 | 文字、图片或视频形式的流式答疑 | `QaDrawer`, `AnswerModeControl`, `MediaCard` |

### 6.3 路由规则

- 根路径读取 `localStorage` 中的 `zhixue_user_id` 并跳转。
- 无用户 ID 跳转 `/login`。
- 有用户 ID 但画像未确认跳转 `/profile`。
- 已确认画像的老用户默认进入 `/workspace`。
- 学习路径和评估页面在前置数据不足时展示空状态，不强制跳回工作台。

## 7. 视觉设计

视觉方向为“A3 明亮数智”：

- 白色导航和浅灰工作区。
- 钴蓝作为主要命令色。
- 草绿表示正常进度和完成状态。
- 珊瑚色表示风险、失败和需要关注的内容。
- 深灰用于主要文字，避免整站被单一蓝色支配。
- 卡片圆角不超过 8px，不在卡片中嵌套装饰性卡片。
- 页面标题保持工作台尺度，不使用营销页式超大标题。
- 工具按钮优先使用 Lucide 图标与 tooltip。
- 固定尺寸的工具栏、进度条、图谱节点和资源预览使用稳定网格与最小/最大尺寸，避免流式内容导致布局跳动。

## 8. 共享组件

### 8.1 内容渲染

- `MarkdownRenderer`：`react-markdown` + `remark-gfm`，支持标题、表格、列表和代码块。
- `CodeBlock`：语法高亮、复制按钮、语言标识和横向滚动。
- `MindMapViewer`：基于 `@xyflow/react` 渲染节点与连线。
- `MediaCard`：统一图片、视频、预览、下载和局部失败状态。
- `VideoPlayer`：使用原生 `<video>`，支持后端本地 URL。

### 8.2 学习交互

- `QuizPlayer`：选择、填空和编程题；提交后显示逐题结果。
- `LearningPathGraph`：复用 React Flow，展示有序阶段、难度和绑定资源。
- `ProfilePanel`：严格渲染后端返回的六维字段。
- `ScorePanel` / `WeaknessChart`：使用 Recharts 展示评估数据。

### 8.3 Agent 任务

- `AgentProgress`：当前 Agent、全局进度、状态文本。
- `TaskRail`：每种资源独立进度和失败重试。
- `StreamingText`：按事件序列追加文本，支持 Markdown 增量刷新。
- `RetryAction`：仅在 `retryable=true` 时出现。

### 8.4 系统状态

- `LoadingState`
- `ErrorNotice`
- `EmptyState`
- `OfflineBanner`
- 页面级与资源卡片级 Error Boundary

## 9. 前端数据管理

- `localStorage` 只保存 `zhixue_user_id` 和非核心 UI 偏好。
- TanStack Query 管理用户、课程、资源、路径和评估缓存。
- SSE 增量通过任务 reducer 写入对应 Query cache。
- Query key 必须包含 `user_id` 与 `course_name`，避免跨用户或跨课程污染。
- 资源列表接口是重复访问的真实来源；不得仅依赖内存缓存。
- API 类型由 FastAPI OpenAPI 通过 `openapi-typescript` 生成，避免手写字段漂移。

## 10. 六维画像契约

网关对前端固定输出：

```json
{
  "knowledge_foundation": "string",
  "cognitive_style": "string",
  "weak_points": ["string"],
  "learning_pace": "string",
  "content_preferences": ["string"],
  "short_term_goal": "string"
}
```

前端不得根据自由文本猜测字段。`RemoteAgentProvider` 负责把队友输出映射到该结构；缺失字段由网关拒绝或保留上一修订版，不允许前端补造。

## 11. API 设计

### 11.1 健康与用户

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | API、数据库和当前 Agent 模式健康状态 |
| GET | `/api/user/info?user_id=...` | 用户信息、完整画像、是否确认 |
| POST | `/api/chat/profile` | 请求体 `{user_id, chat_text}`，以 POST 流返回画像对话事件 |
| POST | `/api/profile/confirm` | 确认当前画像修订版，解锁工作台 |

未知用户的 `GET /api/user/info` 返回 `exists=false`，而不是用 404 表示异常。首次画像对话创建用户记录。

### 11.2 资源与任务

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/resource/generate` | 创建多资源任务，返回 `task_id` |
| GET | `/api/resource/progress/{task_id}` | SSE 推送 Agent 和资源进度 |
| GET | `/api/resource/list` | 按用户、课程和资源类型查询历史资源 |
| GET | `/api/resource/detail/{resource_id}` | 获取完整 Markdown、代码、题目或媒体信息 |
| GET | `/api/task/{task_id}` | 任务快照、累计内容和最终结果 |
| POST | `/api/task/{task_id}/retry` | 重试可重试任务，保留原请求快照 |

资源生成请求：

```json
{
  "user_id": "student-001",
  "course_name": "机器人操作系统",
  "weak_point": "ROS2 节点通信",
  "resource_type_list": ["handout", "mindmap", "quiz", "code", "video"]
}
```

固定资源枚举：`handout`、`mindmap`、`quiz`、`code`、`video`。中文名称只由前端展示。

资源生成请求支持 `Idempotency-Key` 请求头。同一用户、同一请求内容和同一幂等键不得创建重复任务。

### 11.3 学习路径、答题和行为

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/path/get?user_id=...&course_name=...` | 返回有序学习节点和绑定资源 |
| POST | `/api/quiz/submit` | 提交答案，返回逐题判定、总分和更新后的弱项 |
| POST | `/api/learning/events` | 批量记录资源浏览、节点完成和提问事件 |

学习事件允许的 `event_type`：

- `resource_opened`
- `resource_closed`
- `path_node_completed`
- `question_asked`
- `video_progress`

事件必须带客户端时间、用户、课程和关联资源/节点标识；服务端计算可信持续时长，不直接接受任意累计秒数。

### 11.4 答疑与评估

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/chat/qa` | 请求体 `{user_id, question, answer_mode}`，POST 流返回混合内容 |
| GET | `/api/eval/report?user_id=...&course_name=...` | 多维评分、弱项和优化计划 |
| POST | `/api/eval/apply` | 将报告中的优化方案应用为新版学习路径 |

`answer_mode` 固定为 `text`、`image`、`video`。

### 11.5 课程知识库

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/course/list` | 返回课程配置及其 `content_ready`、`is_demo` 状态 |
| GET | `/api/course/base?course_name=...` | 返回章节树、文档元数据和后端预览 URL |

## 12. SSE 事件契约

### 12.1 事件类型

- `task.started`
- `agent.started`
- `task.progress`
- `content.delta`
- `profile.patch`
- `media.ready`
- `resource.ready`
- `task.completed`
- `task.failed`
- `heartbeat`

### 12.2 统一数据结构

```json
{
  "task_id": "tsk_01...",
  "seq": 42,
  "trace_id": "trc_01...",
  "current_agent": "题库Agent",
  "progress": 46,
  "resource_type": "quiz",
  "content": "本次增量文本",
  "media_url": null,
  "finish_flag": false,
  "resource_ids": [],
  "profile_patch": null,
  "error": null
}
```

SSE 的 `id` 与 JSON 中的 `seq` 一致。前端按 `seq` 去重和排序，不以到达时间覆盖已完成状态。

### 12.3 两种流式客户端

- `/api/resource/progress/{task_id}` 使用浏览器 `EventSource`。
- `/api/chat/profile` 和 `/api/chat/qa` 是 POST 流，使用 `fetch` + `ReadableStream` + SSE parser。

POST 流在响应头返回 `X-Task-ID`，首个事件也必须包含 `task_id`。连接中断后前端使用任务快照恢复。

### 12.4 心跳与恢复

- 服务端每 15 秒发送 `heartbeat`。
- 前端 45 秒无事件视为连接异常。
- EventSource 重连携带 `Last-Event-ID`。
- 后端从 `task_events` 重放缺失事件。
- 若无法继续流式重放，前端调用 `GET /api/task/{task_id}` 获取累计快照。
- 只有 `task.failed.error.retryable=true` 才显示任务重试按钮。

## 13. 非流式响应与错误模型

成功响应：

```json
{
  "data": {},
  "trace_id": "trc_01..."
}
```

错误响应：

```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "智能体服务响应超时，请稍后重试。",
    "retryable": true,
    "details": null
  },
  "trace_id": "trc_01..."
}
```

固定错误码至少包括：

- `VALIDATION_ERROR`
- `NETWORK_UNAVAILABLE`
- `UPSTREAM_TIMEOUT`
- `UPSTREAM_REJECTED`
- `CONTENT_BLOCKED`
- `TASK_NOT_FOUND`
- `COURSE_NOT_READY`
- `MEDIA_MISSING`

## 14. 错误、重试与降级

- 参数错误显示在对应输入项旁，不弹全局模态框。
- 查询请求最多自动重试两次，采用指数退避。
- 生成提交不自动重复；显式重试调用幂等重试接口。
- AI 局部失败不得清空其他资源或已收到的流式内容。
- `CONTENT_BLOCKED` 不自动重试，要求用户调整输入。
- 媒体失败仅影响对应媒体卡片。
- 页面错误显示 `trace_id`，后端 JSON 日志关联 `user_id`、`task_id`、Agent 名称和错误码。
- 日志不得记录 API Key、完整授权头或用户密码。

## 15. 数据模型

### 15.1 核心表

- `users`：用户 ID、展示名、创建时间。
- `student_profiles`：六维 JSON、修订号、确认时间。
- `profile_messages`：画像对话消息、角色和任务 ID。
- `tasks`：任务类型、请求快照、状态、进度、错误、幂等键。
- `task_events`：任务序列号、事件类型、完整 payload 和创建时间。
- `resources`：用户、课程、类型、标题、内容、媒体 URL、来源任务。
- `learning_paths`：用户、课程、版本、状态。
- `learning_path_nodes`：顺序、阶段、难度、资源 ID、完成状态。
- `quiz_attempts`：题库资源、答案、逐题结果、分数。
- `learning_events`：行为类型、资源/节点、开始结束时间和元数据。
- `evaluation_reports`：分数、弱项、建议、关联路径版本。
- `courses`：课程名、slug、文件根目录和索引状态。
- `course_documents`：章节、文件类型、路径、哈希和预览信息。

### 15.2 任务状态

固定状态：

- `queued`
- `running`
- `partial_success`
- `succeeded`
- `failed`

最终资源和任务状态在同一数据库事务中提交，避免任务完成但资源列表为空。

## 16. 课程文件处理

正式文件放入：

```text
backend/data/courses/<course-slug>/...
```

每个课程可以先提供只包含名称和 slug 的轻量课程配置。课程配置与正式课程正文是两个概念：

- `content_ready=false` 表示课程可用于 Mock 任务演示，但尚无可浏览的正式知识库正文。
- `is_demo=true` 只允许在 Mock 模式展示，并在课程选择器中明确标注“演示”。
- Remote 模式不自动暴露演示课程，除非队友服务明确声明支持该课程。

索引器按目录生成章节树，使用文件哈希识别更新。支持的输入类型：PDF、DOCX、PPTX、Markdown、TXT、常见代码文件、图片和浏览器可播放视频。

- PDF、图片、文本、代码和兼容视频提供内联预览。
- DOCX/PPTX 提供安全文本预览和原文件下载；不承诺像素级还原 Office 排版。
- 没有真实文件时，课程可以出现在 `/api/course/list` 中，但必须返回 `content_ready=false`；知识库页面显示“课程资料未同步”，不得生成伪造章节或正文。
- Mock Provider 可基于 `is_demo=true` 的课程元数据产生明确标注的演示资源，从而使前端流程在真实 Agent 和课程文件到位前仍可验收。
- 自动化测试可使用隔离的小型测试夹具，但测试内容不得进入正式数据库或正式截图。

## 17. 学习路径与评估闭环

1. 用户确认六维画像。
2. 用户按课程和弱项生成资源。
3. 学习路径接口返回有序节点，每个节点绑定资源 ID。
4. 用户浏览资源、完成节点或提交题库，前端写入学习事件。
5. 评估接口汇总正确率、资源浏览时长和高频提问弱项。
6. 评估页面展示优化建议。
7. 用户点击“一键更新学习计划”，`POST /api/eval/apply` 创建新版路径。

## 18. 测试策略

### 18.1 前端

使用 Vitest 和 Testing Library 覆盖：

- 用户初始化和路由守卫。
- SSE reducer 的排序、去重、完成和失败。
- 六维画像固定字段渲染。
- Markdown、代码、媒体和空状态。
- 题库提交与逐题结果。
- 错误码到 UI 的映射。

### 18.2 后端

使用 pytest 和 HTTPX 覆盖：

- SQLite repositories 和事务。
- API 请求/响应 schema。
- 六维画像校验。
- 幂等任务创建。
- SSE 顺序、心跳、事件重放和任务快照。
- Mock Provider 的可复现事件。
- Remote Provider 的事件映射与超时。
- 题库判分、学习事件和评估应用。
- 课程目录扫描与路径安全。

### 18.3 契约

- FastAPI OpenAPI 是接口唯一来源。
- 前端类型由 OpenAPI 生成。
- CI/本地检查生成结果是否与规范一致。

### 18.4 端到端

Playwright 必须跑通：

1. 新用户登录。
2. 流式画像对话。
3. 确认画像。
4. 生成五类资源并观察独立进度。
5. 查看资源详情并提交练习。
6. 查看更新后的学习路径。
7. 打开全局答疑并接收流式内容。
8. 查看评估并应用新计划。
9. 刷新页面后恢复历史资源和任务。
10. 模拟 SSE 断线、任务失败和重试。

### 18.5 工程门禁

- 删除 `next.config.mjs` 中的 `ignoreBuildErrors`。
- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm test:e2e`
- `pytest`
- `docker compose config`
- Docker 健康检查

## 19. 截图与演示材料

至少输出以下 PC 截图：

- 登录页
- 画像流式采集页
- 资源生成进行中
- 资源生成结果
- 题库在线作答
- 学习路径
- 全局答疑抽屉
- 学习评估
- 知识库或真实的“资料未同步”状态
- 网络失败和 AI 失败状态

Playwright 录制主流程视频和 trace。截图、视频和运行日志统一放在 `artifacts/` 或文档约定目录，文件名稳定，便于成员 C 引用。

## 20. 部署设计

Docker Compose 包含：

- `web`：Next.js standalone 产物。
- `api`：FastAPI + Uvicorn，单 worker。
- `nginx`：统一域名，转发 `/api`、`/media` 和前端页面。
- volumes：SQLite 数据库、媒体结果和课程文件。

同时提供：

- `start.ps1`：Windows 本地启动。
- `start.sh`：Linux 本地启动。
- `.env.example`：无真实密钥的完整配置模板。
- `docker-compose.yml`：云端一键部署。

简易 `user_id` 登录不是安全认证。该部署适合课程项目、答辩和受控访问，不应在无额外访问控制的情况下作为公网多租户服务。

## 21. 分阶段实施

### 阶段 1：基础架构与画像

- 清理论坛与 Coze 的活跃入口。
- 重建应用外壳、登录和路由守卫。
- 建立 FastAPI、SQLite、错误模型和 OpenAPI。
- 完成六维画像流、确认接口和 Mock Provider。

### 阶段 2：资源与学习路径

- 完成五类资源任务、SSE、任务恢复和历史资源。
- 完成 Markdown、代码、思维导图、题库、媒体组件。
- 完成学习路径、资源深链、答题提交和学习事件。

### 阶段 3：答疑、评估与交付

- 完成全局答疑抽屉。
- 完成评估报告和计划应用。
- 完成真实课程目录扫描框架。
- 完成 Remote Provider 接口、Docker、文档、截图和演示材料。

## 22. 最终验收标准

1. 活跃网站与新 FastAPI 不包含论坛入口、路由或数据模型。
2. Coze 源文件、路由、SDK 和依赖从前端工程中移除。
3. 七个业务场景在 Mock 模式完整可运行；演示课程和演示资源均有明确标识。
4. 所有 AI 内容均流式呈现；所有生成任务显示 Agent 和进度。
5. 网络中断后可凭 `task_id` 恢复；重复重试不创建重复任务。
6. 切换 Remote 模式只需环境变量与适配器配置，不修改页面业务代码。
7. 重启服务后用户、画像、任务、资源和学习记录仍存在。
8. 所有工程门禁和端到端关键路径通过。
9. 三种 PC 视口无内容重叠、横向溢出或空白主场景。
10. 交付代码、接口文档、组件文档、启动脚本、部署说明、截图和演示材料。
11. 正式知识库内容验收以用户提供真实文件为前提；文件缺失时空状态即为正确行为。

## 23. 跨团队接入点

队友接入真实 Agent 时只需实现 `AgentProvider` 契约：

- 画像流
- 多资源生成流
- 答疑流
- 路径规划
- 评估报告

网关负责校验、标准化、持久化和向前端发送 SSE。队友不需要了解 React 组件，前端也不需要了解 LangGraph 内部节点。

接入前必须提供：

- 服务基础 URL。
- 鉴权方式。
- 超时约束。
- 上游事件示例。
- 每个事件和网关固定字段的映射。
- 媒体 URL 的可访问范围与生命周期。
