# 演示产物

本目录保存答辩和交付可直接使用的 PC 页面证据。所有画面来自 Playwright 驱动的真实 Next.js + FastAPI Mock 流程，不包含本地伪造的 Agent PNG 或 MP4 素材。

## 截图

| 文件 | 场景 |
|---|---|
| `screenshots/01-login.png` | 登录与产品入口 |
| `screenshots/02-profile-stream.png` | 画像 SSE 流式采集中 |
| `screenshots/03-workspace-generating.png` | 多 Agent 资源生成中与独立进度 |
| `screenshots/04-workspace-results.png` | 五类资源结果 |
| `screenshots/05-resource-quiz.png` | 选择、填空、编程混合题库 |
| `screenshots/06-learning-path.png` | 五阶段学习路径 |
| `screenshots/07-qa-drawer.png` | 图解答疑流与真实媒体等待态 |
| `screenshots/08-evaluation.png` | 学习评分、薄弱点和计划建议 |
| `screenshots/09-knowledge.png` | 无真实课程文件时的只读空状态 |
| `screenshots/10-network-error.png` | 网络失败、缓存页面和重试动作 |
| `screenshots/11-agent-failure.png` | 单资源 Agent 超时与可重试状态 |

截图基准视口为 1440x900，使用全页捕获，因此部分文件高度超过 900px。浏览器验收另外覆盖 1366x768 和 1920x1080。

## 交互素材

- `demo/zhixue-main-flow.webm`：登录到知识库的主浏览器流程录屏。
- `demo/raw/**/trace.zip`：最近一次本地执行生成的完整 Playwright trace，体积较大且被 Git 忽略，可用 `pnpm exec playwright show-trace <path>` 打开。

## 重新生成

```powershell
$env:UPDATE_VISUAL_ARTIFACTS = '1'
pnpm --dir Course-Agent/creative test:e2e -- e2e/visual-capture.spec.ts --project=desktop-1440
Remove-Item Env:UPDATE_VISUAL_ARTIFACTS
pnpm --dir Course-Agent/creative test:e2e -- e2e/full-platform-flow.spec.ts
```

视觉测试始终在内存中执行截图、文件大小、布局和无障碍断言；只有 `UPDATE_VISUAL_ARTIFACTS=1` 时才覆盖命名 PNG。录屏和 raw trace 每次都会写入被忽略的 raw 目录。若要更新精选视频，从最新 raw 场景目录复制最大的 `video.webm` 到 `demo/zhixue-main-flow.webm`，并在提交前重新检查全部截图是否存在裁切、重叠、空白图表或开发工具标记。
