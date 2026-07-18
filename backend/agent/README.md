# 智学引擎本地 Agent 使用手册

`backend/agent/` 是智学引擎的本地多智能体实现，包含学习画像、意图调度、路径规划和课程资源生成等八个角色模块。它通过 DeepSeek 兼容 API 完成模型推理，并由 `backend/app/agents/real.py` 中的 `RealAgentProvider` 适配到 FastAPI 网关契约。当前 Provider 直接调用其中七个角色；`Supervisor` 尚未接入活动 API 调用链。

本目录面向 Agent 开发者和网关集成者。系统普通运行、API 和部署说明见仓库根 [README](../../README.md) 与 [接口文档](../../docs/api-integration.md)。

## 与活动系统的关系

FastAPI 网关支持三种显式模式：

| `AGENT_MODE` | Provider | 用途 |
|---|---|---|
| `mock` | `MockAgentProvider` | 无模型密钥的确定性流程演示和自动化测试 |
| `local` | `RealAgentProvider` | 调用本目录八类 Agent 和 DeepSeek API |
| `remote` | `RemoteAgentProvider` | 对接外部团队的多智能体服务 |

Provider 选择位于 `backend/app/api/dependencies.py`。Local 模式依赖本目录代码、额外 Python 依赖、顶层课程知识库和有效模型密钥；Mock/Remote 模式不会在启动时强制导入本地 Agent 依赖。

```text
FastAPI route/service
        |
        v
AgentProvider interface
        |
        +-- MockAgentProvider
        +-- RealAgentProvider  ----> backend/agent/*
        +-- RemoteAgentProvider ---> external service
        |
        v
GatewayEvent / ResourceDraft / API Schema
```

本地 Agent 的 Pydantic 模型与网关 `app.schemas.*` 并不相同。`RealAgentProvider` 负责画像、资源、题型、路径和错误格式的双向转换，前端不直接依赖本目录数据模型。

## 目录结构

```text
backend/agent/
├── config.py                  # 根 .env 中的 DeepSeek 配置
├── requirements.txt           # 本地 Agent 额外依赖
├── models/
│   └── schemas.py             # Agent 共用模型和枚举
├── utils/
│   ├── llm_client.py          # 同步/异步调用、流式输出和重试
│   ├── json_parser.py         # 模型文本到结构化 JSON
│   ├── dag_loader.py          # 知识 DAG 加载
│   └── material_loader.py     # PDF/DOCX/PPTX/TXT 等资料提取
├── profile_agent/             # 六维学习画像
├── supervisor/                # 意图识别与会话调度
├── planner/                   # 知识 DAG 学习路径规划
├── doc_agent/                 # 个性化讲义
├── mindmap_agent/             # 思维导图
├── quiz_agent/                # 练习题
├── video_agent/               # 课程视频匹配与导览脚本
├── reference_agent/           # 课程内外拓展阅读
└── knowledge_base/            # 旧模板参考，不是运行时知识库
```

权威课程源目录是仓库顶层 [knowledge_base](../../knowledge_base/README.md)。

## 八类 Agent

### 1. ProfileAgent：对话式学习画像

| 项目 | 内容 |
|---|---|
| 输入 | 用户本轮自然语言、已有画像、对话历史 |
| 输出 | `ProfileExtractionResult` 和 `StudentProfile` |
| 核心维度 | 专业/年级与基础、知识掌握、认知风格、目标、薄弱点、学习节奏与兴趣 |
| 网关映射 | 固定为知识基础、认知风格、薄弱点、学习节奏、内容偏好、短期目标六个字段 |

模型返回的 `is_complete` 不是唯一判断依据。`RealAgentProvider` 会再次按已填维度计数，并在信息不足时提出针对性追问。

### 2. Supervisor：意图识别与调度

| 项目 | 内容 |
|---|---|
| 输入 | 用户文本和 `SessionState` |
| 输出 | `SupervisorResult`、意图、回复和更新后的会话状态 |
| 支持意图 | `extract_profile`、`plan_path`、`answer_question`、`generate_resource`、`evaluate`、`chitchat` |

Supervisor 提供本地 Agent 编排能力并有独立测试，但当前 `RealAgentProvider` 未导入或调用它。活动网关以明确 API 路由和 `AgentProvider` 方法直接分派画像、资源、路径、答疑和评估任务；因此不能把 Supervisor 描述为当前线上请求的实际总调度器。

### 3. PlannerAgent：个性化学习路径

| 项目 | 内容 |
|---|---|
| 输入 | `StudentProfile` 与 `KnowledgeDAG` |
| 输出 | `LearningPath` 和有序 `LearningPathNode` |
| 机制 | 先修依赖拓扑排序、学习深度/时长建议和资源类型推荐 |

网关将本地路径节点转换为 API 路径节点，并尽量绑定已生成的匹配资源。

### 4. DocAgent：讲义生成

| 项目 | 内容 |
|---|---|
| 输入 | 知识点、学习画像和课程材料文本 |
| 输出 | `DocResult` / `ResourceOutput<DocContent>` |
| 内容 | 结构化章节、Markdown 正文、关键点、总结和延伸阅读 |

网关使用 `_sections_to_markdown()` 将章节列表转换为前端 `handout.payload.markdown`。

### 5. MindMapAgent：知识图解

| 项目 | 内容 |
|---|---|
| 输入 | 知识点、画像和材料文本 |
| 输出 | `MindMapResult` / `MindMapContent` |
| 内容 | 根主题、节点树和 Mermaid 语法 |

网关当前主要传递标准化节点数组；前端使用节点图或 Mermaid 渲染并提供失败降级。

### 6. QuizAgent：个性化练习

| 项目 | 内容 |
|---|---|
| 输入 | 知识点、画像、材料文本和题目数量 |
| 输出 | `QuizResult` / `QuizContent` |
| 题型 | 单选、多选、判断、简答 |

`RealAgentProvider` 将本地题型映射到网关稳定题型，并生成前端需要的题目 ID、选项、答案和解析。

### 7. VideoAgent：视频匹配与导览

| 项目 | 内容 |
|---|---|
| 输入 | 知识点、画像、材料上下文和素材目录 |
| 输出 | `VideoResult`、本地视频路径、推荐理由和 `VideoScriptContent` |
| 行为 | 优先匹配课程中真实视频，并生成个性化导览脚本 |

VideoAgent 返回的是磁盘路径，不是浏览器 URL。网关必须验证文件存在，并转换为受控 `/media/...` URL；不得向前端暴露任意绝对路径。

### 8. ReferenceAgent：拓展阅读推荐

| 项目 | 内容 |
|---|---|
| 输入 | 知识点、画像、共享资料摘要和资料清单 |
| 输出 | `ReferenceResult`、课程内推荐、外部经典推荐和阅读顺序 |

课程内推荐的 `file_path` 同样需要由网关转换为安全 URL。外部推荐是模型建议，不等同于已下载或已核验的仓库资料。

## 前端资源类型映射

网关对前端稳定提供五种资源枚举：

| API `resource_type` | 本地处理 | 前端主要渲染 |
|---|---|---|
| `handout` | DocAgent | Markdown 讲义 |
| `mindmap` | MindMapAgent | 节点图 / Mermaid |
| `quiz` | QuizAgent | 在线题库 |
| `video` | VideoAgent | 视频卡片和播放器 |
| `code` | 当前 Local Provider 使用 ReferenceAgent 生成拓展阅读，并返回 `handout` | Mock/Remote 可提供真正代码案例 |

最后一行是当前实现边界：本地 `code` 分支尚未接入独立 CodeAgent，不能将其描述为真实代码生成 Agent。若新增 CodeAgent，应同时更新 `ResourceType`、`RealAgentProvider` 映射、API 契约测试和前端渲染测试。

## 共用数据模型

`models/schemas.py` 定义本地 Agent 的核心类型：

- 画像：`StudentProfile`、`KnowledgeBaseItem`、`WeakPoint`。
- 知识图谱：`KnowledgePoint`、`KnowledgeDAG`。
- 路径：`LearningPath`、`LearningPathNode`。
- 资源：`ResourceOutput`、`DocContent`、`MindMapContent`、`QuizContent`、`CodeContent`、`VideoScriptContent`。
- 会话：`TaskIntent`、`Task`、`SessionState`。

所有模型输出在进入网关前仍需经过转换和 API Schema 校验，不应直接序列化给前端。

## 环境配置

从仓库根 `.env.example` 复制 `.env`，Local 模式至少设置：

```dotenv
AGENT_MODE=local
DEEPSEEK_API_KEY=replace-with-secret
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
DEEPSEEK_TIMEOUT=120
DEEPSEEK_MAX_RETRIES=3
KNOWLEDGE_BASE_ROOT=knowledge_base
```

`config.py` 从仓库根 `.env` 加载配置。密钥不得写入 README、源码、日志或提交记录。

安装本地 Agent 额外依赖：

```bash
cd backend
python -m pip install -r agent/requirements.txt
```

VideoAgent 读取视频时长时依赖 `ffprobe`；Linux 可通过 FFmpeg 软件包提供：

```bash
sudo apt update
sudo apt install -y ffmpeg
```

## 网关集成

`RealAgentProvider` 实现以下活动网关方法：

- `stream_profile()`：画像对话流和画像 patch。
- `stream_resources()`：资源 Agent 事件与 `ResourceDraft`。
- `build_learning_path()`：路径草案。
- `stream_qa()`：文字、图解和视频答疑流。
- `build_evaluation()`：基于学习证据的评估草案。

网关负责：

1. 将 API 六维画像转换为本地 `StudentProfile`，并把结果映射回固定字段。
2. 将本地资源、题型和路径转换为稳定 API payload。
3. 产生统一 `GatewayEvent`，附带 `task_id`、`trace_id`、进度和错误信息。
4. 持久化用户、任务、资源、学习事件和评估结果。
5. 校验并转换本地媒体路径，避免路径穿越和磁盘路径泄露。

## 测试

本地 Agent 测试使用 Mock LLM client，不需要真实 API Key：

```bash
cd backend
python -m agent.profile_agent.test_profile_agent
python -m agent.supervisor.test_supervisor
python -m agent.planner.test_planner
python -m agent.doc_agent.test_doc_agent
python -m agent.mindmap_agent.test_mindmap_agent
python -m agent.quiz_agent.test_quiz_agent
python -m agent.video_agent.test_video_agent
python -m agent.reference_agent.test_reference_agent
```

活动网关的契约和回归测试位于 `backend/tests/`：

```bash
python -m pytest tests -q
```

使用真实 DeepSeek 服务前，应单独验证超时、重试、内容过滤、结构化解析失败和配额错误。不要用真实模型调用替代离线契约测试。

## 内容安全与错误边界

- 模型输出先经过 JSON 提取、本地 Pydantic 模型和网关 API Schema 校验。
- 解析失败、模型失败和媒体缺失应返回明确错误或空媒体状态，不能伪装成成功内容。
- 网关的 `CONTENT_BLOCKED` 不自动重试；上游内容安全策略仍需在真实模型服务侧配置和审计。
- 课程资料是生成依据，但不等于自动保证事实正确；正式使用应增加来源引用、人工复核和敏感内容审核。
- 日志不得记录 API Key、完整 Authorization 头或不必要的个人学习数据。

## 已知边界

- Local 模式的独立 CodeAgent 尚未接入，`code` 请求当前映射为拓展阅读。
- 外部经典阅读推荐需要人工核验书目真实性和可获得性。
- 图片和视频生成服务不是本地 Agent 的统一能力；视频优先使用课程已有文件。
- 简易 `user_id` 会话适合比赛演示，不是生产身份认证。

## 相关文档

- [项目总览](../../README.md)
- [FastAPI 网关与 Agent 接入](../../docs/api-integration.md)
- [课程知识库搭建](../../knowledge_base/README.md)
- [部署与环境配置](../../docs/deployment.md)
