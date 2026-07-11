# 云服务器 Docker Hub 超时诊断对话总结

日期：2026-07-11  
工作窗口：Ubuntu Compose 首次启动失败

## 现象

云服务器执行 `docker compose config` 成功，但执行 `docker compose up -d --build` 时拉取 `docker.io/library/nginx:1.27-alpine` 失败。Docker daemon 连接 `registry-1.docker.io:443` 30 秒后超时，`docker compose ps` 为空。

## 结论

- Compose 文件解析正常。
- 失败发生在镜像拉取阶段，API 和 Web 构建尚未开始。
- Docker daemon 无法连接 Docker Hub，可能原因包括云服务器公网出口限制、Docker Hub 在当前网络不可达、DNS 返回异常地址，或代理只配置给终端而没有配置给 Docker daemon。
- `docker compose config` 只验证编排配置，不访问镜像仓库，不能证明镜像可以拉取。

## 诊断顺序

1. 使用 `curl` 访问 `https://registry-1.docker.io/v2/`；HTTP 401 表示宿主机网络可达且属于正常响应。
2. 使用 `getent ahostsv4` 或 `resolvectl query` 检查域名解析。
3. 使用 `docker info` 和 `systemctl show docker` 检查 daemon 的镜像加速器与代理。
4. 单独执行 `docker pull nginx:1.27-alpine` 复现并验证修复。

## 修复方向

- 中国大陆云服务器优先使用云厂商控制台提供的 Docker Hub 镜像加速地址，并配置到 `/etc/docker/daemon.json`。
- 使用代理时，通过 systemd drop-in 为 Docker daemon 配置 `HTTP_PROXY`、`HTTPS_PROXY` 和 `NO_PROXY`，仅在 shell 中导出代理变量通常无效。
- 若宿主机本身也无法访问 Docker Hub，检查云安全组出站 TCP 443、系统防火墙、DNS 和公网路由。
- 镜像恢复可拉取后再执行 `docker compose up -d --build` 和 `/health` 验证。

