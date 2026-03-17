# Docker 部署方案

## 1. 概述

本文档描述价格附件生成系统的 Docker 部署方案，重点考虑 Oracle 数据库环境的集成。

### 1.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        生产环境架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│   │   Nginx      │────▶│   FastAPI    │────▶│   Oracle    │  │
│   │  (反向代理)   │     │   (应用)      │     │  (数据库)    │  │
│   └──────────────┘     └──────────────┘     └─────────────┘  │
│         │                    │                                   │
│         │                    ▼                                   │
│         │            ┌──────────────┐                           │
│         └───────────▶│  静态文件目录  │                           │
│                      │ (下载文件)     │                           │
│                      └──────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 容器说明

| 容器名称 | 镜像 | 说明 |
|----------|------|------|
| contract-app | 自建 | 价格附件生成系统应用 |
| contract-nginx | nginx:alpine | 反向代理和静态文件服务 |
| oracle-db | oracle/database:19.3.0-ee | Oracle 19c 数据库（可选） |

---

## 2. 环境要求

### 2.1 硬件要求

| 环境 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发/测试 | 2核 | 4GB | 50GB |
| 生产 | 4核+ | 8GB+ | 100GB+ |

### 2.2 软件要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- Oracle Instant Client (用于 Thick 模式)

---

## 3. Oracle 数据库部署方案

### 3.1 方案一：使用外部 Oracle 数据库（推荐生产环境）

生产环境建议使用现有的 Oracle 数据库服务器，应用容器通过网络连接。

**配置示例：**

```yaml
# docker-compose.prod.yml 环境变量
ORACLE_DSN=oracle://username:password@oracle-host:1521/service_name
```

### 3.2 方案二：Docker 运行 Oracle

对于开发/测试环境，可以使用 Oracle Docker 镜像。

**docker-compose.yml 配置：**

```yaml
version: '3.8'

services:
  oracle-db:
    image: container-registry.oracle.com/database/express:21.3.0-xe
    container_name: contract-oracle
    environment:
      ORACLE_PWD: OraclePass123!
      ORACLE_CHARACTER: AL32UTF8
    ports:
      - "1521:1521"
      - "5500:5500"
    volumes:
      - oracle-data:/opt/oracle/oradata
    networks:
      - contract-network

volumes:
  oracle-data:
```

**注意：** Oracle Express Edition (XE) 免费但有资源限制。

### 3.3 方案三：Oracle Instant Client（已集成）

Oracle Instant Client 已预先下载到项目本地，无需每次构建时下载。

**文件位置：**
```
deploy/docker/instantclient_21_19/
```

**Dockerfile 使用本地 Instant Client：**

```dockerfile
# 复制 Oracle Instant Client（本地目录）
COPY instantclient_21_19 /opt/oracle/instantclient

# 设置环境变量
ENV ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient
ENV TNS_ADMIN=/opt/oracle/instantclient/network/admin
```

**docker-compose 运行时挂载（可选，用于调试）：**
```yaml
volumes:
  - ./instantclient_21_19:/opt/oracle/instantclient:ro
```

---

## 4. Docker 配置

### 4.1 目录结构

```
deploy/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx.conf
│   ├── .env.example
│   └── scripts/
│       └── entrypoint.sh
└── README.md
```

### 4.2 Dockerfile

```dockerfile
# 阶段1: 构建
FROM python:3.11-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir --user -e .

# 阶段2: 运行
FROM python:3.11-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 Oracle Instant Client
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH \
    ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient \
    PYTHONUNBUFFERED=1

# 创建输出目录
RUN mkdir -p /app/output/downloads

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.3 Docker Compose 配置

#### 4.3.1 开发环境 (docker-compose.yml)

```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: contract-app
    ports:
      - "8000:8000"
    volumes:
      - ../config:/app/config:ro
      - contract-output:/app/output
    environment:
      - APP_DEBUG=true
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
      - DATABASE_DSN=${ORACLE_DSN}
      - DATABASE_MIN_CONNECTIONS=2
      - DATABASE_MAX_CONNECTIONS=10
      - LOGGING_LEVEL=DEBUG
      - DOWNLOADS_STORAGE_DIR=/app/output/downloads
      - DOWNLOADS_BASE_URL=http://localhost:8000
      - ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient
    env_file:
      - .env
    networks:
      - contract-network
    depends_on:
      - oracle-db
    restart: unless-stopped

  oracle-db:
    image: container-registry.oracle.com/database/express:21.3.0-xe
    container_name: contract-oracle
    environment:
      ORACLE_PWD: ${ORACLE_PASSWORD:-OraclePass123!}
    ports:
      - "1521:1521"
      - "5500:5500"
    volumes:
      - oracle-data:/opt/oracle/oradata
    networks:
      - contract-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: contract-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - contract-output:/app/output:ro
    networks:
      - contract-network
    depends_on:
      - app
    restart: unless-stopped

networks:
  contract-network:
    driver: bridge

volumes:
  contract-output:
  oracle-data:
```

#### 4.3.2 生产环境 (docker-compose.prod.yml)

```yaml
version: '3.8'

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: contract-app-prod
    volumes:
      - contract-output:/app/output
      - ./config/production.yaml:/app/config/settings.yaml:ro
    environment:
      - APP_DEBUG=false
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
      - DATABASE_DSN=${ORACLE_DSN}
      - DATABASE_MIN_CONNECTIONS=5
      - DATABASE_MAX_CONNECTIONS=20
      - LOGGING_LEVEL=INFO
      - DOWNLOADS_STORAGE_DIR=/app/output/downloads
      - DOWNLOADS_BASE_URL=https://api.yourcompany.com
      - SECURITY_API_KEYS=${API_KEYS}
    env_file:
      - .env.production
    networks:
      - contract-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  nginx:
    image: nginx:alpine
    container_name: contract-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - contract-output:/app/output:ro
    networks:
      - contract-network
    depends_on:
      - app
    restart: always

networks:
  contract-network:
    driver: bridge

volumes:
  contract-output:
```

### 4.4 Nginx 配置

#### 4.4.1 开发环境 (nginx.conf)

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    sendfile on;
    keepalive_timeout 65;

    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # API 代理
        location /api/ {
            proxy_pass http://app/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 静态文件下载
        location /static/ {
            alias /app/output/;
            autoindex off;
            expires 24h;
            add_header Cache-Control "public, immutable";
        }

        # 健康检查
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
```

#### 4.4.2 生产环境 (nginx.prod.conf)

```nginx
events {
    worker_connections 4096;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    upstream app {
        server app:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        server_name api.yourcompany.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourcompany.com;

        # SSL 配置
        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # 安全头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API 代理
        location /api/ {
            proxy_pass http://app/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Connection "";

            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 静态文件下载
        location /static/ {
            alias /app/output/;
            autoindex off;
            expires 24h;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options "nosniff";
        }

        # 健康检查
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
```

### 4.5 环境变量配置

#### .env.example

```bash
# 应用配置
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

# Oracle 数据库配置
ORACLE_DSN=oracle://read_db:Skhb1189!@172.16.15.6:1521/oadata
ORACLE_USERNAME=read_db
ORACLE_PASSWORD=Skhb1189!
ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient

# 日志配置
LOGGING_LEVEL=INFO

# 下载配置
DOWNLOADS_STORAGE_DIR=/app/output/downloads
DOWNLOADS_BASE_URL=http://localhost:8000

# 安全配置
SECURITY_API_KEYS=[{"key":"sk_prod_xxx","name":"生产环境","enabled":true}]
```

#### .env.production

```bash
# 生产环境必须修改密码
APP_DEBUG=false
APP_HOST=0.0.0.0
APP_PORT=8000

ORACLE_DSN=oracle://prod_user:YOUR_PASSWORD@oracle.yourcompany.com:1521/PROD
ORACLE_USERNAME=prod_user
ORACLE_PASSWORD=YOUR_STRONG_PASSWORD
ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient

LOGGING_LEVEL=INFO

DOWNLOADS_STORAGE_DIR=/app/output/downloads
DOWNLOADS_BASE_URL=https://api.yourcompany.com

# 生产环境 API Keys
SECURITY_API_KEYS=[{"key":"sk_prod_YOUR_KEY","name":"生产环境","enabled":true}]
```

---

## 5. 部署步骤

### 5.1 开发环境部署

```bash
# 1. 进入部署目录
cd deploy/docker

# 2. 复制环境变量文件
cp .env.example .env

# 3. 编辑 .env 文件，配置 Oracle 连接信息
vim .env

# 4. 构建并启动容器
docker-compose up -d --build

# 5. 查看日志
docker-compose logs -f app

# 6. 测试接口
curl http://localhost:8000/health
```

### 5.2 生产环境部署

```bash
# 1. 进入部署目录
cd deploy/docker

# 2. 创建生产环境配置
cp .env.example .env.production

# 3. 编辑生产环境配置
vim .env.production

# 4. 构建生产镜像
docker-compose -f docker-compose.prod.yml build --no-cache

# 5. 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 6. 检查服务状态
docker-compose ps
docker-compose logs -f app
```

### 5.3 Oracle 数据库初始化

如果使用 Docker 运行 Oracle，需要初始化数据库：

```bash
# 等待 Oracle 启动完成（约5分钟）
docker logs -f contract-oracle

# 连接到 Oracle
docker exec -it contract-oracle sqlplus sys/OraclePass123!@localhost:1521/XEPDB1 as sysdba

# 创建应用用户和表空间（可选，使用现有数据库时跳过）
CREATE TABLESPACE contract_ts DATAFILE '/opt/oracle/oradata/XE/XEPDB1/contract_ts.dbf' SIZE 100M AUTOEXTEND ON;
CREATE USER contract IDENTIFIED BY "ContractPass123!" DEFAULT TABLESPACE contract_ts;
GRANT CONNECT, RESOURCE TO contract;
```

---

## 6. 数据持久化

### 6.1 卷配置

| 卷名 | 用途 | 路径 |
|------|------|------|
| contract-output | 下载文件 | /app/output |
| oracle-data | Oracle 数据 | /opt/oracle/oradata |

### 6.2 备份策略

```bash
# 备份 Oracle 数据
docker exec contract-oraclerman target / catalog rman/rman@XEPDB1
BACKUP DATABASE FORMAT '/backup/full_%U.bak';
```

---

## 7. 监控与运维

### 7.1 健康检查

```bash
# 应用健康检查
curl http://localhost:8000/health

# Docker 健康状态
docker ps
```

### 7.2 日志管理

```bash
# 查看应用日志
docker-compose logs -f app

# 查看 Nginx 日志
docker-compose logs -f nginx

# 日志轮转（Docker 日志驱动）
# 在 docker-compose.yml 中配置：
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 7.3 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker-compose build --no-cache

# 滚动更新
docker-compose up -d --build

# 回滚（如有必要）
docker-compose rollback
```

---

## 8. 故障排查

### 8.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Oracle 连接失败 | 网络/防火墙 | 检查 Oracle 端口 1521 |
| 磁盘空间不足 | 下载文件积累 | 清理过期文件或扩容 |
| 应用启动失败 | 配置错误 | 检查环境变量 |
| 内存不足 | 连接数过多 | 调整连接池配置 |

### 8.2 调试命令

```bash
# 进入容器
docker exec -it contract-app /bin/bash

# 查看进程
docker top contract-app

# 查看资源使用
docker stats

# 查看网络
docker network inspect contract-network
```

---

## 9. 安全建议

1. **不要在代码中硬编码密码**，使用环境变量
2. **限制 API Key 权限**，生产环境使用只读账号
3. **定期更换密码**，至少90天更换一次
4. **使用 HTTPS**，生产环境必须启用 SSL
5. **配置防火墙**，只开放必要端口
6. **定期备份**，特别是 Oracle 数据库

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本 |
