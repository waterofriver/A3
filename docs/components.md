# 前端页面与组件边界

本文描述 `Course-Agent/creative` 中活动前端的责任边界。前端负责触发任务、消费 JSON/SSE、维护当前页面展示态和渲染后端返回数据；用户画像、学习记录、任务、资源和课程正文均由 FastAPI + SQLite 持久化。

## 页面边界

| 路由 | 页面职责 | 主要组件 | 数据来源 |
|---|---|---|---|
| `/login` | 保存本地 `user_id`，查询用户状态并分流 | `LoginPanel` | `GET /api/user/info` |
| `/profile` | 对话采集和确认六维画像 | `ProfilePage`、`ProfileChat`、`ProfilePanel` | `POST /api/chat/profile` SSE、`POST /api/profile/confirm` |
| `/workspace` | 提交五类资源、恢复任务、展示进度与结果 | `GenerationForm`、`TaskRail`、`ResourceGrid` | resource/task/course APIs |
| `/resources/[resourceId]` | 单资源阅读、答题和学习行为上报 | `ResourceCard`、`QuizPlayer` | resource/quiz/learning APIs |
| `/path` | 展示画像摘要和五阶段学习路线 | `ProfileSummary`、`LearningPathGraph` | `GET /api/path/get` |
| `/evaluation` | 展示评分、薄弱点、建议并更新计划 | `EvaluationPageContent`、`ScorePanel`、`WeaknessChart`、`PlanChanges` | eval APIs |
| `/knowledge` | 只读浏览真实课程目录和文档 | `KnowledgePageContent`、`KnowledgeTree`、`DocumentPreview` | course APIs |

`AppShell` 只负责全局导航、在线状态提示、Mock/降级标识和 `QaDrawer` 挂载。业务页面不把自身请求状态写入全局壳层。`SessionGuard` 只判断本地会话是否存在，不承担后端权限控制。

## 公共业务组件

| 组件 | 输入与输出 | 所有权规则 |
|---|---|---|
| `ProfileChat` | `messages`、`isStreaming`、`onSend(text)` | 只渲染对话和发出发送命令，不解析画像 JSON |
| `ProfilePanel` | 固定 `StudentProfileData` 六维字段 | 字段名由后端契约决定；不推断自定义字段 |
| `AgentProgress` | `progress`、`currentAgent`、状态文本 | 统一进度可视化；不得自行模拟后台进度 |
| `GenerationForm` | 课程、薄弱点、资源类型选择；提交 `GenerationValues` | 表单只做输入校验，资源缓存和任务由页面协调 |
| `TaskRail` | 任务状态、分类型进度、重试回调 | 已成功资源在其他类型失败时继续可见 |
| `ResourceGrid` | 资源列表与加载状态 | 列表布局，不解析具体资源 payload |
| `ResourceCard` | 判别联合 `ResourceDetail` | 根据 `resource_type` 选择唯一渲染器 |
| `QaDrawer` | `open`、`userId`、可替换的流函数 | 全局保持当前问答轮次；文字增量和媒体事件分开渲染 |
| `LearningPathGraph` | 有序路径节点和节点点击回调 | 图形布局只消费后端顺序，不重新规划学习路径 |
| `KnowledgeTree` | 章节数组、当前文档和选择回调 | 只展示已索引真实文件 |

## 资源渲染契约

`ResourceCard` 的 `resource_type` 与 payload 是固定判别联合：

| `resource_type` | payload | 渲染器 |
|---|---|---|
| `handout` | `{ markdown }` | `MarkdownRenderer`，支持 GFM 表格、标题和代码块 |
| `mindmap` | `{ nodes[] }` | `MindMapViewer`，按 `id/parent_id` 布局 |
| `quiz` | `{ questions[] }` | `QuizPlayer`，支持选择、填空、编程题 |
| `code` | `{ language, code, description }` | `CodeBlock`，支持高亮和复制 |
| `video` | `{ summary, poster_url, duration_seconds }` | `MediaCard` / `VideoPlayer` |

`media_url` 始终允许为 `null`。Mock 模式不会在本地生成 PNG 或 MP4，渲染器必须显示“等待真实 Agent 返回素材”的真实状态。只有收到可访问 URL 后才显示预览与下载操作。

## 统一状态组件

- `ErrorNotice`：把 `VALIDATION_ERROR`、`CONTENT_BLOCKED`、`UPSTREAM_TIMEOUT`、`COURSE_NOT_READY`、`NETWORK_UNAVAILABLE` 等代码映射为稳定操作；仅 `retryable=true` 时提供重试。
- `EmptyState`：一个图标、标题、说明和最多一个动作，避免额外弹窗。
- `OfflineBanner`：浏览器离线时保持缓存内容可见。
- `ResourceErrorBoundary`：隔离单个资源渲染失败，不清空同任务中的其他资源。
- `AgentProgress`：同时显示进度数字、当前 Agent 和当前资源类型。

## 数据流和缓存

1. 页面用 `apiFetch` 获取普通 JSON，统一解包 `{ data, trace_id }`。
2. 画像和答疑使用 `postEventStream` 读取 POST SSE；资源任务使用 `EventSource` 订阅持久化 SSE。
3. `reduceTaskEvent` 按 `seq` 去重，累加 `content.delta`，合并 `profile.patch` 并保留终态。
4. TanStack Query 按用户、课程、资源和路径键缓存。相同课程重复进入时先展示缓存，再按需刷新。
5. 学习行为批量发送至后端；前端不把核心业务数据写入 localStorage。localStorage 仅保存简易 `user_id`。

## 布局规范

- 目标视口为 PC，主要验收尺寸为 1366x768、1440x900 和 1920x1080。
- 页面区段使用无框架布局；卡片只用于独立资源、重复数据项和抽屉内容，不在卡片中再嵌套装饰卡片。
- 固定格式控件使用稳定网格、最小宽度和滚动容器，动态文字不能改变工具栏或路径节点尺寸。
- 图标按钮使用项目已有 Lucide 图标和可访问名称；陌生图标提供 tooltip。
- Markdown、代码、图谱和媒体错误必须局部降级，不能导致整页白屏。
