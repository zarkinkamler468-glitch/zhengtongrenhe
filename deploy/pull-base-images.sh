#!/bin/bash
# 自动尝试多个国内 Docker Hub 代理，找到可用的写入 .env
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "请先配置 .env: cp .env.docker.example .env && vi .env"
  exit 1
fi

PLATFORM=${PLATFORM:-linux/amd64}
IMAGES=(python:3.11-slim node:20-bookworm-slim node:20-alpine mysql:8.0 redis:7-alpine)

REGISTRIES=(
  "docker.1panel.live/library"
  "docker.m.daocloud.io/library"
  "docker.1ms.run/library"
)

try_registry() {
  local reg=$1
  echo ""
  echo ">>> 测试镜像源: $reg"
  for img in "${IMAGES[@]}"; do
    if ! docker pull --platform "$PLATFORM" "${reg}/${img}"; then
      echo "!!! 失败: ${reg}/${img}"
      return 1
    fi
  done
  echo ">>> 可用: $reg"
  return 0
}

SELECTED=""
for reg in "${REGISTRIES[@]}"; do
  if try_registry "$reg"; then
    SELECTED="$reg"
    break
  fi
done

if [ -z "$SELECTED" ]; then
  echo ""
  echo "所有镜像源均失败。请在 .env 中手动设置 DOCKER_REGISTRY，或检查 Docker 网络。"
  exit 1
fi

if [ -f .env ]; then
  if grep -q '^DOCKER_REGISTRY=' .env; then
    sed -i "s|^DOCKER_REGISTRY=.*|DOCKER_REGISTRY=${SELECTED}|" .env
  else
    echo "DOCKER_REGISTRY=${SELECTED}" >> .env
  fi
else
  echo "DOCKER_REGISTRY=${SELECTED}" > .env
fi

echo ""
echo "已写入 .env: DOCKER_REGISTRY=${SELECTED}"
echo "下一步: bash deploy/docker-up.sh"
