# Web Docker npmmirror 设计

日期：2026-07-11

## 目标

解决中国大陆云服务器构建 Web 镜像时，`pnpm install --frozen-lockfile` 访问 `registry.npmjs.org` 速度过慢并超时的问题。

## 设计

只修改 `Course-Agent/creative/Dockerfile` 的 dependencies 阶段。在复制依赖清单后、执行冻结安装前增加：

```dockerfile
RUN pnpm config set registry https://registry.npmmirror.com
```

原有 `RUN pnpm install --frozen-lockfile` 保持不变。该配置只存在于 Docker dependencies 构建阶段，不修改云服务器全局 npm/pnpm 配置，不进入最终 runner 镜像，也不改变应用运行行为。

## 验证

- 静态检查确认 registry 配置存在且位于冻结安装命令之前。
- `docker compose config --quiet` 通过。
- 前端测试、Lint、类型检查和生产构建通过。
- 本地 Docker daemon 若仍无法访问基础镜像仓库，只记录外部网络限制；最终效果由云服务器重新执行 `docker compose build web --no-cache` 验证。

