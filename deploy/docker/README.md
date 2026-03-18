# Docker 部署指南

## 快速开始

### 1. 环境准备

```bash
# 进入部署目录
cd deploy/docker
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# API 测试
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-api-key>" \
  -d '{"wybs": "TEST001"}'
```

## 目录结构

```
deploy/docker/
├── .env.example          # 环境变量模板
├── Dockerfile            # 应用镜像构建
├── docker-compose.yml   # 统一配置
├── nginx.conf           # Nginx 配置
├── instantclient_21_19/ # Oracle Instant Client
└── scripts/
    └── entrypoint.sh    # 入口脚本
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ORACLE_DSN | Oracle 连接字符串 | （必须配置） |
| APP_DEBUG | 调试模式 | false |
| LOGGING_LEVEL | 日志级别 | INFO |
| DATABASE_MIN_CONNECTIONS | 最小连接数 | 5 |
| DATABASE_MAX_CONNECTIONS | 最大连接数 | 20 |
| DOWNLOADS_BASE_URL | 下载 URL 基础地址 | http://localhost:8000 |
| SECURITY_API_KEYS | API Key 列表 | （必须配置） |

## Oracle 数据库配置

配置外部 Oracle 数据库连接：

```bash
# 格式: oracle://username:password@host:port/service_name
ORACLE_DSN=oracle://read_db:YourPassword@172.16.15.6:1521/oadata
```

## 常用命令

```bash
# 启动
docker-compose up -d --build

# 停止
docker-compose down

# 查看日志
docker-compose logs -f app

# 进入容器
docker exec -it contract-app /bin/bash

# 重启
docker-compose restart
```

## 磁盘空间清理

```bash
# 清理过期文件
docker exec contract-app python -c "from src.utils.file_cleaner import run_cleanup; run_cleanup('/app/output/downloads')"
```
