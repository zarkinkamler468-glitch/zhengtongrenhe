# 教育政策智能监测平台

政务教育官网监测、采集、AI 解读与多租户管理。

## 部署

**推荐：Docker 一键部署** → [docs/Docker部署.md](docs/Docker部署.md)

宝塔原生部署（不用 Docker）→ [docs/部署文档.md](docs/部署文档.md)

## 快速启动（Docker）

```bash
cp .env.docker.example .env   # 编辑密码与域名
bash deploy/docker-up.sh
```

## 桌面客户端（Windows）

连接线上服务器 `https://ce.liujianqiang.online`，本机无需后端。

```powershell
cd desktop
start.bat            # 预览（推荐，双击或命令行均可）
build.bat            # 生成安装包 → desktop\release\
```

若要用 PowerShell 脚本，需先：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 目录

```
zhengtongrenhe/
├── backend/           # FastAPI 后端
├── frontend/          # Next.js 前端
├── docker-compose.yml # Docker 编排
├── deploy/            # 部署脚本
└── docs/              # 文档
```

## 默认账号

- 用户名：`admin`
- 密码：`admin123`（上线后务必修改）
