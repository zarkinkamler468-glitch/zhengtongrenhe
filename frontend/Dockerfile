ARG DOCKER_REGISTRY=docker.1panel.live/library

FROM ${DOCKER_REGISTRY}/node:20-bookworm-slim AS builder

WORKDIR /app

ENV NODE_OPTIONS=--max-old-space-size=2048

COPY package.json package-lock.json .npmrc ./

# 容器内构建（网络良好时）；国内 VPS 建议用 deploy/frontend-build.sh + Dockerfile.prebuilt
RUN set -eux; \
    npm config set registry https://registry.npmmirror.com; \
    npm config set fetch-timeout 600000; \
    npm config set fetch-retries 10; \
    npm config set maxsockets 5; \
    sed -i 's|https://registry.npmjs.org/|https://registry.npmmirror.com/|g' package-lock.json; \
    rm -rf node_modules; \
    NODE_ENV=development npm ci --no-audit --no-fund \
      || (rm -rf node_modules && NODE_ENV=development npm install --no-audit --no-fund); \
    node -p "'next ' + require('next/package.json').version"; \
    test -f node_modules/next/dist/bin/next

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NODE_ENV=production

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
