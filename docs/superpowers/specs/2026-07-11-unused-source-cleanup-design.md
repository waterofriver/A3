# 无用源码清理设计

日期：2026-07-11

## 目标

删除不参与智学引擎活动产品、启动链路或部署链路的旧源码和本地临时目录，降低仓库噪声，同时保留可继续开发、演示和交付所需的依赖、构建缓存与演示素材。

## 审计结论

`mywebsite/` 是旧 Django 项目，共包含 50 个 Git 跟踪文件。当前活动前端位于 `Course-Agent/creative/`，活动后端位于 `backend/`；`start.ps1`、`start.sh` 和 `docker-compose.yml` 均不引用 `mywebsite/`。除历史计划、README、`.gitignore` 和一项遗留移除测试外，活动代码没有依赖该目录。

因此，`mywebsite/` 对当前平台没有运行或部署价值，可以从仓库删除。历史计划中对它的描述属于实施记录，保留原文，不作为活动依赖。

## 删除范围

- 删除整个 `mywebsite/` 目录及其中的 Django、论坛、备份、模板和旧资源代码。
- 删除空的根目录 `data/` 和 `.worktrees/`。
- 删除被 Git 忽略的 `.superpowers/` 本地设计预览缓存；正式设计文档已保存在 `docs/superpowers/`。

## 同步修改

- 修改 `Course-Agent/creative/tests/legacy-removal.test.ts`：不再读取 Django 路由文件，改为断言 `mywebsite/` 不存在。
- 修改 `README.md`：移除“保留旧 Django 历史代码”的说明和目录项，明确旧论坛与 Coze 代码已从仓库移除。
- 修改 `.gitignore`：删除仅针对 `mywebsite/` 的忽略项，保留活动 Python、Node.js、Next.js、SQLite、课程资料和运行产物所需规则。

## 明确保留

- `artifacts/` 中已跟踪的截图、演示视频和索引，供答辩、PPT 与交付使用。
- `Course-Agent/creative/node_modules/`、`Course-Agent/creative/.next/` 和 `backend/.venv/`，避免本次源码清理导致本地环境重新安装。
- `backend/data/` 下的运行数据库和课程资料目录。
- `docs/superpowers/plans/` 与已有设计文档，作为实施与决策记录。
- FastAPI、Next.js、Nginx、Docker Compose 和一键启动脚本的全部活动源码与配置。

## 行为影响

清理不改变任何活动页面、API、数据模型或 Agent 接入契约。唯一可见变化是仓库不再包含可误认为活动后端的 Django 项目。现有 Web 与 API 进程不依赖该目录，因此删除不会中断当前服务。

## 验收标准

- Git 跟踪树中不存在 `mywebsite/`。
- 根目录不存在 `data/`、`.worktrees/` 和 `.superpowers/` 临时目录。
- 活动代码、README 和 `.gitignore` 中不存在把 `mywebsite/` 当作现存模块的引用。
- 后端测试、前端测试、ESLint、TypeScript 类型检查、Next.js 生产构建和文档验收全部通过。
- `/health` 返回 `status=ok`，登录页返回 HTTP 200。
- Git diff 只包含约定的删除、引用同步和当前窗口总结。

