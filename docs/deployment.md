# 部署与环境配置

本项目支持 Windows 本地启动、Linux 本地启动和 Linux/Docker Compose 部署。FastAPI 是唯一活动网关；旧 Django 目录不启动。SQLite 部署固定使用一个 Uvicorn worker。

## 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `AGENT_MODE` | `mock` | `mock` 或 `remote` |
| `ALLOW_MOCK_FALLBACK` | `false` | 远程失败时是否显式降级 |
| `REMOTE_AGENT_BASE_URL` | 空 | 队友 Agent 服务根 URL |
| `REMOTE_AGENT_API_KEY` | 空 | 可选 Bearer token |
| `REMOTE_AGENT_TIMEOUT_SECONDS` | `120` | 上游总超时秒数 |
| `DATABASE_URL` | `sqlite:///./data/zhixue.db` | SQLite 连接串 |
| `COURSE_ROOT` | `./data/courses` | 真实课程文件根目录 |
| `WEB_ORIGINS` | 本地前端地址 | 允许的 CORS 来源，逗号分隔 |
| `MOCK_EVENT_DELAY_MS` | `40` | Mock 流演示延迟 |
| `SSE_POLL_INTERVAL_MS` | `250` | 持久化事件轮询间隔 |
| `SSE_HEARTBEAT_SECONDS` | `15` | SSE 心跳周期 |
| `ZHIXUE_PORT` | `8080` | Compose 对外端口 |
| `BASE_REGISTRY` | `docker.io` | 基础镜像仓库前缀 |

五个 `REMOTE_*_PATH` 的默认值和上游字段见 [接口接入说明](api-integration.md)。机密只写入未跟踪的 `.env` 或云平台 Secret，不提交到 Git。

## Windows 本地

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

`start.ps1` 会：

1. 创建 `backend/.venv` 并安装后端测试依赖。
2. 用冻结锁文件安装前端依赖。
3. 执行 `alembic upgrade head`。
4. 从 8000/3000 起查找未占用端口。
5. 隐藏启动 API 和 Web 子进程，并把日志写入 `artifacts/logs/`。
6. 在当前终端被中断时清理两个子进程。

脚本打印的端口是实际访问端口，不能假定始终为 3000/8000。

## Linux 本地

```bash
cp .env.example .env
chmod +x start.sh
API_PORT=8000 WEB_PORT=3000 ./start.sh
```

Linux 脚本执行同样的依赖、迁移和进程清理流程。它不自动选择备用端口；冲突时显式设置 `API_PORT` 和 `WEB_PORT`。

## Docker Compose

```bash
cp .env.example .env
docker compose config
docker compose build
docker compose up -d
curl http://127.0.0.1:8080/health
```

服务：

- `api`：Python 3.12、非 root 用户，先迁移再启动单 worker Uvicorn。
- `web`：Node 22 多阶段构建，Docker 内启用 Next standalone 输出。
- `nginx`：对外唯一入口，同源代理 Web、API 和课程媒体。

卷：

- `zhixue-data`：SQLite 与应用数据。
- `zhixue-media`：为后续真实 Agent 媒体集成保留；当前 Mock 不写入本地 PNG/MP4。
- `./backend/data/courses:/app/data/courses:ro`：真实课程文件只读挂载。

Next standalone 只在 Docker 构建时通过 `NEXT_OUTPUT_MODE=standalone` 启用，避免 Windows 本地构建阶段因符号链接权限失败。

若 Docker daemon 无法访问镜像仓库，先验证主机和 daemon 的代理/DNS，再设置可用 `BASE_REGISTRY`。`docker compose config --quiet` 只能证明编排语法正确，不能替代真实镜像构建和健康检查。

## Nginx、SSE 与 HTTPS

`infra/nginx/default.conf` 对 `/api/` 关闭 `proxy_buffering` 和缓存，读写超时为 300 秒，并传递 `X-Trace-ID`。部署到云服务器时保留这些 SSE 设置。

生产环境在外层负载均衡器或 Nginx 增加 HTTPS：

```nginx
server {
    listen 443 ssl http2;
    server_name learn.example.com;
    ssl_certificate /etc/letsencrypt/live/learn.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/learn.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

同时把正式来源加入 `WEB_ORIGINS`。真实 Agent 的媒体 URL 必须是 HTTPS 或同源可访问路径，避免浏览器混合内容拦截。

## 接入真实 Agent

推荐先在预发布环境关闭降级：

```dotenv
AGENT_MODE=remote
ALLOW_MOCK_FALLBACK=false
REMOTE_AGENT_BASE_URL=https://agent.internal.example
REMOTE_AGENT_API_KEY=secret
REMOTE_AGENT_TIMEOUT_SECONDS=120
```

逐项验证画像流、资源流、答疑流、路径 JSON 和评估 JSON。上游暂不可用时，网关应显示明确错误而不是静默生成内容。演示确实需要降级时才临时设置 `ALLOW_MOCK_FALLBACK=true`，并确认页面出现“演示模式”。

## 课程和媒体

- 正式课程：放入 `backend/data/courses/<course>/` 后重启 API 触发索引。
- 支持文本层：Markdown、PDF、DOCX、PPTX；扫描版 PDF 没有 OCR 时可能没有预览文本。
- 课程原文件通过受路径校验的 `/media/courses/...` 只读返回。
- 生成媒体：当前仓库不做本地 PNG/MP4 生成。由真实 Agent 返回 `media_url`，网关只校验和持久化，前端只预览/下载。

## 备份与恢复

Compose 数据位于命名卷。备份前停止 API 写入：

```bash
docker compose stop api
docker run --rm -v zhixue-platform_zhixue-data:/data -v "$PWD/backups:/backup" alpine \
  sh -c 'cp /data/zhixue.db /backup/zhixue-$(date +%Y%m%d-%H%M%S).db'
docker compose start api
```

恢复时先停止 `api`，保留旧数据库副本，再把验证过的备份放回卷。启动后执行健康检查和 Alembic 当前版本检查。

## 发布检查

```powershell
backend\.venv\Scripts\python -m pytest backend/tests -q
pnpm --dir Course-Agent/creative lint
pnpm --dir Course-Agent/creative typecheck
pnpm --dir Course-Agent/creative test
pnpm --dir Course-Agent/creative build
pnpm --dir Course-Agent/creative test:e2e
docker compose config --quiet
```

云部署还必须完成真实容器构建、`/health`、SSE 长连接、持久卷重启、HTTPS、正式 Agent 错误和课程只读挂载验证。
