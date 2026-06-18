#!/usr/bin/env bash
# 在宿主机构建 Next.js（避免 Docker 内 npm 超时）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$ROOT/frontend"
cd "$FRONTEND"

export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=2048}"

# 从项目 .env 读取公网地址
if [ -f "$ROOT/.env" ]; then
  PUBLIC_URL="$(grep -E '^PUBLIC_URL=' "$ROOT/.env" | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")"
fi
if [ -n "${PUBLIC_URL:-}" ]; then
  export NEXT_PUBLIC_API_URL="$PUBLIC_URL"
  echo ">> NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"
elif [ -f .env.production ]; then
  # shellcheck disable=SC1091
  set -a && source .env.production && set +a
  echo ">> 使用 .env.production"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "错误: 未找到 node，请先在宝塔安装 Node.js 20+"
  exit 1
fi

NODE_MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$NODE_MAJOR" -lt 20 ]; then
  echo "警告: 当前 Node $(node -v)，建议升级到 20+（宝塔 Node 版本管理器）"
fi

echo ">> node $(node -v) | npm $(npm -v)"

npm config set registry https://registry.npmmirror.com
npm config set fetch-timeout 600000
npm config set fetch-retries 10
npm config set maxsockets 5

LOCK_BAK=""
if [ -f package-lock.json ] && grep -q 'registry.npmjs.org' package-lock.json; then
  LOCK_BAK="$(mktemp)"
  cp package-lock.json "$LOCK_BAK"
  sed -i 's|https://registry.npmjs.org/|https://registry.npmmirror.com/|g' package-lock.json
fi

rm -rf node_modules .next

echo ">> npm ci（国内镜像）..."
if ! NODE_ENV=development npm ci --no-audit --no-fund; then
  echo ">> npm ci 失败，改用 npm install..."
  rm -rf node_modules
  NODE_ENV=development npm install --no-audit --no-fund
fi

if [ -n "$LOCK_BAK" ]; then
  mv "$LOCK_BAK" package-lock.json
fi

if [ ! -f node_modules/next/dist/bin/next ]; then
  echo "错误: next 仍未安装成功"
  npm ls next || true
  exit 1
fi

echo ">> next build..."
export NODE_ENV=production
node node_modules/next/dist/bin/next build

if [ ! -f .next/BUILD_ID ]; then
  echo "错误: .next/BUILD_ID 不存在，构建失败"
  exit 1
fi

if [ ! -d .next/standalone ]; then
  echo "错误: 未生成 .next/standalone，请确认 next.config 含 output: standalone"
  exit 1
fi

# 供部署校验与排查 chunk 404
cp .next/BUILD_ID public/build-id.txt

echo ">> 前端构建完成: $(cat .next/BUILD_ID)"
