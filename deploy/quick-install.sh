#!/bin/bash
# 极简一键部署（宝塔 CentOS）
# 用法: bash deploy/quick-install.sh /www/wwwroot/zhengtongrenhemain "你的MySQL密码" "https://你的域名.com"
set -e

PROJECT_DIR="${1:-/www/wwwroot/zhengtongrenhemain}"
DB_PASS="${2:-}"
API_URL="${3:-http://127.0.0.1}"

if [ -z "$DB_PASS" ]; then
  echo "用法: bash deploy/quick-install.sh <项目目录> <MySQL密码> [前端API地址]"
  echo "示例: bash deploy/quick-install.sh /www/wwwroot/zhengtongrenhemain 'abc123' 'https://edu.example.com'"
  exit 1
fi

echo "==> 项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

echo "==> 安装 Python 依赖（跳过 Playwright 浏览器）..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
mkdir -p data/attachments

cat > .env <<EOF
DATABASE_URL=mysql+aiomysql://edu_policy:${DB_PASS}@127.0.0.1:3306/edu_policy_db?charset=utf8mb4
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_EAGER=true
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LLM_PROVIDER=deepseek
LLM_API_KEY=
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
ATTACHMENT_DIR=./data/attachments
DEFAULT_CRAWL_INTERVAL_MINUTES=30
EOF

echo "==> 构建前端..."
cd ../frontend
echo "NEXT_PUBLIC_API_URL=${API_URL}" > .env.production
npm install --registry=https://registry.npmmirror.com
npm run build

echo "==> PM2 启动（API + 前端）..."
cd "$PROJECT_DIR"
pm2 delete edu-policy-api edu-policy-web 2>/dev/null || true
pm2 start deploy/ecosystem.config.cjs
pm2 save

echo ""
echo "=========================================="
echo " 部署完成！还需在宝塔做 2 步："
echo " 1. 数据库 edu_policy_db 用户 edu_policy 密码与脚本一致"
echo " 2. 网站 Nginx 反代: /api/ -> 8000, / -> 3000"
echo ""
echo " 验证: curl http://127.0.0.1:8000/api/v1/auth/config"
echo " 登录: admin / admin123"
echo "=========================================="
