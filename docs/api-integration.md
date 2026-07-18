# FastAPI 网关与 Agent 接口接入

前端只调用 FastAPI 网关，不直接调用 LangGraph、资源 Agent 或媒体服务。网关负责固定字段校验、任务持久化、SSE 序号、错误映射和 SQLite CRUD。

本地默认地址为 `http://127.0.0.1:8000`，Docker/Nginx 下使用同源 `/api` 与 `/media`。

## 通用响应

普通成功响应：

```json
{
  "data": {},
  "trace_id": "2c5a8b..."
}
```

普通失败响应：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "可直接展示给用户的说明",
    "retryable": false,
    "details": null
  },
  "trace_id": "2c5a8b..."
}
```

常见错误码包括 `VALIDATION_ERROR`、`CONTENT_BLOCKED`、`TASK_NOT_FOUND`、`COURSE_NOT_READY`、`UPSTREAM_TIMEOUT`、`UPSTREAM_UNAVAILABLE`、`UPSTREAM_REJECTED`、`QA_GENERATION_FAILED` 和 `NETWORK_UNAVAILABLE`。前端必须以 `retryable` 决定是否显示重试按钮，不根据消息文本猜测。

## 网关端点

| 方法与路径 | 请求 | 主要返回 |
|---|---|---|
| `GET /health` | 无 | API 与数据库状态 |
| `GET /api/user/info?user_id=` | 查询参数 | 用户存在状态、六维画像、确认状态 |
| `POST /api/chat/profile` | `user_id`, `chat_text` | POST SSE；响应头 `X-Task-ID` |
| `POST /api/profile/confirm` | `user_id` | 已确认用户与画像 |
| `GET /api/course/list` | 无 | 课程摘要数组 |
| `GET /api/course/base?course_name=` | 查询参数 | 章节、文档元数据和文本预览 |
| `POST /api/resource/generate` | 用户、课程、薄弱点、资源类型 | `202` 和 `task_id` |
| `GET /api/resource/progress/{task_id}` | `after_seq` 或 `Last-Event-ID` | 可重放资源 SSE |
| `GET /api/resource/list?user_id=&course_name=` | 查询参数 | 已持久化资源摘要 |
| `GET /api/resource/detail/{resource_id}` | 路径参数 | 固定判别联合资源正文 |
| `GET /api/task/{task_id}` | 路径参数 | 任务快照、进度、结果和错误 |
| `POST /api/task/{task_id}/retry` | 无 | 新 `task_id` 和原任务关联 |
| `POST /api/quiz/submit` | 用户、资源和答案映射 | 分数与逐题结果 |
| `POST /api/learning/events` | 用户、课程和事件数组 | 接受数量 |
| `GET /api/path/get?user_id=&course_name=` | 查询参数 | 有序学习路径 |
| `POST /api/chat/qa` | 用户、问题、回答模式 | POST SSE；响应头 `X-Task-ID` |
| `GET /api/eval/report?user_id=&course_name=` | 查询参数 | 分数、薄弱点和建议 |
| `POST /api/eval/apply` | `report_id` | 幂等返回应用后的路径版本 |
| `GET /api/memory/report?user_id=&course_name=` | 查询参数 | 记忆保持度估计、先修知识提示和最多三条复习建议 |

## 画像

请求：

```http
POST /api/chat/profile
Content-Type: application/json
Accept: text/event-stream

{"user_id":"student-001","chat_text":"我正在学 ROS2，基础较弱，希望两周掌握通信模型。"}
```

画像字段固定为：

```json
{
  "knowledge_foundation": "...",
  "cognitive_style": "...",
  "weak_points": ["..."],
  "learning_pace": "...",
  "content_preferences": ["..."],
  "short_term_goal": "..."
}
```

前端只合并 `profile.patch.profile_patch` 中这六个字段，不解析额外自然语言字段。画像确认前，答疑、路径和评估等依赖画像的能力可返回 `VALIDATION_ERROR`。

## 资源生成

提交示例：

```http
POST /api/resource/generate
Idempotency-Key: student-001-ros2-20260711
Content-Type: application/json

{
  "user_id": "student-001",
  "course_name": "ROS2 机器人开发",
  "weak_point": "发布订阅与 QoS",
  "resource_type_list": ["handout", "mindmap", "quiz", "code", "video"]
}
```

资源枚举固定为 `handout | mindmap | quiz | code | video`。同一 `Idempotency-Key` 的重复提交返回已有任务并把 `deduplicated` 设为 `true`。

接受响应：

```json
{
  "data": {
    "task_id": "6f8d...",
    "status": "queued",
    "deduplicated": false,
    "retry_of_task_id": null
  },
  "trace_id": "2c5a8b..."
}
```

随后订阅：

```http
GET /api/resource/progress/6f8d...
Accept: text/event-stream
Last-Event-ID: 17
```

也可以用 `?after_seq=17`。网关持久化每个事件，断线后从较大的 `Last-Event-ID`/`after_seq` 继续，客户端必须按 `seq` 去重。

## SSE 契约

事件名固定为：

```text
task.started
agent.started
task.progress
content.delta
profile.patch
media.ready
resource.ready
task.completed
task.failed
heartbeat
```

每个 `data` 都是完整 JSON 对象：

```json
{
  "event": "content.delta",
  "task_id": "6f8d...",
  "seq": 18,
  "trace_id": "2c5a8b...",
  "current_agent": "讲义Agent",
  "progress": 42,
  "resource_type": "handout",
  "content": "增量 Markdown",
  "media_url": null,
  "finish_flag": false,
  "resource_ids": [],
  "profile_patch": null,
  "error": null,
  "demo_mode": false
}
```

规则：

- `content.delta` 只能追加，不能替换前文。
- `progress` 为 `0..100`，`current_agent` 是当前执行者名称。
- `task.completed` 必须有 `progress=100`、`finish_flag=true`；资源任务同时返回完整 `resource_ids`。
- `task.failed` 在流内携带统一 `error`，已完成的资源保持可见。
- `heartbeat` 不改变业务状态。
- `demo_mode=true` 表示远程失败后的显式 Mock 降级，不能伪装为真实 Agent 输出。

## 资源详情

`GET /api/resource/detail/{resource_id}` 按 `resource_type` 返回下列 payload：

- `handout`: `{ "markdown": "..." }`
- `mindmap`: `{ "nodes": [{ "id": "n1", "label": "...", "parent_id": null }] }`
- `quiz`: `{ "questions": [{ "id", "question_type", "prompt", "options", "answer", "explanation" }] }`
- `code`: `{ "language", "code", "description" }`
- `video`: `{ "summary", "poster_url", "duration_seconds" }`

所有资源都有可空的 `media_url`。本地 Mock 不生成 PNG 或 MP4，因此返回 `media_url: null`；真实 Agent 应返回浏览器和 Nginx 可访问的 HTTP(S) 或同源路径。前端不得根据标题或文本拼接素材 URL。

## 答疑

```http
POST /api/chat/qa
Content-Type: application/json
Accept: text/event-stream

{"user_id":"student-001","question":"QoS 的可靠性策略如何选择？","answer_mode":"image"}
```

`answer_mode` 固定为 `text | image | video`。网关把已确认的六维画像传给 Agent。文字通过多个 `content.delta` 流式返回；媒体通过 `media.ready` 返回 `media_url`。没有真实素材时允许 URL 为 `null`，此时卡片展示等待接入状态。

## 学习事件与评估

学习事件类型固定为 `resource_opened`、`resource_closed`、`path_node_completed`、`question_asked`、`video_progress`。评估服务基于已持久化的答题成绩、路径节点和高频问题构造证据，前端不提交分数。

`POST /api/eval/apply` 只接收 `report_id`。相同报告重复应用时返回同一路径版本，不重复创建计划。

## 学习记忆助手

`GET /api/memory/report` 从已持久化的测验、学习事件、路径完成状态和课程知识 DAG 计算“学习记忆保持度估计”。每个知识点返回第 0、1、3、7 天的估计曲线、风险等级、复习建议和可选的先修知识提示；最多返回三条今日行动建议。该结果是用于安排复习顺序的解释性估计，不是心理测量结论。

新用户或尚无可映射学习行为时仍返回 200，并在 `has_personal_evidence=false` 与摘要中明确标记为课程起步建议。前端不得把起步建议描述为个人学习结论。

## Remote Agent 接入

通过环境变量启用：

```dotenv
AGENT_MODE=remote
REMOTE_AGENT_BASE_URL=https://agent.example.com
REMOTE_AGENT_API_KEY=secret
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
REMOTE_PROFILE_PATH=/profile/stream
REMOTE_RESOURCES_PATH=/resources/stream
REMOTE_QA_PATH=/qa/stream
REMOTE_PATH_PATH=/path
REMOTE_EVALUATION_PATH=/evaluation
```

Bearer 鉴权仅在 `REMOTE_AGENT_API_KEY` 非空时发送。三个流式端点接收 POST JSON 并返回 SSE JSON；路径和评估端点返回 JSON，可直接返回正文或 `{ "data": ... }` 包装。

### 上游画像流

输入包含 `user_id`、`chat_text`、`current_profile`。事件 `type` 为：

- `agent`: `name`, `progress`
- `delta`: `text`, `progress`
- `profile`: 完整六维 `profile`, `progress`
- `progress`: `progress`
- `done`
- `error`: `code`, `message`, `retryable`, `details`
- `heartbeat`

### 上游资源流

输入包含 `user_id`、`course_name`、`weak_point`、`resource_type_list`。事件 `type` 为 `agent | delta | progress | resource | done | error`。除 `done/error` 外必须提供或继承有效 `resource_type`；`resource` 事件必须包含：

```json
{
  "type": "resource",
  "name": "题库Agent",
  "progress": 95,
  "resource_type": "quiz",
  "resource": {
    "resource_type": "quiz",
    "title": "QoS 自测题",
    "payload": { "questions": [] },
    "media_url": null
  }
}
```

网关会用资源判别联合再次校验 payload；类型不一致或字段缺失返回 `UPSTREAM_REJECTED`。

### 上游答疑流

输入包含 `user_id`、`question`、`answer_mode`、完整 `profile`。事件 `type` 为 `agent | delta | media | progress | done | error | heartbeat`。`media` 的 `kind` 只能是 `image` 或 `video`，URL 字段名为 `url`，说明文本为可选 `text`。

### 上游路径与评估

- `/path` 输入用户、课程、画像和资源摘要；返回 `{ "nodes": [{ "stage_name", "difficulty", "resource_id" }] }`。
- `/evaluation` 输入用户、课程和 `evidence`；返回 `theory_score`、`practice_score`、`weak_points`、`recommended_changes`。

上线前由后端成员用真实样例逐字段验证。未知事件、无效百分比、无效 JSON 和不符合固定模型的数据都会被拒绝；前端不为上游临时字段增加旁路解析。
