# 智学引擎 / Zhixue Engine

> 多智能体个性化学习系统

智学引擎是一个面向 PC 演示和后续云部署的教学平台框架。活动前端位于 `Course-Agent/creative`，活动后端是 `backend` 中的 FastAPI + SQLite 网关。原论坛、旧 Django 项目和 Coze 智能体接入已从仓库移除。

当前仓库可以在 `AGENT_MODE=mock` 下完整演示七个业务场景，也已经预留远程 Agent 适配层。Mock 模式只生成可验证的结构化文本数据，不在本地伪造 PNG 或 MP4；图片、短视频等真实素材必须由后续接入的 Agent 返回 `media_url`。

## 已实现范围

- 简易 `user_id` 登录和新老用户分流。
- 六维学生画像对话采集、SSE 增量更新与画像确认。
- 讲义、思维导图、题库、代码案例、图文视频五类资源并行任务框架。
- 全局进度、当前 Agent、独立资源进度、失败重试和断线续传。
- Markdown、代码、思维导图、题库和媒体资源统一渲染。
- 五阶段个性化学习路径及资源绑定。
- 全局文字、图解、短视频三种模式的画像感知答疑。
- 学习评估、薄弱点统计和幂等的一键更新计划。
- 真实 Markdown、PDF、DOCX、PPTX 课程文件索引与只读浏览。
- Mock/Remote Agent 显式切换、统一错误契约和部分成功展示。

## 架构

```text
Browser (Next.js 15)
        |
        | JSON + SSE
        v
FastAPI Gateway ---- SQLite
        |
        +---- MockAgentProvider（本地框架演示）
        |
        +---- RemoteAgentProvider（队友 Agent 服务）
```

前端不持久化画像、学习记录或资源正文。SQLite 由 FastAPI 独占写入；部署时保持单个 API worker。资源生成与答疑流使用统一 `GatewayEvent`，远程 Agent 的原始事件会先经过固定 Pydantic 契约校验，再交给前端。

## 目录

```text
Course-Agent/creative/  Next.js 活动前端、组件测试和浏览器测试
backend/                FastAPI 网关、SQLite、迁移和后端测试
infra/nginx/            同源代理与 SSE 配置
docs/                   组件、接口、部署和演示文档
artifacts/              截图、演示和本地日志（部分产物被忽略）
docker-compose.yml      Web、API、Nginx 编排
start.ps1 / start.sh    本地一键启动脚本
```

## 环境要求

- Windows 10/11 + PowerShell 5.1，或 Linux + Bash。
- Python 3.12。
- Node.js 22、Corepack、pnpm。
- Docker Desktop / Docker Engine（仅 Docker 方式需要）。

## 本地启动

Windows：

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

脚本会创建 `backend/.venv`、安装依赖、执行 Alembic，并寻找可用的 API/Web 端口。终端会打印实际地址；按 `Ctrl+C` 同时停止两个进程。

Linux：

```bash
cp .env.example .env
chmod +x start.sh
./start.sh
```

默认地址：

- 前端：`http://127.0.0.1:3000`
- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

## Docker Compose

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build -d
Invoke-RestMethod http://127.0.0.1:8080/health
```

浏览器访问 `http://127.0.0.1:8080`。如端口占用，在 `.env` 中设置 `ZHIXUE_PORT`。镜像仓库不可达时可设置 `BASE_REGISTRY` 为可用镜像前缀；这不会改变应用行为。

## Agent 模式

本地框架演示：

```dotenv
AGENT_MODE=mock
ALLOW_MOCK_FALLBACK=false
```

接入队友服务：

```dotenv
AGENT_MODE=remote
REMOTE_AGENT_BASE_URL=https://agent.example.com
REMOTE_AGENT_API_KEY=replace-with-secret
REMOTE_AGENT_TIMEOUT_SECONDS=120
ALLOW_MOCK_FALLBACK=false
```

远程模式默认不会静默返回模拟内容。仅在明确设置 `ALLOW_MOCK_FALLBACK=true` 时才会降级，而且事件会携带 `demo_mode=true`，前端持续显示“演示模式”。完整上游契约见 [接口接入说明](docs/api-integration.md)。

## 课程知识库

知识库的源目录放在仓库根部的 `knowledge_base/`，你可以把课程素材按知识点 ID 放进 `knowledge_base/materials/<knowledge_point_id>/`，并维护 `knowledge_base/knowledge_dag.json`。后端启动时会把它同步到 `backend/data/courses/<course_slug>/`，再由现有索引器读取。

`backend/data/courses/` 是运行时镜像，不需要你手工维护；它会在本地启动或 Docker 容器启动时由知识库自动同步生成。没有真实文件时知识库页面显示“课程资料未同步”，不会生成或填充虚构正文。

你已经把资源压缩到 100MB 以下，因此可以直接提交这些资源文件。`parsed/`、`resource_index.json` 和每个目录里的 `metadata.json` 都属于增强层，按需生成即可。

## 验证命令

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e
powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
docker compose config --quiet
```

## 交付文档

- [前端页面与组件边界](docs/components.md)
- [网关与 Agent 接口接入](docs/api-integration.md)
- [本地和云部署](docs/deployment.md)
- [答辩演示脚本](docs/demo-script.md)

真实 Agent URL、鉴权信息、媒体素材 URL 和正式课程文件属于外部输入。仓库只提供稳定接入框架，不声明这些外部输入已经交付。
