ARG DOCKER_REGISTRY=docker.1panel.live/library

FROM ${DOCKER_REGISTRY}/node:20-bookworm-slim AS builder

WORKDIR /app

# BuildKit 常注入 NODE_ENV=production，会导致 devDependencies 缺失；构建阶段强制 development
ENV NODE_ENV=development

COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci \
    && test -f node_modules/next/dist/bin/next \
    || (echo "ERROR: next 未安装，请检查 npm 镜像与 package-lock.json" && npm ls next && exit 1)

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# 直接调用 next 二进制，避免 PATH 中找不到 node_modules/.bin/next
RUN node node_modules/next/dist/bin/next build

FROM ${DOCKER_REGISTRY}/node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
