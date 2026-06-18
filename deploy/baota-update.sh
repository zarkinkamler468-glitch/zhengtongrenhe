#!/usr/bin/env bash
# 宝塔部署更新：解决 git pull 后页面 ChunkLoadError / 跳回旧版
# 用法:
#   bash deploy/baota-update.sh pm2    # PM2 部署（quick-install）
#   bash deploy/baota-update.sh docker # Docker 部署（推荐：宿主机 npm + 轻量镜像）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODE="${1:-docker}"

echo "==> git pull"
git pull

if [ "$MODE" = "pm2" ]; then
  bash deploy/frontend-build.sh
  echo "==> 重启 PM2"
  pm2 restart edu-policy-api edu-policy-web
  pm2 save
else
  echo "==> 在宿主机构建前端（避免容器内 npm 超时）"
  bash deploy/frontend-build.sh

  echo "==> 打包 web 镜像（Dockerfile.prebuilt，不再容器内 npm ci）"
  cd "$ROOT/frontend"
  if [ -f .dockerignore ]; then
    cp .dockerignore .dockerignore.bak
  fi
  cp .dockerignore.prebuilt .dockerignore

  cd "$ROOT"
  WEB_DOCKERFILE=Dockerfile.prebuilt docker compose build --no-cache web
  docker compose up -d web api celery-worker celery-beat

  cd "$ROOT/frontend"
  if [ -f .dockerignore.bak ]; then
    mv .dockerignore.bak .dockerignore
  fi
fi

echo ""
echo "==> 更新完成。请在宝塔："
echo "    1. 站点 Nginx 参考 deploy/baota-nginx.conf（HTML 不缓存、/_next/static 可缓存）"
echo "    2. 关闭站点「静态缓存 / CDN 全站缓存」"
echo "    3. 浏览器 Ctrl+Shift+R 强刷一次"
