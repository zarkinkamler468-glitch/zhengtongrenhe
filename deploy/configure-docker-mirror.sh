#!/bin/bash
# 国内服务器配置 Docker 镜像加速（腾讯云优先）
set -e

MIRRORS='[
  "https://mirror.ccs.tencentyun.com",
  "https://docker.1ms.run",
  "https://docker.xuanyuan.me"
]'

DAEMON=/etc/docker/daemon.json

if [ ! -d /etc/docker ]; then
  mkdir -p /etc/docker
fi

if [ -f "$DAEMON" ]; then
  cp "$DAEMON" "${DAEMON}.bak.$(date +%Y%m%d%H%M%S)"
  echo "已备份原配置: ${DAEMON}.bak.*"
fi

cat > "$DAEMON" <<EOF
{
  "registry-mirrors": ${MIRRORS},
  "max-concurrent-downloads": 3,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl daemon-reload
systemctl restart docker

echo ""
echo "Docker 镜像加速已配置，当前 mirrors:"
docker info 2>/dev/null | grep -A5 "Registry Mirrors" || true
echo ""
echo "下一步: bash deploy/pull-base-images.sh"
