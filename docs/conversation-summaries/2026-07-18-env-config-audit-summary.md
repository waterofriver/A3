# 2026-07-18 环境变量配置检查对话总结

## 用户目标

检查网站项目所需的 `.env` 配置，确认本地、Docker、远程 Agent 和本地真实 Agent 的变量要求。

## 检查结论

- 根目录 `.env` 是 `start.ps1`、`start.sh` 与 `docker compose` 的统一入口；根目录 `.env.example` 现包含启动、后端、远程 Agent 与本地真实 Agent 的全部可配置变量。
- 默认 `AGENT_MODE=mock` 可直接运行，不需要 API Key。
- `AGENT_MODE=remote` 需要 `REMOTE_AGENT_BASE_URL`；如果远程服务受保护，还需要 `REMOTE_AGENT_API_KEY`。
- `AGENT_MODE=local` 从仓库根目录 `.env`（或优先级更高的进程环境变量）读取 `DEEPSEEK_API_KEY`；其余 DeepSeek 变量有代码默认值。
- `backend/.env.example` 和 `Course-Agent/creative/.env.example` 适用于分别独立启动后端或前端的场景。通过根目录启动脚本时，无需分别创建这两个文件。

## 已实施的收敛

- 后端 `Settings` 现在显式从仓库根目录 `.env` 读取配置，不再受启动工作目录影响。
- 本地 Agent 只从仓库根目录 `.env` 加载 dotenv 配置；系统环境变量仍保持更高优先级。
- 根目录 `.env.example` 已包含本地真实 Agent 所需的 `DEEPSEEK_*` 变量。
- Agent 使用文档已改为指向根目录 `.env`，并新增配置定位回归测试。

## 验证

- `pytest backend/tests/test_environment_config.py backend/tests/test_health.py -q`：4 passed。
- `docker compose config --quiet`：通过。
- `docs/test-documentation.ps1`：通过。
- 启动脚本会根据实际端口覆盖 `NEXT_PUBLIC_API_BASE_URL` 与 `WEB_ORIGINS`，Docker Compose 会固定应用容器的数据库、课程目录、知识库目录和同源 API 地址。

## 未做改动

未修改 `.env` 或应用代码；现有工作区的其他未提交改动保持不变。
