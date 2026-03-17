# 功能设计：ZIP压缩包下载功能

## 1. 需求概述

### 1.1 背景
当前API返回的是Base64编码的Word文件内容，用户端需要自行处理解码和保存。改为返回下载URL后，用户可以直接通过URL下载ZIP压缩包，提升用户体验。

### 1.2 目标
- 将生成的Word文件打包成ZIP压缩包
- 返回可下载的URL地址
- 支持文件过期自动清理

---

## 2. 技术方案

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI                               │
├─────────────────────────────────────────────────────────────┤
│  /generate → 生成Word → ZIP打包 → 保存到静态目录 → 返回URL │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ┌───────────────────┐
                    │  静态文件目录      │
                    │  /downloads/       │
                    │  ├── 20260317/    │
                    │  │   └── xxx.zip  │
                    │  └── ...           │
                    └───────────────────┘
                              ↓
                    ┌───────────────────┐
                    │  Nginx 静态文件   │  ← 生产环境
                    │  /static/downloads│
                    └───────────────────┘
```

### 2.2 文件存储结构

```
output/
├── downloads/
│   ├── 20260317/
│   │   ├── wybs_123456_20260317103000.zip
│   │   └── wybs_789012_20260317103100.zip
│   └── ...
```

**命名规则**: `{wybs}_{时间戳}.zip`

### 2.3 返回格式变更

**当前返回格式**:
```json
{
  "success": true,
  "data": {
    "filename": "xxx.docx",
    "file_base64": "UEsDBBQABgA...",
    "templates_used": ["模板1"]
  }
}
```

**新返回格式**:
```json
{
  "success": true,
  "data": {
    "download_url": "http://localhost:8000/static/downloads/20260317/wybs_123456_20260317103000.zip",
    "filename": "wybs_123456_20260317103000.zip",
    "file_count": 3,
    "expires_in": 3600,
    "templates_used": ["模板6.1", "模板6.2"]
  }
}
```

---

## 3. 现有代码复用分析

### 3.1 FilePacker 复用评估

**文件**: `src/utils/file_packer.py`

| 方法 | 功能 | 复用情况 |
|------|------|----------|
| `pack()` | 多文件打包为ZIP | ✅ 直接复用 |
| `pack_single()` | 单文件处理 | ⚠️ 需修改：打包成ZIP |
| `cleanup()` | 清理临时文件 | ✅ 直接复用 |
| `pack_files_to_base64_zip()` | Base64编码ZIP | ⚠️ 兼容保留 |

**结论**: `FilePacker` 类可复用，只需扩展 `pack_single()` 方法支持单文件也打包成ZIP。

---

## 4. 配置项设计

### 4.1 settings.yaml 配置

```yaml
template:
  # ... 现有配置
  output_dir: output

# 新增：下载服务配置
downloads:
  # URL路径
  url_path: /static/downloads
  # 存储目录
  storage_dir: output/downloads
  # 生成完整URL所需的Base URL
  base_url: "http://localhost:8000"
  # 文件过期时间（秒），默认24小时
  expires_in: 86400
  # 是否启用自动清理
  auto_cleanup: true
  # 定时清理Cron表达式（每天凌晨2点）
  cleanup_cron: "0 2 * * *"
  # 单个文件大小限制（MB）
  max_file_size_mb: 100
  # 磁盘空间告警阈值（%）
  disk_space_threshold: 80
```

### 4.2 Schema变更

```python
class GenerateSuccessData(BaseModel):
    """单文件生成成功数据"""

    download_url: str           # 下载URL
    filename: str               # ZIP文件名
    file_count: int            # ZIP内包含的文件数量
    expires_in: int            # 过期时间（秒）
    templates_used: List[str]  # 使用的模板列表
```

---

## 5. 生产环境部署：Nginx配置

### 5.1 架构变更

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   客户端     │ ───→ │   Nginx      │ ───→ │  FastAPI    │
│             │      │  (静态文件)  │      │  (API服务)  │
└─────────────┘      │  反向代理    │      └─────────────┘
                     └─────────────┘
```

### 5.2 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name api.yourcompany.com;

    # 静态文件目录（FastAPI output/downloads）
    location /static/downloads/ {
        alias /path/to/contract/output/downloads/;
        expires 24h;
        add_header Cache-Control "public, immutable";
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

### 5.3 settings.yaml 生产配置

```yaml
downloads:
  url_path: /static/downloads
  storage_dir: output/downloads
  base_url: "https://api.yourcompany.com"  # 生产环境用HTTPS
  # ...
```

---

## 6. 实现计划

### 6.1 第一阶段：静态文件服务配置

- [x] 在 `config/settings.yaml` 中添加静态文件目录配置
- [x] 在 FastAPI 中配置静态文件路由
- [x] 配置静态文件目录为可访问
- [x] 添加 `base_url` 配置项

### 6.2 第二阶段：ZIP打包功能（复用FilePacker）

- [x] 修改 `FilePacker.pack_single()` 方法支持单文件打包成ZIP
- [x] 添加过期文件清理工具类 `FileCleaner`
- [x] 集成到文档生成流程

### 6.3 第三阶段：URL返回功能

- [x] 修改 `GenerateSuccessData` Schema
- [x] 更新 `/generate` 接口返回URL
- [x] 支持单文件和多文件场景

### 6.4 第四阶段：过期文件清理

- [x] 添加定时任务或启动时清理过期文件
- [x] 配置过期时间（默认24小时）
- [x] 记录清理日志
- [x] 添加磁盘空间检查

### 6.5 第五阶段：安全性增强

- [x] 目录遍历防护：验证文件名安全性

---

## 7. 关键代码变更

### 7.1 新增文件

| 文件 | 说明 |
|------|------|
| `src/utils/file_cleaner.py` | 过期文件清理工具（新增） |

### 7.2 修改文件

| 文件 | 变更内容 |
|------|----------|
| `src/api/schemas.py` | 修改 GenerateSuccessData |
| `src/api/routes/generate.py` | 变更返回逻辑：文件→ZIP→URL |
| `src/main.py` | 添加静态文件路由 |
| `src/utils/file_packer.py` | 修改 pack_single() 方法 |
| `config/settings.yaml` | 添加下载配置 |

---

## 8. 错误处理设计

### 8.1 异常类定义

```python
class ZipPackerError(Exception):
    """ZIP打包异常基类"""
    pass

class SourceFileNotFoundError(ZipPackerError):
    """源文件不存在"""
    pass

class DiskSpaceError(ZipPackerError):
    """磁盘空间不足"""
    pass

class FileExpiredError(ZipPackerError):
    """文件已过期"""
    pass
```

### 8.2 错误场景处理

| 场景 | 处理方式 |
|------|----------|
| ZIP打包失败 | 返回500错误，包含具体错误信息 |
| 源文件不存在 | 跳过并记录日志，返回部分成功 |
| 磁盘空间不足 | 写入前检查空间，不足则报错 |
| 文件过期 | 返回404，引导重新生成 |

---

## 9. 安全性考虑

1. **目录遍历防护**：验证文件名不包含 `../`
2. **文件类型验证**：只允许 `.zip` 文件被下载
3. **访问控制**：
   - 生产环境通过Nginx配置IP白名单
   - 内网可访问静态目录
4. **存储限制**：设置磁盘空间告警（默认80%）

---

## 10. 待确认事项

- [x] 复用现有 FilePacker 类 ✅
- [x] 生产环境使用 Nginx ✅
- [x] 定时清理策略：启动时清理 + 定时任务 ✅
- [x] 不需要保留 Base64 返回方式 ✅

---

## 11. 风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 磁盘空间耗尽 | 高 | 添加磁盘空间监控+告警 |
| 大文件打包内存溢出 | 中 | 使用流式ZIP打包 |
| URL跨域/域名问题 | 中 | 添加 base_url 配置项 |
| 并发请求磁盘竞争 | 中 | 使用独立子目录隔离 |

---

## 12. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-17 | 初始版本 |
| v1.1 | 2026-03-17 | 专家评审后更新：添加base_url配置、复用FilePacker、Nginx配置 |
