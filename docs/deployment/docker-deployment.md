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
│   │   Nginx      │────▶│   FastAPI    │────▶│   Oracle    │  │
│   │  (反向代理)   │     │   (应用)      │     │  (外部数据库) │  │
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
│   ├── Dockerfile                # 应用镜像构建
│   ├── docker-compose.yml        # 统一配置
│   ├── nginx.conf               # Nginx 配置
│   ├── instantclient_21_19/     # Oracle Instant Client
│   ├── .env.example             # 环境变量模板
│   └── scripts/
│       └── entrypoint.sh        # 入口脚本
└── README.md                    # 部署指南
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
| SECURITY_API_KEYS | API Key 列表 | - | ✅ |

### 4.3 Nginx 配置

```nginx
# 核心功能
- 静态文件服务 (/static/)
- API 反向代理 (/api/)
- 健康检查 (/health)
- Gzip 压缩
- SSL 支持（可选）
```

---

## 5. 部署步骤

### 5.1 配置环境变量

```bash
cd deploy/docker
cp .env.example .env
vim .env
```

必需配置：

```bash
# Oracle 连接字符串
ORACLE_DSN=oracle://username:password@host:port/service_name

# API Key（JSON 格式）
SECURITY_API_KEYS=[{"key":"sk_prod_xxx","name":"生产环境","enabled":true}]
```

### 5.2 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 5.3 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# API 测试
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-api-key>" \
  -d '{"wybs": "TEST001"}'
```

---

## 6. 常用命令

```bash
# 启动服务
docker-compose up -d --build

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f app

# 进入容器
docker exec -it contract-app /bin/bash

# 查看状态
docker-compose ps
```

---

## 7. 数据持久化

### 7.1 卷配置

| 卷名 | 用途 | 容器路径 |
|------|------|----------|
| contract-output | 下载文件 | /app/output |

### 7.2 备份

```bash
# 备份输出目录
docker run --rm -v contract_output:/data -v $(pwd):/backup alpine \
  tar czf /backup/contract-output.tar.gz /data
```

---

## 8. 监控与运维

### 8.1 健康检查

应用提供健康检查端点：

```bash
curl http://localhost:8000/health
```

### 8.2 日志管理

```bash
# 应用日志
docker-compose logs -f app

# Nginx 日志
docker-compose logs -f nginx

# Docker 日志轮转（docker-compose.yml 中配置）
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 8.3 磁盘清理

```bash
# 清理过期文件（超过 24 小时）
docker exec contract-app python -c "from src.utils.file_cleaner import run_cleanup; run_cleanup('/app/output/downloads')"
```

---

## 9. 故障排查

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Oracle 连接失败 | 网络/防火墙 | 检查 Oracle 端口 1521 |
| 磁盘空间不足 | 下载文件积累 | 清理过期文件或扩容 |
| 应用启动失败 | 配置错误 | 检查环境变量 |
| 内存不足 | 连接数过多 | 调整连接池配置 |

### 9.2 调试命令

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

## 10. 安全建议

1. **不要在代码中硬编码密码**，使用环境变量
2. **限制 API Key 权限**，生产环境使用只读账号
3. **定期更换密码**，至少90天更换一次
4. **使用 HTTPS**，生产环境配置 SSL 证书
5. **配置防火墙**，只开放必要端口

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本 |
