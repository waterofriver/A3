# Next ChunkLoadError 与 502 对话总结

## 用户反馈

页面出现 `Runtime ChunkLoadError`，无法加载 `http://127.0.0.1:3000/_next/static/chunks/app/(platform)/layout.js`；同时外层报告 `https://code.codingplay.top/responses` 返回 502。

## 诊断结论

- 本地监听检查确认 3000 和 8000 均没有服务进程。
- `PlatformLayout` 只负责组合 `SessionGuard` 与 `AppShell`，没有抛出截图所示错误。
- `.next` 缓存停留在服务被结束前。浏览器请求已停止的开发服务器，因此 chunk 请求超时；错误面板将首次调用该 chunk 的布局文件标为位置。
- `code.codingplay.top/responses` 的 502 是远端代理链路错误，无法由本地前端布局修复。

## 建议恢复步骤

在仓库根目录重新执行 `./start.ps1 -ApiPort 8000 -WebPort 3000`，然后浏览器强制刷新页面。如果仍出现旧 chunk，删除 `Course-Agent/creative/.next` 后再执行启动脚本。若远端仍返回 502，需检查 `code.codingplay.top` 的上游服务和 Cloudflare 日志。

## 会话限制

本会话的执行环境拒绝缓存删除和后台服务启动命令，因此未能替用户实际完成重启。
