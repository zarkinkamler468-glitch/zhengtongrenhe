#!/bin/bash
# 国内服务器配置 Docker Hub 镜像加速（解决 pull / build 超时、not found）
set -e

MIRRORS='[
  "https://docker.1ms.run",
  "https://docker.xuanyuan.me",
  "https://hub.rat.dev"
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
echo "测试拉取: docker pull python:3.11-slim"
