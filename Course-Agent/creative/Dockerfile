ARG BASE_REGISTRY=docker.io
# 多阶段-依赖安装层
FROM ${BASE_REGISTRY}/library/node:22-alpine AS dependencies
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
# 合并配置源+安装，增加超时参数，避免下载卡死
RUN pnpm config set registry https://registry.npmmirror.com \
    && pnpm install --frozen-lockfile --fetch-timeout 300000

# 多阶段-构建层
FROM ${BASE_REGISTRY}/library/node:22-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
# 复用依赖层缓存 node_modules
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
# 构建参数注入
ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_AGENT_MODE="mock"
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_AGENT_MODE=$NEXT_PUBLIC_AGENT_MODE \
    NEXT_OUTPUT_MODE=standalone
RUN pnpm build

# 多阶段-生产运行层（最小镜像，无构建依赖）
FROM ${BASE_REGISTRY}/library/node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
# 创建低权限运行用户
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs
# 仅拷贝运行必需文件
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
# 切换非root用户启动，加固容器安全
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]