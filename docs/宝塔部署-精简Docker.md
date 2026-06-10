# 宝塔 2核2G + Docker 精简部署

> 原则：**MySQL、Redis 用宝塔装（省内存）**，Docker 只跑 4 个业务容器；**不装 Elasticsearch**。

内存大约占用：MySQL ~400M + Redis ~50M + Docker 四容器 ~1.2G → 2G 机器建议 **加 2G 交换分区（swap）**。

---

## 一、宝塔里先装 3 个东西（软件商店）

1. **Nginx**
2. **MySQL 8.0** → 建库 `edu_policy_db`，用户 `edu_policy`，记密码
3. **Redis** → 保持 `127.0.0.1`，不设密码即可

再装 **Docker**（软件商店 → Docker 管理器）。

---

## 二、上传代码

```bash
cd /www/wwwroot
git clone <你的仓库> zhengtongrenhe
cd zhengtongrenhe
```

---

## 三、配置 backend/.env

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**关键几项**（把密码、域名、密钥改成你的）：

```env
DATABASE_URL=mysql+aiomysql://edu_policy:数据库密码@host.docker.internal:3306/edu_policy_db?charset=utf8mb4
REDIS_URL=redis://host.docker.internal:6379/0
CELERY_EAGER=false
SECRET_KEY=用python生成的长随机串
LLM_API_KEY=sk-你的DeepSeek密钥

ELASTICSEARCH_URL=http://127.0.0.1:9200
ATTACHMENT_DIR=./data/attachments
```

> `host.docker.internal` 让容器访问宝塔本机的 MySQL/Redis（compose 里已配置）。

---

## 四、一条命令启动（4 容器）

项目根目录创建 `.env`（给前端构建用）：

```bash
echo "NEXT_PUBLIC_API_URL=https://你的域名.com" > .env
```

构建并启动：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

查看状态：

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```

---

## 五、宝塔 Nginx 反代（复制到网站配置）

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 300s;
}

location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

网站 → SSL → 申请 Let's Encrypt → 强制 HTTPS。

---

## 六、验收

1. 打开 `https://你的域名.com` → 首页
2. 登录 `admin` / `admin123` → **立刻改密码**
3. 监测页 → 立即采集 → 有数据即成功

---

## 七、建议（2G 机器）

| 项 | 建议 |
|----|------|
| swap | 宝塔 → 系统 → .swap 加 **2048MB** |
| 多用户 | 管理后台可关闭多用户模式 |
| 定时采集 | beat 已包含；任务多时可先手动采集 |
| 更新 | `git pull && docker compose -f docker-compose.prod.yml up -d --build` |

---

## 和「完整 compose」的区别

| 完整 docker-compose.yml | docker-compose.prod.yml（本方案） |
|-------------------------|-----------------------------------|
| Postgres + ES + Redis 全在 Docker | MySQL/Redis 用宝塔 |
| 内存要 4G+ | 2G 可跑 |
| 步骤多 | **配 .env → compose up → Nginx** |

---

## 常见问题

**构建 frontend 失败**  
确认根目录 `.env` 里 `NEXT_PUBLIC_API_URL` 是 **https 域名**（与 Nginx 一致）。

**数据库连不上**  
MySQL 用户权限选「本地」；`DATABASE_URL` 主机必须是 `host.docker.internal`。

**内存爆掉 / OOM**  
加 swap；宝塔 MySQL 设置里调小 `innodb_buffer_pool_size`（如 128M）。
