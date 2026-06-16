# Docker 一键部署（推荐）

适合宝塔 + 2核2G 服务器，**不用**手动装 Python、Node、Redis、Supervisor、Playwright。

## 一、宝塔准备

1. 安装 **Docker**（软件商店搜索 Docker 或 Docker 管理器）
2. 安装 **Nginx**
3. **系统 → Swap** 添加 2048MB（2G 内存建议必做）
4. 防火墙只开 **80、443**

## 二、拉代码

```bash
cd /www/wwwroot
git clone https://ghproxy.net/https://github.com/zarkinkamler468-glitch/zhengtongrenhe.git zhengtongrenhemain
cd zhengtongrenhemain
```

## 三、配置环境

```bash
cp .env.docker.example .env
vi .env
```

必改项：

| 变量 | 说明 |
|------|------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 |
| `MYSQL_PASSWORD` | 应用数据库密码 |
| `SECRET_KEY` | 随机长字符串 |
| `PUBLIC_URL` | 对外访问地址，如 `https://edu.example.com` |
| `LLM_API_KEY` | DeepSeek 密钥（可选） |

## 四、一键启动

```bash
bash deploy/docker-up.sh
```

或：

```bash
docker compose up -d --build
```

首次构建约 5～15 分钟（视网络而定）。

验证：

```bash
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000
```

## 五、宝塔 Nginx 反代

**网站** → 添加站点（你的域名）→ 配置文件加入：

```nginx
client_max_body_size 50m;

location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
}

location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**SSL** → 申请 Let's Encrypt → 强制 HTTPS。

> `PUBLIC_URL` 必须与最终 HTTPS 域名一致。修改后需重建前端：
> `docker compose up -d --build web`

## 六、验收

1. 浏览器打开 `https://你的域名`
2. 登录 `admin` / `admin123`，**立即改密码**
3. **监测** → **立即采集**，有数据即成功

## 七、常用命令

```bash
cd /www/wwwroot/zhengtongrenhemain

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f api
docker compose logs -f celery-worker

# 更新代码
git pull
docker compose up -d --build

# 停止
docker compose down

# 停止并删除数据库（慎用）
docker compose down -v
```

## 容器说明

| 容器 | 作用 |
|------|------|
| mysql | 数据库 |
| redis | 任务队列 |
| api | FastAPI 后端 |
| celery-worker | 采集 / AI 异步任务 |
| celery-beat | 定时巡检 |
| web | Next.js 前端 |

## 说明

- 未包含 Playwright 浏览器（默认监测源不需要，镜像更小、构建更快）
- 数据持久化在 Docker 卷 `mysql_data`、`backend_data`
- 原生宝塔部署见 [部署文档.md](./部署文档.md)
