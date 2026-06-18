#!/usr/bin/env bash
# 部署后校验 web 容器静态资源是否可访问
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

HOST="${1:-127.0.0.1:3000}"
BASE="http://${HOST}"

echo "==> 检查端口占用"
if command -v ss >/dev/null 2>&1; then
  ss -tlnp | grep ':3000' || true
fi
if command -v pm2 >/dev/null 2>&1 && pm2 list 2>/dev/null | grep -q edu-policy-web; then
  echo "警告: PM2 仍在运行 edu-policy-web，可能与 Docker web 冲突！"
  echo "      Docker 部署请执行: pm2 delete edu-policy-web || true"
fi

if [ -f frontend/.next/BUILD_ID ]; then
  echo "==> 宿主机 BUILD_ID: $(cat frontend/.next/BUILD_ID)"
fi

if docker compose ps web 2>/dev/null | grep -q Up; then
  echo "==> 容器 BUILD_ID:"
  docker compose exec -T web cat .next/BUILD_ID 2>/dev/null || echo "  (无法读取)"
  echo "==> 容器 static 文件数:"
  docker compose exec -T web sh -c 'find .next/static -type f 2>/dev/null | wc -l' || true
fi

echo "==> 请求首页 HTML"
HTML="$(curl -fsS "$BASE/" || { echo "错误: 无法访问 $BASE/"; exit 1; })"

ASSET="$(echo "$HTML" | grep -oE '/_next/static/[^"'\'' ]+\.(js|css)' | head -1 || true)"
if [ -z "$ASSET" ]; then
  echo "警告: 首页 HTML 中未找到 _next/static 资源引用"
else
  echo "==> 校验静态资源: $ASSET"
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "$BASE$ASSET")"
  if [ "$CODE" = "200" ]; then
    echo "OK: $ASSET -> 200"
  else
    echo "错误: $ASSET -> HTTP $CODE（HTML 与 static 版本不一致或容器缺文件）"
    exit 1
  fi
fi

echo "==> 校验 build-id.txt"
if curl -fsS "$BASE/build-id.txt" >/dev/null 2>&1; then
  echo "OK: build-id.txt -> $(curl -fsS "$BASE/build-id.txt")"
else
  echo "提示: /build-id.txt 不可用（旧版本未生成，可忽略）"
fi

echo "==> 验证通过"
