# Docker 部署运维手册

## 1. 服务器信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | 192.168.20.162 |
| SSH 用户 | root |
| 应用目录 | /opt/contract-app |
| 镜像名称 | docker-app:latest + nginx:alpine |
| 服务端口 | 80 (HTTP), 443 (HTTPS) |

---

## 2. 本地推送脚本

### 推送镜像到远程服务器

```bash
cd /Users/yan/khb/contract

# 1. 构建镜像
docker build -f deploy/docker/Dockerfile -t docker-app:latest .

# 2. 运行推送脚本
./deploy/docker/scripts/push-image.sh
```

### 推送脚本功能
- 构建 nginx amd64 镜像（适配远程 x86_64 服务器）
- 导出镜像为 tar.gz 文件（压缩传输）
- 复制到远程服务器
- 加载镜像并打标签
- 清理临时文件

---

## 3. 远程服务器操作

### 启动服务

```bash
ssh root@192.168.20.162
cd /opt/contract-app
docker-compose -f docker-compose.remote.yml up -d
```

### 查看状态

```bash
docker-compose ps
docker ps
```

### 查看日志

```bash
# 查看应用日志
docker-compose logs -f

# 查看指定容器日志
docker logs -f contract-app
```

### 重启服务

```bash
docker-compose restart
```

### 停止服务

```bash
docker-compose down
```

### 完全重建（清除卷）

```bash
docker-compose down -v
docker-compose up -d
```

---

## 4. API 访问

### 基础信息

| 项目 | 值 |
|------|-----|
| 基础 URL | http://192.168.20.162 |
| API 文档 | http://192.168.20.162/docs |
| API Key | sk_prod_20260317_a1b2c3d4e5f6 |

### 健康检查

```bash
curl http://192.168.20.162/api/v1/health
```

### 生成文档

```bash
curl -X POST http://192.168.20.162/api/v1/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_prod_20260317_a1b2c3d4e5f6" \
  -d '{"wybs": "2026030006"}'
```

### 获取模板列表

```bash
curl http://192.168.20.162/api/v1/templates \
  -H "Authorization: Bearer sk_prod_20260317_a1b2c3d4e5f6"
```

---

## 5. 配置说明

### 配置文件位置

```
/opt/contract-app/
├── docker-compose.yml    # Docker 编排配置
├── .env                   # 环境变量配置
└── config/               # 应用配置
    ├── settings.yaml      # 应用设置
    ├── template_metadata/ # 模板元数据
    └── templates/        # Word 模板文件
```

### 环境变量

| 变量 | 说明 | 示例值 |
|------|------|--------|
| ORACLE_DSN | Oracle 连接字符串 | oracle://user:pass@host:1521/service |
| SECURITY_API_KEYS | API 密钥列表 | [{"key":"xxx","name":"生产","enabled":true}] |
| LOGGING_LEVEL | 日志级别 | INFO |
| TEMPLATE_PATH | 模板目录 | config/templates |
| DOWNLOADS_BASE_URL | 下载基础 URL | http://192.168.20.162 |

### 修改配置

```bash
# 1. 编辑配置文件
vim /opt/contract-app/.env

# 2. 重启服务使配置生效
docker-compose restart
```

---

## 6. 数据备份

### 备份配置

```bash
# 备份配置目录
tar -czvf config-backup.tar.gz /opt/contract-app/config/

# 备份输出文件
docker cp contract-app:/app/output/downloads ./downloads-backup/
```

### 备份 Oracle 连接信息

确保 .env 文件中的 ORACLE_DSN 已正确配置。

---

## 7. 故障排查

### 常见问题

#### 1. 容器启动失败

```bash
# 查看日志
docker logs contract-app

# 检查配置文件
cat /opt/contract-app/.env
```

#### 2. Oracle 连接失败

- 检查 ORACLE_DSN 配置是否正确
- 检查网络是否可达 Oracle 服务器
- 检查 Oracle 端口 1521 是否开放

```bash
# 测试 Oracle 端口连通性
docker exec contract-app sh -c "echo > /dev/tcp/172.16.15.6/1521"
```

#### 3. 模板文件缺失

```bash
# 检查模板目录
ls -la /opt/contract-app/config/templates/

# 检查模板元数据
ls -la /opt/contract-app/config/template_metadata/
```

#### 4. 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理过期文件
docker exec contract-app python -c "from src.utils.file_cleaner import run_cleanup; run_cleanup('/app/output/downloads')"
```

#### 5. 容器频繁重启

```bash
# 查看容器状态
docker ps -a

# 查看重启日志
docker logs --tail 50 contract-app
```

### 完全重置

```bash
# 停止并删除所有资源
docker-compose down -v

# 删除配置目录（谨慎）
rm -rf /opt/contract-app/config

# 从头部署
# 1. 重新推送镜像
# 2. 重新复制配置文件
# 3. 启动服务
```

---

## 8. 更新部署

### 步骤

```bash
# 1. 本地构建新镜像
cd /Users/yan/khb/contract
docker build -f deploy/docker/Dockerfile -t docker-app:latest .

# 2. 推送镜像
./deploy/docker/scripts/push-image.sh

# 3. 远程服务器更新
ssh root@192.168.20.162
cd /opt/contract-app

# 拉取新镜像（如果有私有仓库）
# docker pull docker-app:latest

# 重启服务
docker-compose down
docker-compose up -d
```

---

## 9. 安全建议

1. **修改 API Key**: 生产环境请更换 SECURITY_API_KEYS
2. **限制端口**: 只开放必要端口 (8000)
3. **定期备份**: 定期备份配置和输出文件
4. **日志监控**: 定期检查日志文件

---

## 10. 联系信息

如有问题，请联系开发团队。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-18 | 初始版本 |
