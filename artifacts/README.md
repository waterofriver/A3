# 演示与验证产物

`artifacts/` 保存可直接用于项目评审、演示 PPT、操作说明和回归核对的精选证据。当前已提交 11 张 PC 端全页截图和一段主流程 WebM；它们来自 Playwright 驱动的 Next.js + FastAPI `mock` 模式，不是 Agent 生成的教学图片或教学视频。

本目录只保留经过筛选、体积可控且有交付价值的文件。运行日志、浏览器 trace、失败快照、Next.js 构建缓存和临时导出均属于可再生本地产物，由 `.gitignore` 排除。

## 已提交截图

| 文件 | 记录场景 | 证据性质 |
|---|---|---|
| `screenshots/01-login.png` | 原登录入口与产品标题 | 历史入口证据，见下方更新说明 |
| `screenshots/02-profile-stream.png` | 画像对话的 SSE 流式采集与进度 | 核心功能 |
| `screenshots/03-workspace-generating.png` | 多 Agent 资源生成与独立进度 | 核心功能 |
| `screenshots/04-workspace-results.png` | 五类个性化资源生成结果 | 核心功能 |
| `screenshots/05-resource-quiz.png` | 选择、填空、编程混合题库 | 核心功能 |
| `screenshots/06-learning-path.png` | 分阶段个性化学习路径 | 核心功能 |
| `screenshots/07-qa-drawer.png` | 图解答疑流与真实媒体等待态 | 可选加分功能及边界 |
| `screenshots/08-evaluation.png` | 学习评分、薄弱点和计划建议 | 可选加分功能 |
| `screenshots/09-knowledge.png` | 课程资料未同步时的只读状态 | 数据边界与空状态 |
| `screenshots/10-network-error.png` | 接口异常、缓存页面和重试动作 | 异常处理 |
| `screenshots/11-agent-failure.png` | 单资源 Agent 超时与可重试状态 | 异常处理 |

截图基准项目为 `desktop-1440`，视口 1440x900，使用全页捕获，因此部分 PNG 高于 900px。当前文件均为 1440px 宽；浏览器主流程测试还配置了 1366x768 和 1920x1080 两个桌面视口，用于检查横向溢出、关键布局和无障碍问题。

这些截图证明的是捕获时版本的前端状态和 Mock 业务链路，不等同于真实远程大模型、多模态生成服务或生产数据的运行证明。`07-qa-drawer.png` 中的“等待真实 Agent 返回素材”正是对外部媒体能力边界的显式展示。

## 已提交录屏

- `demo/zhixue-main-flow.webm`：从登录进入学习平台并浏览主要功能的精选录屏，当前约 1.81 MiB。

Playwright 每次运行产生的原始视频和 trace 位于 `artifacts/demo/raw/`。这些文件用于本地排查，体积和数量不稳定，不纳入 Git。只有人工检查过、能够代表当前主流程的录屏才应替换精选 WebM。

## 沉浸式展示页更新说明

当前 `/login` 已升级为带粒子场景、分章节整屏切换和登录弹层的沉浸式展示页，因此已提交的 `01-login.png` 不再代表最新首屏视觉。它暂时保留为历史证据，不应在新答辩材料中标注为“当前展示页”。

下一次刷新交付证据时，应同时更新 `Course-Agent/creative/e2e/visual-capture.spec.ts` 的登录交互，再重新捕获：

- 展示页桌面首屏；
- 登录弹层打开状态；
- 至少一个移动端视口；
- 鼠标按住拖动粒子场景后的状态，如需证明交互；
- 一次滚轮输入后完整切换到下一章节的状态。

新的入口证据通过检查后，可替换 `01-login.png`，也可按稳定命名新增展示页截图并同步更新本清单。粒子缓慢自转、仅按住左键拖动、滚轮不改变粒子状态以及整屏章节切换等交互，更适合通过录屏或自动化交互断言证明，单张静态截图只能证明视觉状态。

## 重新生成截图

前提：已安装前端依赖、Playwright Chromium 和后端 Python 依赖；本机的 3000、8000 端口可用，或已调整 Playwright 配置。测试配置会以 `AGENT_MODE=mock` 启动后端，从而得到可复现的演示数据。

只执行视觉捕获并覆盖命名 PNG：

```powershell
$env:UPDATE_VISUAL_ARTIFACTS = '1'
pnpm --dir Course-Agent/creative test:e2e -- e2e/visual-capture.spec.ts --project=desktop-1440
Remove-Item Env:UPDATE_VISUAL_ARTIFACTS
```

执行三个桌面视口的完整主流程：

```powershell
pnpm --dir Course-Agent/creative test:e2e -- e2e/full-platform-flow.spec.ts
```

`visual-capture.spec.ts` 即使不设置 `UPDATE_VISUAL_ARTIFACTS`，仍会在内存中执行截图大小、横向溢出和关键无障碍断言；只有环境变量为 `1` 时才覆盖 `artifacts/screenshots/` 中的命名图片。原始视频和 trace 会写入被忽略的 `artifacts/demo/raw/`。

更新精选录屏时，从最新 raw 场景目录选择完整且清晰的 `video.webm`，人工检查后替换：

```text
artifacts/demo/zhixue-main-flow.webm
```

不要仅按文件大小自动选择录屏；应确认它覆盖目标流程、没有等待卡死、敏感信息、开发工具遮挡或与当前 UI 不一致的片段。

## 已忽略的本地产物

以下目录或文件不影响网站功能，可由开发、构建或测试过程重新生成：

| 路径 | 内容 |
|---|---|
| `artifacts/logs/` | `start.ps1` / `start.sh` 和服务运行日志 |
| `artifacts/playwright/` | 临时浏览器验证输出 |
| `artifacts/test-results/` | 本地测试报告和失败附件 |
| `artifacts/demo/raw/` | 原始视频、trace.zip 和中间录制数据 |
| `.playwright-cli/` | Playwright CLI 会话快照与缓存 |
| `Course-Agent/creative/playwright-report/` | HTML 测试报告 |
| `Course-Agent/creative/test-results/` | 前端浏览器测试输出 |
| `Course-Agent/creative/.next/`、`.next-*/` | Next.js 开发、验证和生产构建缓存 |
| `Course-Agent/creative/out/` | Next.js 静态导出目录 |
| `Course-Agent/creative/output/` | 本地截图和临时验证导出 |

这些路径不应为了答辩“证据更多”而整目录提交。需要保留某次失败现场时，应挑选必要截图或摘要，去除敏感数据后再放入明确命名的交付位置。

## 提交前检查

- [ ] 清单中的 11 张 PNG 和精选 WebM 均存在且可打开。
- [ ] 截图对应当前要讲解的版本；历史截图已明确标注或完成替换。
- [ ] 页面没有裁切、文字重叠、空白图表、开发工具标记或加载遮罩残留。
- [ ] 录屏覆盖目标流程，时间合理，画面与操作连续。
- [ ] Mock 演示、真实课程文件和外部 Agent 能力没有混写。
- [ ] 截图或录屏中没有密钥、个人隐私、绝对路径等敏感信息。
- [ ] 未误提交日志、raw trace、`.next-*`、`output/` 或 `.playwright-cli/`。
- [ ] README、演示 PPT 和视频脚本使用一致的产物名称与功能表述。
