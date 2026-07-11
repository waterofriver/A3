# GitHub 私有仓库 SSH 拉取对话总结

日期：2026-07-11  
工作窗口：云服务器使用 SSH 密钥访问私有仓库

## 场景

用户已经配置公私钥对，并把公钥添加到 GitHub，需要在云服务器上通过 SSH 拉取私有仓库 `waterofriver/A3`。

## 核心结论

- 私钥必须存在于执行 Git 命令的云服务器用户的 `~/.ssh/` 中，不能上传到 GitHub、仓库或聊天记录。
- GitHub 使用固定 SSH 用户 `git`，仓库地址为 `git@github.com:waterofriver/A3.git`。
- 默认密钥名可直接使用；自定义密钥名需要在 `~/.ssh/config` 中配置 `IdentityFile` 和 `IdentitiesOnly yes`。
- 应先执行 `ssh -T git@github.com` 验证认证，再执行 `git clone`。
- 不使用 `sudo git clone`，避免 root 用户无法读取当前用户的密钥。
- 已有 HTTPS 克隆可用 `git remote set-url origin git@github.com:waterofriver/A3.git` 切换到 SSH。
- 本地 A3 当前相对 `origin/main` 领先 1 个对话总结提交；如需云端拉取完全一致的 HEAD，需要先从本机推送。

## 安全与排错

- `~/.ssh` 权限设为 700，私钥设为 600，配置文件设为 600。
- 首次连接应核对 GitHub 官方公布的主机密钥指纹后再接受。
- `Permission denied (publickey)` 时使用 `ssh -vT git@github.com` 检查实际选择的用户、私钥和认证结果。
- 如果使用带口令的私钥，交互登录后通过 `ssh-agent` 和 `ssh-add` 加载；无人值守部署建议使用只授予该仓库读取权限的 Deploy Key。

