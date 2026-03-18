# Docker 部署方案

## 1. 概述

本文档描述价格附件生成系统的 Docker 部署方案。

### 1.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        部署架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│   │   客户端      │────▶│   FastAPI    │────▶│   Oracle    │  │
│   │  (浏览器/API) │     │   (应用)      │     │  (外部数据库) │  │
│   └──────────────┘     └──────────────┘     └─────────────┘  │
│                                │                                   │
│                                ▼                                   │
│                        ┌──────────────┐                           │
│                        │  静态文件目录  │                           │
│                        │ (下载文件)     │                           │
│                        └──────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 容器说明

| 容器名称 | 镜像 | 说明 |
|----------|------|------|
| contract-app | 自建 | 价格附件生成系统应用（uvicorn） |

### 1.3 部署模式

- **内网使用**: 直接使用 uvicorn 服务（推荐）
- **公网使用**: 如需 HTTPS，可在前端配置 Nginx 或其他反向代理

---

## 2. 环境要求

### 2.1 硬件要求

| 环境 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 通用 | 2核+ | 4GB+ | 50GB+ |

### 2.2 软件要求

- Docker Engine 20.10+
- Docker Compose 2.0+

---

## 3. Oracle 数据库配置

### 3.1 方案说明

应用容器通过 `ORACLE_DSN` 环境变量连接**外部 Oracle 数据库**，无需在 Docker 中部署 Oracle。

### 3.2 Oracle Instant Client

Oracle Instant Client 已集成到 Docker 镜像中（位于 `deploy/docker/instantclient_21_19/`），无需额外配置。

---

## 4. Docker 配置

### 4.1 目录结构

```
deploy/
├── docker/
│   ├── Dockerfile                   # 应用镜像构建
│   ├── docker-compose.yml           # Docker 编排配置
│   ├── docker-compose.remote.yml    # 远程部署配置
│   ├── instantclient_21_19/        # Oracle Instant Client
│   ├── .env.example                 # 环境变量模板
│   └── scripts/
│       └── push-image.sh            # 镜像推送脚本
```

### 4.2 环境变量

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| ORACLE_DSN | Oracle 连接字符串 | - | ✅ |
| APP_DEBUG | 调试模式 | false | - |
| LOGGING_LEVEL | 日志级别 | INFO | - |
| DATABASE_MIN_CONNECTIONS | 最小连接数 | 5 | - |
| DATABASE_MAX_CONNECTIONS | 最大连接数 | 20 | - |
| DOWNLOADS_BASE_URL | 下载 URL 基础地址 | http://localhost:8000 | - |
| TEMPLATE_PATH | 模板目录 | config/templates | - |
| SECURITY_API_KEYS | API Key 列表 | - | ✅ |

### 4.3 配置文件

#### .env 示例

```bash
# 必需配置
ORACLE_DSN=oracle://username:password@host:port/service_name
SECURITY_API_KEYS=[{"key":"sk_prod_xxx","name":"生产环境","enabled":true}]

# 可选配置
APP_DEBUG=false
LOGGING_LEVEL=INFO
```

---

## 5. 本地部署

### 5.1 构建镜像

```bash
cd /Users/yan/khb/contract

# 构建镜像
docker build -f deploy/docker/Dockerfile -t docker-app:latest .
```

### 5.2 启动服务

```bash
cd deploy/docker

# 复制环境变量模板
cp .env.example .env
vim .env  # 编辑配置

# 启动服务
docker-compose up -d
```

### 5.3 验证部署

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# API 测试
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-api-key>" \
  -d '{"wybs": "2026030006"}'
```

---

## 6. 远程部署

### 6.1 推送镜像

```bash
cd /Users/yan/khb/contract

# 构建并推送镜像
docker build -f deploy/docker/Dockerfile -t docker-app:latest .
./deploy/docker/scripts/push-image.sh
```

### 6.2 远程服务器配置

```bash
ssh root@192.168.20.162

# 创建应用目录
mkdir -p /opt/contract-app
```

### 6.3 复制配置文件

需要复制以下文件到远程服务器：
- `docker-compose.yml` 或 `docker-compose.remote.yml`
- `.env`（配置 Oracle 连接等）
- `config/` 目录（配置文件和模板）

### 6.4 启动服务

```bash
cd /opt/contract-app
docker-compose up -d
```

---

## 7. 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 进入容器
docker exec -it contract-app /bin/bash

# 查看状态
docker-compose ps

# 完全重建（清除卷）
docker-compose down -v
docker-compose up -d
```

---

## 8. 数据持久化

### 8.1 卷配置

| 卷名 | 用途 | 容器路径 |
|------|------|----------|
| contract-output | 下载文件 | /app/output |

### 8.2 备份

```bash
# 备份输出目录
docker cp contract-app:/app/output/downloads ./downloads-backup/

# 备份配置
tar -czvf config-backup.tar.gz /opt/contract-app/config/
```

---

## 9. 监控与运维

### 9.1 健康检查

应用提供健康检查端点：

```bash
curl http://localhost:8000/api/v1/health
```

### 9.2 日志管理

```bash
# 应用日志
docker-compose logs -f

# Docker 日志轮转
# 可在 daemon.json 中配置
```

### 9.3 磁盘清理

```bash
# 清理过期文件（超过 24 小时）
docker exec contract-app python -c "from src.utils.file_cleaner import run_cleanup; run_cleanup('/app/output/downloads')"
```

---

## 10. 故障排查

### 10.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Oracle 连接失败 | 网络/防火墙 | 检查 Oracle 端口 1521 |
| 磁盘空间不足 | 下载文件积累 | 清理过期文件或扩容 |
| 应用启动失败 | 配置错误 | 检查环境变量 |
| 内存不足 | 连接数过多 | 调整连接池配置 |

### 10.2 调试命令

```bash
# 进入容器
docker exec -it contract-app /bin/bash

# 查看进程
docker top contract-app

# 查看资源使用
docker stats

# 查看网络
docker network inspect contract_default
```

---

## 11. 安全建议

1. **不要在代码中硬编码密码**，使用环境变量
2. **限制 API Key 权限**，生产环境使用只读账号
3. **定期更换密码**，至少90天更换一次
4. **内网使用**，建议只在内部网络访问
5. **配置防火墙**，只开放必要端口

---

## 12. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本 |
| v1.1 | 2026-03-18 | 移除 Nginx，简化内网部署配置 |
