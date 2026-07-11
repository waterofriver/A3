# 智学引擎交付续作对话总结

- 日期：2026-07-11
- 工作窗口：`C:\Users\PEIWENHAO2\Desktop\A3\.worktrees\zhixue-platform`
- 分支：`feat/zhixue-platform`
- 功能与产物基线：`c2b48f9ce3d9b9ab17dcb5ee40d0bf77721fb16e`
- 上一窗口总结：`docs/conversation-summaries/2026-07-10-zhixue-engine-brainstorm-summary.md`

## 本窗口目标

继续完成 Phase 3 交付任务：部署资产、说明文档、全页面浏览器流程、无障碍与布局审计、截图/录屏、完整测试和发布审计。

用户最新约束优先于旧计划：不实现本地、离线、确定性生成教学 PNG 或 MP4，只保留真实 Agent 的 `media_url` 接入口。Mock 图片/视频保持 `media_url=null` 并显示“等待真实 Agent 返回素材”。交付目录中的 PNG 是网站运行截图，WebM 是浏览器交互录屏，不是 Agent 生成的教学媒体。

## 本窗口完成内容

1. 完成 Windows/Linux 一键启动、FastAPI/Next Dockerfile、Nginx SSE 代理和 Docker Compose 编排。
2. 将 Next standalone 输出限制在 Docker 构建，避免 Windows 本地构建的符号链接权限问题。
3. 重写 README，并新增组件边界、API/Agent 接入、部署和答辩演示文档及文档验收脚本。
4. 新增 1366x768、1440x900、1920x1080 三个 Playwright PC 项目。
5. 新增全业务 E2E、横向溢出检查和 Axe `critical` 无障碍检查。
6. 修复工作台三栏在 1440/1366 视口溢出的问题。
7. 修复答疑回答形式分段控件只显示圆点、丢失图标与文字的问题，并增加单元回归测试。
8. 生成并人工检查 11 张全页截图、主流程 WebM 和本地 raw trace。
9. 将 E2E 数据库改为每次命令独立文件，视觉场景使用固定用户和固定 Agent 节拍。
10. 常规 E2E 只在内存中截图；只有 `UPDATE_VISUAL_ARTIFACTS=1` 才覆盖已评审 PNG，保证测试后 Git 干净。

## 本窗口提交

```text
c2b48f9 test: make visual capture deterministic
62b68be test: capture full platform demonstration
6e0df16 fix(web): harden desktop workflow presentation
9f4a586 docs: add platform integration and deployment guides
172beaf build: add local and Docker deployment
```

## 最终验证证据

```text
backend\.venv\Scripts\python -m pytest backend/tests -q
52 passed in 14.07s

pnpm --dir Course-Agent/creative test
25 files, 55 tests passed

pnpm --dir Course-Agent/creative lint
exit 0

pnpm --dir Course-Agent/creative typecheck
exit 0

pnpm --dir Course-Agent/creative build
10 routes generated, exit 0

pnpm --dir Course-Agent/creative test:e2e
10 passed, 2 expected visual-project skips, 5.0m

powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1
Documentation acceptance checks passed.

pnpm --dir Course-Agent/creative test -- tests/legacy-removal.test.ts
3 passed

docker compose config --quiet
exit 0
```

OpenAPI 已重新导出，`openapi-typescript` 已重新生成 `Course-Agent/creative/lib/api/generated.ts`，Git 无契约差异。活动 `Course-Agent/creative` 与 `backend` 中未发现 Coze、forum 或“论坛”引用。最终全量 E2E 后 `git status --short` 为空。

## 视觉产物

- 索引：`artifacts/README.md`
- 截图：`artifacts/screenshots/01-login.png` 至 `11-agent-failure.png`
- 精选录屏：`artifacts/demo/zhixue-main-flow.webm`
- 本地 trace：`artifacts/demo/raw/**/trace.zip`，体积较大并由 Git 忽略

截图已检查登录、画像流、资源生成中、资源结果、题库、路径、答疑抽屉、评估图表、知识库空状态、网络错误和 Agent 超时。未发现横向溢出、文字裁切、互相覆盖、空白图表或 Next 开发工具标记。

## 当前本地服务

- Web：`http://127.0.0.1:3000/login`，HTTP 200，监听 PID `23040`
- API：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`，返回 `status=ok`，监听 PID `27556`
- 日志：`artifacts/logs/web-live.log`、`artifacts/logs/api-live.log`

## Docker 外部限制

Docker daemon 和 BuildKit 正常，Compose 配置以及两个 Dockerfile 均被解析。实际 `docker compose build` 在读取基础镜像元数据时失败：Docker Desktop 未配置 HTTPS proxy，无法连接 `registry-1.docker.io:443`，因此本机没有完成容器构建和 `http://localhost:8080/health` 检查。没有残留 Compose 容器。

这是 Docker daemon 的外部网络配置问题，不是 Dockerfile 或 Compose 语法错误。云服务器或已配置代理/镜像仓库的机器仍需重新执行：

```powershell
docker compose build
docker compose up -d
Invoke-RestMethod http://127.0.0.1:8080/health
docker compose down
```

## 尚需外部提供

- 队友真实 Agent 服务 URL、Bearer 鉴权信息和五个端点的真实事件样例。
- 正式课程 Markdown/PDF/DOCX/PPTX 文件。
- 图片和教学视频的真实 `media_url`；前端不参与媒体生成。
- 云部署机器的域名、HTTPS 证书、Docker registry/proxy 和备份策略。

除上述外部输入与 Docker 网络环境外，前端框架、FastAPI 网关、SQLite CRUD、Mock/Remote 适配边界、文档、启动脚本和演示材料均已落地。
