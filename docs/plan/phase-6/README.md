# Phase 6: API 接口模块 - 设计文档

## 概述

实现 RESTful API 接口，支持价格附件的生成和下载。

**时间估算**: 3-4 天

**复杂度**: 中

---

## 一、安全设计

### 1.1 认证机制

**方案**: API Key 认证

```python
# 请求头
Authorization: Bearer <api_key>
```

**配置**：
```yaml
# config/settings.yaml
security:
  api_keys:
    - key: "sk_dev_xxxxx"
      name: "开发环境"
      enabled: true
    - key: "sk_prod_xxxxx"
      name: "生产环境"
      enabled: false
```

**说明**：
- 内部系统使用 API Key 认证
- 生产环境可升级为 JWT

### 1.2 输入验证

```python
# src/api/schemas.py
from pydantic import BaseModel, Field
import re

class GenerateRequest(BaseModel):
    wybs: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Z0-9_-]+$",
        description="报价单号"
    )

class BatchRequest(BaseModel):
    wybs_list: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="报价单号列表"
    )
    async: bool = Field(default=False, description="是否异步处理")

    @validator('wybs_list')
    def validate_wybs_list(cls, v):
        # 去重
        unique_list = list(dict.fromkeys(v))
        if len(unique_list) != len(v):
            raise ValueError("报价单号列表中存在重复项")
        # 验证每个元素
        for item in unique_list:
            if not re.match(r"^[A-Z0-9_-]+$", item):
                raise ValueError(f"报价单号格式错误: {item}")
        return unique_list
```

### 1.3 限流配置

```yaml
# config/settings.yaml
rate_limit:
  default: "100/minute"
  generate: "20/minute"
  batch: "5/minute"
  by_ip: true
  whitelist:
    - "127.0.0.1"
    - "10.0.0.0/8"
```

---

## 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 状态 |
|------|------|----------|--------|------|
| 6.1 | FastAPI 应用初始化 | `src/main.py` | FastAPI 应用 | ✅ 已确认 |
| 6.2 | 请求/响应模型 | `src/api/schemas.py` | Pydantic 模型 | ✅ 已确认 |
| 6.3 | 健康检查接口 | `src/api/routes/health.py` | /health 端点 | ✅ 已确认 |
| 6.4 | 模板列表查询接口 | `src/api/routes/templates.py` | /templates 端点 | ✅ 已确认 |
| 6.5 | 单文件生成接口 | `src/api/routes/generate.py` | /generate 端点 | ✅ 已确认 |
| 6.6 | 批量生成接口 | `src/api/routes/batch.py` | /batch 端点 | ✅ 已确认 |
| 6.7 | 文件下载处理 | `src/api/dependencies/file.py` | 文件响应处理 | ✅ 已确认 |
| 6.8 | 异步任务处理 | `src/api/tasks/manager.py` | 异步任务管理 | ✅ 已确认 |
| 6.9 | API 路由注册 | `src/api/router.py` | 路由聚合 | ✅ 已确认 |
| 6.10 | API 中间件 | `src/api/middleware/*.py` | 中间件 | ✅ 已确认 |

---

## 待讨论问题

### 6.1 FastAPI 应用初始化

**当前计划**: `src/main.py`

**讨论点**:
- 是否需要拆分应用工厂模式？
- 是否需要多环境配置（dev/prod）？

---

### 6.2 请求/响应模型 ✅ 已更新

**统一响应格式**：
```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    success: bool
    data: Optional[T] = None
    error: Optional["ErrorDetail"] = None
    message: Optional[str] = None
    request_id: Optional[str] = None  # 用于日志追踪

class ErrorCode(str, Enum):
    """错误码体系"""
    VALIDATION_ERROR = "VALIDATION_ERROR"           # 参数验证错误
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"           # 报价单不存在
    TEMPLATE_NOT_MATCHED = "TEMPLATE_NOT_MATCHED" # 无匹配模板
    GENERATION_FAILED = "GENERATION_FAILED"       # 生成失败
    TASK_NOT_FOUND = "TASK_NOT_FOUND"              # 任务不存在
    TASK_CANCELLED = "TASK_CANCELLED"             # 任务已取消
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"  # 限流
    UNAUTHORIZED = "UNAUTHORIZED"                 # 未授权
    INTERNAL_ERROR = "INTERNAL_ERROR"             # 内部错误

class ErrorDetail(BaseModel):
    """错误详情"""
    code: ErrorCode
    message: str
    details: Optional[dict] = None
```

---

### 6.3 健康检查接口 ✅ 已确认

**接口设计**：

```python
# GET /health
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-03-10T12:00:00Z",
    "services": {
      "database": "connected",
      "oracle": "connected"
    }
  }
}
```

**检查项**：
1. **数据库连接** - 检查 Oracle 连接池可用
2. **模板文件** - 检查模板目录是否存在
3. **配置加载** - 检查必要配置是否加载成功

---

### 6.4 模板列表查询接口 ✅ 已确认

**接口设计**：

```python
# GET /api/v1/templates
# GET /api/v1/templates?category=集采产品
```

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | str | 否 | 分类筛选 |

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": "模板3.1",
      "name": "通用生化（肾功和心肌酶）产品价格-集采中标价",
      "category": "集采产品",
      "file": "templates/模板3.1.docx",
      "match_conditions": {
        "产品细分": "通用生化试剂"
      }
    }
  ]
}
```

**分类列表**：
- 集采产品
- 酶免胶体金
- 通用生化
- 外购试剂

---

### 6.5 单文件生成接口 ✅ 已确认

**接口设计**：

```python
# POST /api/v1/generate
# Header: Authorization: Bearer <api_key>
# Content-Type: application/json
```

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| wybs | str | 是 | 报价单号 (1-50位, 字母数字_-) |

**响应格式**：
- 采用 **同步处理**
- 统一返回 **JSON Base64**

**成功响应**：
```json
{
  "success": true,
  "data": {
    "filename": "报价单_20240301_模板1.docx",
    "file_base64": "UEsDBBQABgA...",
    "templates_used": ["模板1", "模板2"]
  },
  "request_id": "req_abc123"
}
```

**失败响应**：
```json
{
  "success": false,
  "error": {
    "code": "QUOTE_NOT_FOUND",
    "message": "报价单不存在",
    "details": {"wybs": "20240301001"}
  },
  "request_id": "req_abc123"
}
```

---

### 6.6 批量生成接口 ✅ 已确认

**接口设计**：

```python
# POST /api/v1/batch
# Header: Authorization: Bearer <api_key>
# Content-Type: application/json
```

**请求参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| wybs_list | List[str] | 是 | 报价单号列表（1-100个，自动去重） |
| async | bool | 否 | 是否异步处理（默认false） |

**响应格式**：

**同步模式**（推荐用于少量，<10个）：
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "results": [
      {
        "wybs": "20240301001",
        "files": [
          {"filename": "报价单_20240301_模板1.docx", "base64": "..."}
        ],
        "success": true,
        "error": null
      }
    ],
    "zip_base64": "UEsDBBQABgA..."
  },
  "request_id": "req_abc123"
}
```

**异步模式**（用于大量，>=10个）：
```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "status": "pending",
    "estimated_time": 60
  },
  "request_id": "req_abc123"
}
```

**异步任务状态查询**：
```python
# GET /api/v1/tasks/{task_id}
# Header: Authorization: Bearer <api_key>
```

---

### 6.7 文件下载处理 ✅ 已确认

**方案**：
- 不存储文件到磁盘，直接返回 Base64
- 前端负责下载和保存
- 临时文件存储在 `/tmp/price_attachments/`，定时清理

**大文件处理**：
- 单个文件 > 10MB，采用分块传输
- 配置最大文件大小：50MB

---

### 6.8 异步任务处理 ✅ 已确认

**方案**：内存队列（开发）→ Redis + Celery（生产）

```python
# 任务状态
class TaskStatus(str, Enum):
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消
```

**任务超时**：
- 默认超时时间：30分钟
- 可通过配置调整：`task_timeout: 1800`

**任务管理**：

| 接口 | 方法 | 说明 |
|------|------|------|
| 创建任务 | POST /api/v1/batch?async=true | 返回 task_id |
| 查询状态 | GET /api/v1/tasks/{task_id} | 返回任务状态和结果 |
| 取消任务 | DELETE /api/v1/tasks/{task_id} | 取消进行中的任务 |

**状态查询响应**：
```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "status": "processing",
    "progress": 50,
    "total": 10,
    "processed": 5,
    "failed": 0,
    "created_at": "2026-03-10T12:00:00Z",
    "completed_at": null,
    "results": []  // 完成后返回结果
  },
  "request_id": "req_abc123"
}
```

**生产环境方案**：
- 任务状态存储：Redis
- 任务结果存储：文件系统或 Redis
- 队列：Redis Queue 或 Celery

---

### 6.9 API 路由注册 ✅ 已确认

**路由结构**：

```python
# src/api/router.py
from fastapi import APIRouter
from src.api.routes import health, templates, generate, batch, tasks

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(templates.router, tags=["templates"])
api_router.include_router(generate.router, tags=["generate"])
api_router.include_router(batch.router, tags=["batch"])
api_router.include_router(tasks.router, tags=["tasks"])
```

**路由列表**：

| 路由 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/templates` | GET | 模板列表 |
| `/api/v1/generate` | POST | 单文件生成 |
| `/api/v1/batch` | POST | 批量生成 |
| `/api/v1/tasks/{task_id}` | GET/DELETE | 任务管理 |

---

### 6.10 API 中间件 ✅ 已确认

**中间件列表**：

| 中间件 | 文件 | 说明 |
|--------|------|------|
| 认证 | `src/api/middleware/auth.py` | API Key 认证 |
| CORS | `src/api/middleware/cors.py` | 跨域资源共享 |
| 日志 | `src/api/middleware/logging.py` | 请求日志 |
| 错误处理 | `src/api/middleware/error_handler.py` | 统一异常处理 |
| 请求限流 | `src/api/middleware/rate_limit.py` | 限流保护 |

**错误处理响应格式**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "报价单号格式错误",
    "details": {
      "field": "wybs",
      "reason": "只能包含字母、数字、下划线和连字符"
    }
  },
  "request_id": "req_abc123"
}
```

**HTTP 状态码映射**：

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 200 | - | 成功 |
| 400 | VALIDATION_ERROR | 参数验证错误 |
| 401 | UNAUTHORIZED | 未授权 |
| 404 | QUOTE_NOT_FOUND / TASK_NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMIT_EXCEEDED | 限流 |
| 500 | INTERNAL_ERROR | 内部错误 |

---

## API 总结

### 完整接口列表

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/v1/templates` | GET | 模板列表（支持category筛选） |
| `/api/v1/generate` | POST | 单文件生成（同步，返回Base64） |
| `/api/v1/batch` | POST | 批量生成（支持async参数） |
| `/api/v1/tasks/{task_id}` | GET | 任务状态查询 |
| `/api/v1/tasks/{task_id}` | DELETE | 任务取消 |

### 响应格式

```python
# 成功响应
ApiResponse[T](success=True, data=T, message="操作成功")

# 失败响应
ApiResponse[T](success=False, error=ErrorDetail(code="...", message="..."))
```

---

*讨论完成时间：2026-03-10*
