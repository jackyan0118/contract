# Docker 部署指南

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd contract

# 进入部署目录
cd deploy/docker
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（确保 ORACLE_DSN 指向正确的外部 Oracle 数据库）
vim .env
```

### 3. 启动服务

#### 开发环境

```bash
# 启动应用 + Nginx
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

#### 生产环境

```bash
# 创建生产配置
cp .env.example .env.production

# 编辑生产配置（必须修改密码）
vim .env.production

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d --build
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

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
├── .env.example              # 环境变量模板
├── Dockerfile                # 应用镜像构建
├── docker-compose.yml        # 开发环境配置
├── docker-compose.prod.yml   # 生产环境配置
├── nginx.conf               # 开发环境 Nginx
├── nginx.prod.conf          # 生产环境 Nginx
├── instantclient_21_19/    # Oracle Instant Client（已集成）
├── scripts/
│   └── entrypoint.sh        # 入口脚本
└── README.md                # 本文件
```

## Oracle 数据库配置

所有环境均使用**外部 Oracle 数据库**，通过 `ORACLE_DSN` 环境变量配置。

### 配置示例

修改 `.env` 文件：

```bash
# 格式: oracle://username:password@host:port/service_name
ORACLE_DSN=oracle://read_db:YourPassword@172.16.15.6:1521/oadata
```

### 可用环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ORACLE_DSN | Oracle 连接字符串 | oracle://read_db:@localhost:1521/oadata |
| DATABASE_MIN_CONNECTIONS | 最小连接数 | 2 |
| DATABASE_MAX_CONNECTIONS | 最大连接数 | 10 |
| DATABASE_CONNECT_TIMEOUT | 连接超时(秒) | 30 |
| DATABASE_COMMAND_TIMEOUT | 命令超时(秒) | 60 |

## 常见问题

### 1. Oracle 连接失败

```bash
# 检查 Oracle 网络连通性
telnet 172.16.15.6 1521

# 查看应用日志
docker-compose logs app

# 确认 Oracle 服务正常运行
```

### 2. 磁盘空间不足

```bash
# 清理未使用的 Docker 资源
docker system prune -a

# 清理过期文件
docker exec contract-app python -c "from src.utils.file_cleaner import run_cleanup; run_cleanup('/app/output/downloads')"
```

### 3. 应用启动失败

```bash
# 查看应用日志
docker-compose logs app

# 进入容器调试
docker exec -it contract-app /bin/bash
```

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 查看更新日志
docker-compose logs -f
```

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（慎用）
docker-compose down -v
```

## 备份与恢复

### 备份

```bash
# 备份配置文件
cp .env .env.backup

# 备份数据卷
docker run --rm -v contract_output:/data -v $(pwd):/backup alpine \
  tar czf /backup/contract-output.tar.gz /data
```

### 恢复

```bash
# 恢复数据卷
docker run --rm -v contract_output:/data -v $(pwd):/backup alpine \
  tar xzf /backup/contract-output.tar.gz -C /
```
