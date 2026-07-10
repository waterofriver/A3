# 智学引擎改造对话总结

- 日期：2026-07-10
- 工作窗口：`C:\Users\PEIWENHAO2\Desktop\A3`
- 当前阶段：设计已确认，等待书面规格审阅

## 用户目标

基于现有 Next.js 前端改造完整个性化教学平台，删除论坛功能和原有 Coze 智能体接入，建立可直接对接队友 LangGraph/资源 Agent 的前端框架与 FastAPI 网关骨架，并交付文档、启动脚本、截图和演示材料。

## 已检查的现状

- 根目录不是 Git 仓库，没有可用提交历史。
- 前端位于 `Course-Agent/creative`，使用 Next.js 15、React 19、Tailwind 和 shadcn/ui。
- 核心 `components/creative.tsx` 约 2400 行，混合论坛、Coze、示例工作台和资源逻辑。
- 论坛同时耦合 Next.js 前端与 Django 的 Blog/Comment/Like 模型、路由和模板。
- 当前后端是 Django，不是需求要求的 FastAPI。
- `materials.json` 存在课程元数据，但对应课程原文件未随仓库提供。
- `node_modules`、`.next` 和 SQLite 数据库当前不存在。

## 已确认决策

1. 新建 FastAPI + SQLite，作为唯一运行后端；旧 Django 仅保留历史参考并退出启动/部署。
2. 上游 Agent 暂不可用，先实现 Mock Provider 和 Remote Provider 适配接口。
3. 正式知识库等待用户提供真实文件，不伪造课程正文。
4. 删除 Coze 悬浮聊天、自动出题、Token 路由、SDK 和依赖。
5. 最终覆盖全部七个业务场景，分三个阶段连续交付。
6. 全站采用“教学指挥台”布局。
7. 视觉采用“A3 明亮数智”：白色、浅灰、钴蓝、草绿和珊瑚色。
8. 产品名称为“智学引擎”，副标题为“多智能体个性化学习系统”。
9. 本地 Mock 模式可独立演示；云端通过环境变量接入真实 Agent API。
10. 云服务器采用 Linux + Docker Compose 部署。
11. 在原 Next.js 工程内模块化重建，不继续扩张单体 `creative.tsx`，也不另建重复前端项目。

## 参考作品接口后的补充

纳入以下闭环接口：

- `GET /api/course/list`
- `POST /api/profile/confirm`
- `GET /api/task/{task_id}`
- `POST /api/task/{task_id}/retry`
- `GET /api/resource/list`
- `POST /api/quiz/submit`
- `POST /api/learning/events`
- `POST /api/eval/apply`

不采用 JWT 注册登录、宽泛 `/chat/send` 和手工 `/profile/update`，因为它们与当前简易 user_id 登录及 Agent 固定画像契约不一致。

## 已通过的设计章节

- 总体架构
- 页面、导航与组件边界
- 任务数据流与 SSE 生命周期
- 异常、降级与空状态
- 测试、验收与交付证据

## 关键工程约束

- SQLite 模式使用单个 API worker。
- 远程 Agent 失败时不得静默返回模拟内容。
- SSE 使用 task_id、seq、trace_id、固定 Agent/进度字段和可重试错误。
- 正式课程文件缺失时显示空状态。
- 取消 Next.js 的 TypeScript 构建错误忽略。
- PC 视口必须通过 Playwright 截图与重叠检查。

## 尚需外部提供

- 真实课程文件。
- 队友 Agent 服务 URL、鉴权方式、超时和事件样例。

## 下一步

1. 用户审阅正式规格：`docs/superpowers/specs/2026-07-10-zhixue-engine-platform-design.md`。
2. 规格获批后使用 `superpowers:writing-plans` 生成实施计划。
3. 按计划分阶段实现、验证和交付。

