# 无用源码清理对话总结

日期：2026-07-11  
工作窗口：旧 Django 项目与临时目录清理

## 用户选择

用户选择保守的仓库源码清理方案：删除不参与活动产品的源码和本地设计临时目录，同时保留依赖、构建缓存、运行数据目录与交付截图/视频。

## 审计结论

- `mywebsite/` 是旧 Django、论坛、资源和 Flask 备份代码，共有 50 个 Git 跟踪文件。
- Next.js、FastAPI、`start.ps1`、`start.sh` 和 `docker-compose.yml` 均不依赖该目录。
- 唯一活动引用是一项遗留测试；它原先通过读取 Django 路由文件确认论坛入口被停用。

## 实施结果

- 删除整个 `mywebsite/`，包括 50 个跟踪文件和主工作区中 9 个被忽略的上传/备份残留文件。
- 总计从 Git 跟踪内容中删除 7,547 行旧代码。
- 遗留测试改为直接断言仓库中不存在 `mywebsite/`。
- README 改为明确旧 Django、论坛和 Coze 接入均已从仓库移除。
- `.gitignore` 删除 5 条仅针对 `mywebsite/` 的规则。
- 删除根级空 `data/`、空 `.worktrees/` 和 `.superpowers/` 本地设计预览缓存。
- 清理分支以 fast-forward 方式合并到 `main`，功能工作树和分支均已删除。
- `git pull --ff-only` 返回 `Already up to date`，本轮远端同步状态已验证。

## 明确保留

- `artifacts/` 中的截图、演示视频和交付索引。
- 主工作区的 `Course-Agent/creative/node_modules/`、`Course-Agent/creative/.next/` 和 `backend/.venv/`。
- `backend/data/` 下的运行数据库与课程资料位置。
- FastAPI、Next.js、Nginx、Docker Compose、一键启动脚本及全部交付文档。
- 历史计划和设计文档，作为决策记录保留。

## TDD 证据

- RED：将测试改成要求 `mywebsite/` 不存在后，目标测试按预期失败，收到 `true` 而期望 `false`。
- GREEN：删除旧目录后，`legacy-removal.test.ts` 的 3 项测试全部通过。

## 验证结果

- 隔离工作树基线：后端 `52 passed`，前端 `55 passed`。
- 清理后后端：`52 passed`。
- 清理后前端：`55 passed`。
- ESLint：通过。
- TypeScript 类型检查：通过。
- Next.js 生产构建：通过，9 个业务路由成功生成。
- 文档验收：通过。
- `docker compose config --quiet`：通过。
- API 健康检查返回 `status=ok`、`database=ok`、`agent_mode=mock`。
- 登录页返回 HTTP 200。

后端测试导入应用时会根据默认数据库地址创建一个根级空 `data/` 目录；确认其为空且不属于源码后，已在最终验收阶段删除。Docker 镜像拉取和镜像构建仍受本机 Docker Hub 网络/代理条件影响，本轮只验证 Compose 配置。
