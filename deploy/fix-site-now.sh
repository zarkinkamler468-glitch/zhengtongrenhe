#!/usr/bin/env bash
# 一键修复：页面无样式 / chunk 404 / 时好时坏（PM2 与 Docker 冲突）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "========== 1. 停止 PM2 前端（避免与 Docker 抢 3000 端口）=========="
if command -v pm2 >/dev/null 2>&1; then
  pm2 delete edu-policy-web 2>/dev/null || true
  pm2 save 2>/dev/null || true
fi

echo "========== 2. 检查 3000 端口 =========="
if command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep ':3000' || echo "（3000 端口当前无监听，正常）"
fi

echo "========== 3. 拉取最新代码 =========="
git pull

echo "========== 4. 宿主机构建前端 =========="
bash deploy/frontend-build.sh

echo "========== 5. 重建 Docker web 容器 =========="
cd "$ROOT/frontend"
[ -f .dockerignore ] && cp .dockerignore .dockerignore.bak || true
cp .dockerignore.prebuilt .dockerignore
cd "$ROOT"

docker compose stop web 2>/dev/null || true
docker compose rm -f web 2>/dev/null || true
WEB_DOCKERFILE=Dockerfile.prebuilt docker compose build --no-cache web
docker compose up -d --force-recreate web api celery-worker celery-beat

cd "$ROOT/frontend"
[ -f .dockerignore.bak ] && mv .dockerignore.bak .dockerignore || true

echo "========== 6. 等待并校验 =========="
sleep 5
bash deploy/verify-web-deploy.sh 127.0.0.1:3000

echo ""
echo "========== 7. 请手动完成（宝塔面板）=========="
echo "  ① 网站 → 配置文件：按 deploy/baota-nginx.conf 更新 location / 块"
echo "     必须有: proxy_hide_header Cache-Control;"
echo "             add_header Cache-Control \"no-store...\" always;"
echo "  ② 网站 → 清除缓存；关闭静态缓存 / CDN / 网站加速"
echo "  ③ 浏览器 Ctrl+Shift+R 或无痕窗口打开"
echo ""
echo "验证公网："
echo "  curl -I https://ce.liujianqiang.online/ | grep -i cache-control"
echo "  （应看到 no-store，不能有 s-maxage=31536000）"
