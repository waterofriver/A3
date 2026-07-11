ARG BASE_REGISTRY=docker.io
FROM ${BASE_REGISTRY}/library/node:22-alpine AS dependencies
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm config set registry https://registry.npmmirror.com
RUN pnpm install --frozen-lockfile

FROM ${BASE_REGISTRY}/library/node:22-alpine AS builder
RUN corepack enable
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_AGENT_MODE="mock"
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_AGENT_MODE=$NEXT_PUBLIC_AGENT_MODE \
    NEXT_OUTPUT_MODE=standalone
RUN pnpm build

FROM ${BASE_REGISTRY}/library/node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
