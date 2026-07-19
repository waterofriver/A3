# 智学引擎 / Zhixue Engine

> 面向高等教育的多智能体个性化学习系统

智学引擎面向高校学生“资源多而无序、内容难以匹配个人基础、课堂节奏难以兼顾个体差异”的学习场景，将对话式学习画像、多智能体资源生成、知识图谱学习路径、智能答疑、学习评估与记忆保持组织成一个可持续迭代的学习闭环。

项目以“机器人与安全”专业课程为真实知识库样例。当前仓库包含可运行的 Next.js 前端、FastAPI 网关、SQLite 数据层、本地八个 Agent 角色模块、Mock/Local/Remote 三种 Agent 模式、课程资料、测试、部署配置和答辩演示产物，可用于本地演示或 Linux/Docker 云部署。八个角色中有七个已由 `RealAgentProvider` 直接接入活动 API；`Supervisor` 当前保留为已实现、可测试的本地编排模块，尚未进入网关调用链。

## 项目价值

传统教学平台通常提供统一内容和固定顺序，学生仍需自行判断“缺什么、先学什么、用什么形式学、学完是否掌握”。智学引擎围绕这些问题提供以下能力：

- 用自然语言对话替代表单，持续更新不少于六个维度的学习画像。
- 按学生的课程、薄弱点、目标和内容偏好并行生成多种学习资源。
- 以课程知识 DAG、画像和学习证据共同规划学习路径，而不是简单排列资源。
- 将练习、资源浏览、路径进度和提问记录沉淀为评估与复习依据。
- 使用统一任务事件展示 Agent、进度、局部失败和可重试状态，避免长时间白屏。

项目不把 Mock 数据或接口占位描述为真实多模态生成成果。Mock 模式用于可重复的完整流程演示；Local 模式调用仓库内本地 Agent；Remote 模式对接外部多智能体服务。真实图片、视频或远程模型输出必须来自实际课程素材或已配置的 Agent 服务。

## 赛题需求与实现对应

| 赛题能力 | 当前实现 | 主要证据入口 |
|---|---|---|
| 对话式学习画像 | 通过 SSE 流式对话抽取知识基础、认知风格、薄弱点、学习节奏、内容偏好、短期目标六个稳定维度，支持增量修订与确认 | `Course-Agent/creative/components/profile/`、`/api/chat/profile` |
| 多智能体资源生成 | 平台契约和 Mock 演示覆盖讲义、思维导图、题库、代码案例、视频五类资源；不同 Agent 独立进度、局部失败保留和单任务重试 | `Course-Agent/creative/components/resources/`、`backend/agent/`、`/api/resource/*` |
| 个性化路径与推送 | 结合画像、知识 DAG、薄弱点和已生成资源形成有序学习阶段，并将资源绑定到路径节点 | `Course-Agent/creative/components/learning-path/`、`/api/path/get` |
| 智能辅导（加分项） | 全局答疑抽屉支持文字、Mermaid 图解和视频模式；以流式文本和媒体就绪事件呈现 | `Course-Agent/creative/components/qa/`、`/api/chat/qa` |
| 学习效果评估（加分项） | 汇总练习、路径完成、学习事件和提问证据，展示评分、薄弱点与计划调整建议 | `Course-Agent/creative/components/evaluation/`、`/api/eval/*` |
| 记忆保持与主动复习 | 基于学习证据和知识图谱估计记忆健康度，定位先修知识并给出短时复习建议 | `Course-Agent/creative/components/memory/`、`/api/memory/report` |
| 真实课程数据 | 提供完整课程 DAG 和 Markdown/PDF/DOCX/PPTX/视频等资料，启动时同步、索引并只读预览 | `knowledge_base/`、`/api/course/*` |
| 进度与稳定性 | SSE 心跳、事件序号去重、任务快照、断线恢复、幂等键、错误码和重试边界 | `lib/sse/`、`backend/app/tasks/` |

## 已实现功能

### 学习入口与画像

- 沉浸式登录展示页：Five-chapter 全屏展示、Three.js 学习核心、左键拖动和缓慢自转。
- 简易 `user_id` 登录及新用户画像页、已确认用户工作台分流。
- 六维画像对话采集、流式内容、画像 patch、历史恢复和画像确认。

### 多智能体资源工作台

- 讲义、思维导图、题库、代码案例、视频五类稳定资源枚举。
- 多资源并行任务、当前 Agent、总进度、分资源进度和部分成功状态。
- 讲义 Markdown、代码高亮、Mermaid/节点图、在线答题、视频与媒体卡片渲染。
- 任务快照、SSE 断线恢复、失败重试和历史资源查询。

### 学习闭环

- 五阶段个性化学习路径和资源深链。
- 选择、填空和编程题交互，提交后返回逐题结果与薄弱点。
- 文字、图解、短视频三种模式的画像感知答疑。
- 多维学习评估、薄弱点统计和幂等的一键更新学习计划。
- 学习记忆助手：记忆健康度、优先复习知识、先修知识定位和短时复习建议。

### 课程、工程与异常状态

- 真实 Markdown、PDF、DOCX、PPTX、图片、代码和视频资料索引与只读浏览。
- Mock/Local/Remote Agent 显式切换；Remote 失败默认不会静默伪装成 Mock 成功。
- 统一加载、空状态、离线提示、错误边界、错误码和 `trace_id`。
- Windows/Linux 启动脚本、Docker Compose、Nginx 同源代理、SSE 配置和 SQLite 持久卷。

## 核心创新

1. **从内容生成升级为学习闭环**：画像、资源、路径、学习行为、评估和记忆互相提供证据，而不是多个孤立 AI 页面。
2. **可观察的多 Agent 协同**：统一 `GatewayEvent` 展示当前 Agent、资源类型、进度、媒体和错误；单个资源失败不会清空其他结果。
3. **知识 DAG 与学习证据结合**：课程先修关系约束路径顺序，练习和行为证据驱动薄弱点诊断与复习优先级。
4. **演示与真实能力显式分层**：Mock 保证答辩流程可重复，Local/Remote 提供真实模型接入；`demo_mode` 和媒体空状态避免能力混淆。
5. **面向长任务的交互设计**：SSE 增量输出、心跳、序号去重、任务快照、幂等重试和独立进度降低等待焦虑。
6. **课程证据可追溯**：生成上下文来自实际课程 DAG 和资料目录；课程内容缺失时展示空状态，不伪造正文。

## 系统架构

```text
┌────────────────────────────── Browser ──────────────────────────────┐
│ Next.js 15 / React 19                                              │
│ 展示页 · 画像 · 资源 · 路径 · 答疑 · 评估 · 记忆 · 知识库          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ JSON + SSE
                         Nginx 同源代理
                                │
┌──────────────────────── FastAPI Gateway ────────────────────────────┐
│ Pydantic 契约 · 任务管理 · 错误标准化 · 课程索引 · 媒体安全路由     │
│                                                                    │
│  AgentProvider                                                     │
│  ├─ MockAgentProvider      可重复的本地演示                         │
│  ├─ RealAgentProvider      本地 Agent 模块 + DeepSeek              │
│  └─ RemoteAgentProvider    外部多智能体服务适配                     │
└───────────────────────┬──────────────────────┬─────────────────────┘
                        │                      │
                 SQLite / Alembic       knowledge_base/
                 用户与学习证据          课程 DAG 与真实资料
```

前端不持久化画像、学习记录或资源正文。FastAPI 负责契约校验、任务事件、持久化和媒体路径安全；SQLite 部署保持单 API worker。Remote Agent 的原始事件必须先映射到固定网关契约，再交给前端。

## 核心学习流程

```text
登录
  -> 对话采集并确认六维画像
  -> 选择课程与薄弱知识点
  -> 多 Agent 并行生成五类资源
  -> 形成个性化学习路径并绑定资源
  -> 学习、答题、提问和记录行为
  -> 评估薄弱点、记忆保持度与先修缺口
  -> 调整路径和下一轮资源推荐
```

## 技术栈与开源组件

| 层级 | 技术 | 用途与协议 |
|---|---|---|
| Web | Next.js、React、TypeScript | 路由、组件和服务端构建；MIT |
| UI | Tailwind CSS、shadcn/ui、Radix UI、Lucide | 样式、可访问组件和图标；MIT/ISC |
| 可视化 | Three.js、React Flow、Recharts、Mermaid | 展示页粒子、路径图、评估图表和知识图解；MIT |
| 数据请求 | TanStack Query、原生 Fetch/EventSource | 缓存、请求状态和 SSE |
| API | FastAPI、Pydantic、Uvicorn、HTTPX | 网关、Schema、ASGI 与远程调用；MIT/BSD |
| 数据 | SQLite、SQLAlchemy、Alembic | 持久化和迁移；Public Domain/MIT |
| 测试 | pytest、Vitest、Testing Library、Playwright、Axe | 单元、契约、浏览器和无障碍验证；MIT/Apache-2.0 |
| 部署 | Docker Compose、Nginx | 容器编排、同源代理和 HTTPS 接入 |
| 模型 | DeepSeek API（Local 模式） | 本地 Agent 的大模型推理；按服务条款配置 |

仓库代码许可证见 [LICENSE](LICENSE)。第三方依赖的准确版本以 `Course-Agent/creative/package.json`、`pnpm-lock.yaml`、`backend/pyproject.toml` 和 `backend/agent/requirements.txt` 为准；使用和再分发时应同时遵守各项目许可证与模型服务条款。

## 项目结构

```text
A3/
├── Course-Agent/creative/          # Next.js 活动前端
│   ├── app/                        # 登录与平台路由
│   ├── components/                 # 业务组件、共享状态和 UI 基础组件
│   ├── lib/                        # API、SSE、会话和运行时工具
│   ├── tests/                      # Vitest / Testing Library 测试
│   ├── e2e/                        # Playwright 端到端与视觉测试
│   ├── package.json
│   └── Dockerfile
├── backend/                        # FastAPI 网关与本地 Agent
│   ├── app/
│   │   ├── api/routes/             # 用户、画像、资源、路径、答疑、评估等 API
│   │   ├── agents/                 # Mock / Local / Remote Provider
│   │   ├── repositories/           # SQLite 数据访问
│   │   ├── schemas/                # Pydantic 请求、响应和事件契约
│   │   ├── services/               # 业务服务、知识库同步和课程索引
│   │   ├── tasks/                  # 长任务与事件管理
│   │   └── db/                     # SQLAlchemy 模型和连接
│   ├── agent/                      # 八类本地学习 Agent
│   ├── migrations/                 # Alembic 迁移
│   ├── tests/                      # pytest API、服务和契约测试
│   ├── pyproject.toml
│   └── Dockerfile
├── knowledge_base/                 # 课程 DAG、真实资料、校验和索引工具
├── infra/nginx/                    # Web/API/媒体同源反向代理和 SSE 配置
├── docker-compose.yml              # Web + API + Nginx + 持久卷
├── start.ps1 / start.sh            # Windows / Linux 本地启动
├── .env.example                    # 无密钥环境变量模板
└── LICENSE
```

## 环境要求

- Windows 10/11 + PowerShell 5.1，或常见 Linux 发行版 + Bash。
- Python 3.12（后端声明最低 Python 3.11）。
- Node.js 22、Corepack 和 pnpm。
- Docker Desktop / Docker Engine 与 Compose 插件（Docker 方式）。

## 快速开始

### Windows

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

脚本会创建 `backend/.venv`、安装依赖、执行 Alembic 迁移并启动 API/Web。若默认端口被占用，脚本会选择可用端口并打印实际地址；按 `Ctrl+C` 停止两个子进程。

### Linux

```bash
cp .env.example .env
chmod +x start.sh
API_PORT=8000 WEB_PORT=3000 ./start.sh
```

默认入口：

- Web：`http://127.0.0.1:3000/login`
- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

## Agent 模式与环境变量

演示模式：

```dotenv
AGENT_MODE=mock
ALLOW_MOCK_FALLBACK=false
```

本地 Agent：

```dotenv
AGENT_MODE=local
DEEPSEEK_API_KEY=replace-with-secret
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
```

远程 Agent：

```dotenv
AGENT_MODE=remote
REMOTE_AGENT_BASE_URL=https://agent.example.com
REMOTE_AGENT_API_KEY=replace-with-secret
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
```

远程模式默认不静默降级。只有显式设置 `ALLOW_MOCK_FALLBACK=true` 时才使用 Mock 兜底，事件会持续携带 `demo_mode=true`。所有密钥只写入未跟踪的 `.env` 或云平台 Secret。

## 课程知识库

权威课程源位于 `knowledge_base/`。知识点在 `knowledge_dag.json` 中定义，资料按知识点 ID 放入 `materials/<knowledge_point_id>/`。后端启动时将课程同步到运行时数据目录并建立索引；不要手工维护 `backend/data/courses/`。

```bash
cd knowledge_base
python validate_knowledge_base.py
python build_knowledge_base.py   # 可选：生成 metadata 和 resource_index
```

详细字段、目录规范和交付清单见 [知识库 README](knowledge_base/README.md)。

## Docker 与云部署

```bash
cp .env.example .env
docker compose config
docker compose up --build -d
curl http://127.0.0.1:8080/health
```

Compose 包含 API、Next.js standalone Web、Nginx 和持久卷。生产环境建议：

- 使用域名和 HTTPS，宿主机 Nginx或云负载均衡反代到 Compose 入口。
- 只开放 80/443，避免直接暴露 API、SQLite 或内部容器端口。
- 保留 `/api/` 的 SSE 关闭缓冲和 300 秒读取超时设置。
- 备份 `zhixue-data` 持久卷中的 SQLite 数据。
- 将正式域名加入 `WEB_ORIGINS`，避免跨域和混合内容问题。

## 测试与质量检查

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e
docker compose config --quiet
```

测试覆盖后端仓储与 API、SSE 顺序和恢复、Mock/Remote/Local Provider、前端业务组件、错误状态、关键浏览器流程、响应式布局和无障碍检查。仓库中的历史验证结果仅代表对应提交；发布前应在目标环境重新执行。

## 安全、可靠性与内容边界

- Pydantic Schema、固定资源枚举和网关事件契约限制上游自由输出。
- `CONTENT_BLOCKED`、超时、网络中断、媒体缺失和课程未就绪都有明确错误状态。
- 课程浏览与预览只读取仓库资料；无文件时显示“未同步”，不会在知识库页面伪造课程正文。Mock 资源正文则属于显式标记的演示数据。
- Remote Agent 输出仍需由实际模型服务承担事实核验、内容安全和审计；本仓库不声明已达到可量化的防幻觉准确率。
- 当前 `user_id` 登录用于比赛演示和受控环境，不是公网多租户身份认证。正式上线需增加账号认证、权限控制、限流和审计。
- SQLite 适合当前单机演示和单 worker 部署；大规模并发场景应评估独立数据库与任务队列。

## AI Coding 使用说明

本项目开发过程中使用了 OpenAI Codex 等 AI Coding 工具辅助需求梳理、代码实现、测试诊断、浏览器验证和文档整理。AI 工具输出不作为功能完成的唯一依据；最终说明以仓库源码、接口契约、测试结果和人工审阅为准。使用第三方 AI 服务时应遵守比赛规则、服务条款与数据安全要求。

## 当前外部依赖与限制

仓库已提供完整前端、FastAPI 网关、SQLite、课程知识库、本地 Agent、Mock/Remote 接口、测试和部署框架。以下内容需要在实际交付环境中另行配置或验证：

- 模型 API Key 或远程 Agent 服务 URL、鉴权方式和真实事件样例。
- 图片、教学视频等真实媒体生成服务及其 `media_url` 生命周期。
- 正式域名、HTTPS 证书、云平台网络、镜像仓库和备份策略。
- 目标服务器上的完整容器构建、性能、安全和内容质量验收。
- Local 模式尚未接入独立 CodeAgent；`code` 请求当前由 `ReferenceAgent` 生成拓展阅读并以 `handout` 返回。
- `Supervisor` 虽已实现并有独立测试，但当前 `RealAgentProvider` 没有调用它，活动网关由明确 API 路由直接分派任务。
