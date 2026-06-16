#!/bin/bash
# 预先拉取构建所需基础镜像（配置镜像加速后执行）
set -e
cd "$(dirname "$0")/.."

echo "==> 拉取 python / node / mysql / redis ..."
docker pull python:3.11-slim
docker pull node:20-bookworm-slim
docker pull node:20-alpine
docker pull mysql:8.0
docker pull redis:7-alpine

echo "==> 基础镜像就绪，可执行: bash deploy/docker-up.sh"
