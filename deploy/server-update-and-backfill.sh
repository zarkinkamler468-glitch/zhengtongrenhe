#!/usr/bin/env bash
# 服务器上一键：拉代码 → 重建容器 → 同步预设 → 补采空正文 → 批量修正关键信息
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LIMIT="${1:-500}"

echo "==> git pull"
git pull

echo "==> docker compose build & up (web 无缓存)"
docker compose build --no-cache web
docker compose up -d --build api celery-worker celery-beat web

echo "==> 等待 API 就绪..."
sleep 8

echo "==> 补采正文为空的文章 (limit=${LIMIT})"
docker compose exec -T api python scripts/backfill_empty_content.py --limit "$LIMIT" --fix-key-info

echo "==> 完成。建议在网页「政策知识库」执行「批量修正截止时间」或「批量重新分析」"
echo "    或在 API 容器内: curl -X POST .../articles/batch/fix-deadlines"
