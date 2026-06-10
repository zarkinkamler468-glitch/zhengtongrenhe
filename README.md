# 教育政策智能监测平台

政务教育官网监测、采集、AI 解读与多租户管理。

## 快速启动（Windows）

| 命令 | 说明 |
|------|------|
| `setup.bat` | 首次安装依赖 |
| `start.bat` | 启动前后端 |
| `stop.bat` | 停止服务 |
| `restart.bat` | 重启服务 |

- 前端：http://localhost:3001  
- 后端：http://localhost:8000/docs  
- 默认账号：`admin` / `admin123`

## 目录结构

```
zhengtongrenhe/
├── docs/                    # 需求与开发文档
├── scripts/                 # 本地开发脚本（dev.ps1）
├── backend/                 # FastAPI 后端
│   ├── app/                 # 业务代码
│   │   ├── api/             # REST 接口
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 业务逻辑
│   │   ├── crawler/         # 采集引擎
│   │   ├── tasks/           # Celery 任务
│   │   └── data/            # 预设监测源数据
│   ├── scripts/             # 维护/探测脚本
│   │   ├── probes/          # 教育部/栏目探测（一次性调试）
│   │   ├── dev/             # MySQL、启动自检
│   │   └── output/          # 脚本运行产物（不入库）
│   ├── data/                # 运行时数据（附件、本地库，不入库）
│   ├── requirements.txt     # 生产依赖
│   └── requirements-local.txt
├── frontend/                # Next.js 前端
│   ├── src/app/             # 页面路由
│   ├── src/components/      # UI 组件
│   └── public/              # 静态资源
└── docker-compose.yml       # Docker 部署（可选）
```

## 文档

- [开发文档](docs/开发文档.md)
- [需求文档 V1.0](docs/教育政策智能监测平台%20V1.0.docx)

## 部署

生产环境（宝塔 2核2G）：见 [docs/宝塔部署-精简Docker.md](docs/宝塔部署-精简Docker.md)，执行 `docker compose -f docker-compose.prod.yml up -d --build`。
