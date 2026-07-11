# 后台进程关闭与云部署对话总结

日期：2026-07-11  
工作窗口：本地服务停止与 GitHub 云部署说明

## 本轮目标

- 关闭由 A3 一键启动脚本创建的全部后台服务进程。
- 确认本地 Web、API 和 Compose 入口均不可访问。
- 根据当前仓库配置整理 Ubuntu 云服务器的 GitHub 拉取与 Docker Compose 启动步骤。

## 进程关闭结果

按进程树定位并结束以下 A3 专属进程：

- PowerShell 启动器：PID `26220`。
- Uvicorn Python 包装进程与服务进程：PID `15280`、`4568`。
- pnpm、cmd、Next.js 父子进程：PID `43860`、`4072`、`46020`、`39648`、`29480`。

未按 `node`、`python` 或 `powershell` 进程名批量结束，因此没有主动关闭其他项目进程。

关闭后验证：

- 3000、8000、8080 端口均无监听。
- 上述 A3 进程 PID 均不存在。
- `http://127.0.0.1:3000/login`、`http://127.0.0.1:8000/health` 和 `http://127.0.0.1:8080/health` 均无法连接。

## 仓库与部署依据

- GitHub：`https://github.com/waterofriver/A3.git`。
- 活动分支：`main`。
- 停止服务后检查时，本地 `main` 与 `origin/main` 的 ahead/behind 为 `0/0`。
- 推荐云部署方式：Ubuntu + Docker Engine + Docker Compose plugin。
- Compose 对外默认端口：`8080`。
- 默认 Agent 模式：`mock`；队友服务就绪后通过 `.env` 切换为 `remote`。
- SQLite 固定使用单个 Uvicorn worker，数据和媒体由 Docker 命名卷持久化。

## 云部署流程摘要

1. 云安全组临时开放 TCP 8080，正式域名部署开放 80/443。
2. 安装 Git、Docker Engine 和 Docker Compose plugin。
3. 克隆仓库并进入 A3 目录。
4. 从 `.env.example` 创建 `.env`，填写 Agent 模式和密钥。
5. 创建 `backend/data/courses/`，放入真实课程文件时保持只读挂载。
6. 执行 `docker compose up -d --build`。
7. 用 `docker compose ps`、日志和 `/health` 验证。
8. 后续更新使用 `git pull --ff-only` 和 `docker compose up -d --build --remove-orphans`。

