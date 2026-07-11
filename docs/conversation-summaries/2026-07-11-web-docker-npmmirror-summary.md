# Web Docker npmmirror 修复对话总结

日期：2026-07-11  
工作窗口：云服务器前端依赖下载超时修复

## 问题

云服务器构建 Web 镜像时，dependencies 阶段执行 `pnpm install --frozen-lockfile` 访问 `registry.npmjs.org`。下载速度过低且多次超时，最终 pnpm 以 exit code 1 退出。

## 修改

在 `Course-Agent/creative/Dockerfile` 的 dependencies 阶段、冻结安装命令之前加入：

```dockerfile
RUN pnpm config set registry https://registry.npmmirror.com
```

原有 `RUN pnpm install --frozen-lockfile` 保持不变。配置只影响 Docker 构建依赖层，不修改宿主机全局 npm/pnpm 配置，也不进入最终 runner 镜像。

## 验证

- RED：修改前静态契约检查失败，提示 npmmirror 必须配置在 pnpm install 之前。
- GREEN：修改后契约检查通过。
- `docker compose config --quiet`：通过。
- 前端测试：`55 passed`。
- ESLint：通过。
- TypeScript 类型检查：通过。
- Next.js 生产构建：通过，9 个业务路由生成成功。
- 文档验收和 `git diff --check`：通过。

本地 Docker daemon 的外部镜像仓库连通性不能代表云服务器环境，因此未把真实容器依赖下载声明为本地已验证。云端需拉取提交后执行无缓存 Web 构建，并在日志中确认请求目标为 `registry.npmmirror.com`。

## 云端复验

```bash
cd /opt/A3
git pull --ff-only origin main
docker compose build web --no-cache --progress=plain
docker compose up -d
docker compose ps
curl -f http://127.0.0.1:8080/health
```

