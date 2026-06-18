#!/usr/bin/env bash
# 宝塔部署更新：解决 git pull 后页面 ChunkLoadError / 跳回旧版
# 用法:
#   bash deploy/baota-update.sh pm2    # PM2 部署（quick-install）
#   bash deploy/baota-update.sh docker # Docker 部署
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODE="${1:-docker}"

echo "==> git pull"
git pull

if [ "$MODE" = "pm2" ]; then
  echo "==> 重建前端 (PM2)"
  cd frontend
  if [ -f .env.production ]; then
    echo "    使用 .env.production: $(cat .env.production)"
  else
    echo "    警告: 未找到 frontend/.env.production，请设置 NEXT_PUBLIC_API_URL"
  fi
  npm ci --registry=https://registry.npmmirror.com
  rm -rf .next
  npm run build
  cd "$ROOT"
  echo "==> 重启 PM2"
  pm2 restart edu-policy-api edu-policy-web
  pm2 save
else
  echo "==> 重建 web 容器（无缓存，避免旧 chunk）"
  docker compose build --no-cache web
  docker compose up -d web api celery-worker celery-beat
fi

echo ""
echo "==> 更新完成。请在宝塔："
echo "    1. 站点 Nginx 参考 deploy/baota-nginx.conf（HTML 不缓存、/_next/static 可缓存）"
echo "    2. 关闭站点「静态缓存 / CDN 全站缓存」"
echo "    3. 浏览器 Ctrl+Shift+R 强刷一次"
