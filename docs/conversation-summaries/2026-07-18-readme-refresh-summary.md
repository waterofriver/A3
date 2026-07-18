# README 重写对话总结

## 用户目标

重写仓库内全部 README，使其忠于当前项目，不因压缩篇幅而丢失项目结构、运行方法和技术细节。README 既要能作为比赛交付文件供评委阅读，也要为团队或 AI 后续撰写系统开发说明书、测试说明书、演示 PPT 等正式材料提供可靠事实，但本次不直接编写作品文档。

用户提供了高等教育个性化学习赛题背景、核心功能、非功能要求、实现条件、文档规范与评分比例，并明确要求区分已实现能力、Mock 演示、外部依赖和未来工作，不虚构功能或指标。

## 信息架构

仓库共保留五份职责分明的 README：

- 根 `README.md`：项目定位、赛题对应、功能、创新点、架构、技术栈、项目结构、运行部署、测试、边界和文档索引。
- `backend/agent/README.md`：本地八个 Agent 角色模块、网关接入关系、输入输出、配置、测试和内容安全边界。
- `knowledge_base/README.md`：活动课程 DAG、素材目录、校验、元数据构建、运行时同步和交付规范。
- `artifacts/README.md`：已提交截图与录屏、视觉证据更新、再生成命令和本地忽略产物。
- `backend/agent/knowledge_base/README.md`：旧 Agent 模板的最小字段与迁移说明，不再与顶层活动知识库争夺权威性。

信息架构设计记录位于 `docs/superpowers/specs/2026-07-18-readme-information-architecture-design.md`，执行计划位于 `docs/superpowers/plans/2026-07-18-readme-refresh.md`。

## 本次更新

### 根 README

- 说明学生面对资源无序、内容不匹配、统一教学节奏等实际痛点及系统实用价值。
- 将赛题的画像、资源生成、路径推送、智能辅导、学习评估和非功能体验映射到真实组件与 API。
- 恢复完整项目结构、本地启动、Docker/云部署、HTTPS 建议、Agent 环境变量、知识库和测试命令。
- 标注 Next.js、React、FastAPI、SQLite、SSE、Three.js、Playwright 等技术及开源使用边界。
- 说明 AI Coding 的实际使用，不把 AI 输出当成功能完成证据。
- 明确 Mock、Local、Remote 三种模式、简易 `user_id` 登录、真实媒体服务、内容核验和生产部署限制。

### Agent README

- 逐一记录 ProfileAgent、Supervisor、PlannerAgent、DocAgent、MindMapAgent、QuizAgent、VideoAgent 和 ReferenceAgent 的输入、输出与职责。
- 说明活动 Provider 位于 `backend/app/agents/`，本地模型由 `backend/app/agents/real.py` 转换为固定网关契约。
- 明确八个角色模块中，当前 `RealAgentProvider` 直接调用七个；Supervisor 已实现并有测试，但尚未进入活动 API 调用链。
- 明确 Local 模式没有独立 CodeAgent；`code` 请求当前由 ReferenceAgent 生成拓展阅读并返回 `handout`。
- 保留 DeepSeek 配置、依赖安装、八组模块测试、网关 pytest 和媒体路径转换要求。

### 知识库 README

- 记录当前课程为“机器人与安全”，`course_slug` 为 `robot-safety`，DAG 共有 15 个知识点。
- 完整说明顶层字段、知识点字段、DAG 无环规则、入口节点、目录命名和素材格式。
- 区分校验器认可的教学素材扩展名与构建脚本可分类的附加代码、视频、图片和压缩文件。
- 说明 `python validate_knowledge_base.py`、`python build_knowledge_base.py` 及后端启动同步流程。
- 明确 `knowledge_base/` 是权威源，`backend/data/courses/<course_slug>/` 是运行时副本；同步不会自动删除目标端旧文件。
- 增加 GitHub 50 MiB 警告、100 MiB 限制、当前未配置 Git LFS 规则以及比赛离线打包注意事项。
- 将 `backend/agent/knowledge_base/knowledge_dag_template.json` 标注为缺少 `course_slug` 的历史模板，并给出迁移步骤。

### 产物 README

- 恢复 11 张已提交截图的逐项清单和 `demo/zhixue-main-flow.webm` 说明。
- 记录截图基准为 1440x900 全页捕获，浏览器流程还配置 1366x768 与 1920x1080。
- 明确现有 `01-login.png` 是旧入口历史证据，当前沉浸式展示页应在同步更新 Playwright 登录流程后重新捕获。
- 说明截图只能证明视觉状态；粒子自转、左键拖动、滚轮不改变粒子和整屏章节切换应结合录屏或交互断言证明。
- 区分已提交评审证据与被忽略的日志、raw trace、`.playwright-cli/`、`.next-*`、`output/` 等可再生产物。

## 关键事实边界

- 平台契约与 Mock 演示覆盖讲义、思维导图、题库、代码案例和视频五类资源；Local 模式的代码分支当前不等价于代码生成 Agent。
- Mock 数据用于可重复演示，事件携带 `demo_mode=true`；不能将其描述为真实远程模型或媒体生成成果。
- 课程浏览与预览只读取仓库资料；知识库未同步时显示空状态。Mock 资源正文是另一条显式演示链路。
- Remote 模式需要真实服务 URL、鉴权、事件契约和媒体生命周期；默认不会静默降级为 Mock，除非显式允许。
- 当前登录方式适合比赛演示，不是公网多租户认证；生产环境仍需身份认证、权限、限流与审计。
- 仓库没有可量化的防幻觉准确率或生产性能结论，目标服务器仍需完成构建、性能、安全和内容质量验收。

## 验证结果

本次重写完成后执行并确认：

- `rg --files -g "README.md" -g "README.*"`：共 5 份 README，与预期一致。
- 相对 Markdown 链接检查：检查 23 个本地链接，损坏链接 0 个。
- 关键引用路径检查：检查 29 个目录、脚本、配置和产物路径，缺失 0 个。
- `python knowledge_base/validate_knowledge_base.py`：输出“校验通过”。
- `powershell -ExecutionPolicy Bypass -File docs/test-documentation.ps1`：文档验收检查通过。
- `git diff --check`：无空白和补丁格式错误。

本次工作只修改文档，没有启动网站、调用真实模型、重建前端或改动应用行为。README 中的历史测试结果只代表对应版本，正式提交前仍应在目标环境重新执行测试和浏览器验收。
