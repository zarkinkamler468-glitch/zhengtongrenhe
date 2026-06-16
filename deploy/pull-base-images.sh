#!/bin/bash
# 从阿里云 library 拉取基础镜像（绕过 Docker Hub attestation 404）
set -e
cd "$(dirname "$0")/.."

REG=registry.cn-hangzhou.aliyuncs.com/library
PLATFORM=${PLATFORM:-linux/amd64}

pull() {
  echo "==> docker pull --platform $PLATFORM $1"
  docker pull --platform "$PLATFORM" "$1"
}

echo "==> 拉取 python / node / mysql / redis（阿里云源）..."
pull ${REG}/python:3.11-slim
pull ${REG}/node:20-bookworm-slim
pull ${REG}/node:20-alpine
pull ${REG}/mysql:8.0
pull ${REG}/redis:7-alpine

echo ""
echo "==> 基础镜像就绪，可执行: bash deploy/docker-up.sh"
