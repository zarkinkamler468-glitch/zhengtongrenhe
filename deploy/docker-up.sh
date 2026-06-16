#!/bin/bash
# Docker 一键启动
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.docker.example .env
  echo "已生成 .env，请先编辑 MYSQL 密码、SECRET_KEY、PUBLIC_URL 后再运行本脚本"
  exit 1
fi

if grep -q "请改成" .env 2>/dev/null; then
  echo "请先编辑 .env 中的密码和 PUBLIC_URL"
  exit 1
fi

docker compose up -d --build

echo ""
echo "=========================================="
echo " Docker 已启动"
echo " 后端: http://127.0.0.1:8000/health"
echo " 前端: http://127.0.0.1:3000"
echo ""
echo " 宝塔 Nginx 反代到 8000(/api/) 和 3000(/)"
echo " 登录: admin / admin123"
echo "=========================================="
