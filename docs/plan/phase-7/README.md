# Phase 7: 日志与错误处理 - 设计文档

## 概述

完善日志记录和错误处理机制，保障系统可观测性和问题排查能力。

**时间估算**: 2-3 天

**复杂度**: 低

---

## 一、日志设计

### 1.1 日志格式

采用 JSON 结构化日志，便于解析和检索：

```json
{
  "timestamp": "2026-03-10T12:00:00.123Z",
  "level": "INFO",
  "logger": "request",
  "message": "API request completed",
  "request_id": "req_abc123",
  "method": "POST",
  "path": "/api/v1/generate",
  "status_code": 200,
  "duration_ms": 150,
  "client_ip": "10.0.0.1"
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | string | ISO 8601 格式时间戳 |
| level | string | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| logger | string | 日志记录器名称 |
| message | string | 日志消息 |
| request_id | string | 请求追踪ID |
| others | object | 上下文字段 |

### 1.2 日志分类

| 日志类型 | 文件 | 说明 |
|----------|------|------|
| 应用日志 | `logs/app.log` | 应用程序运行日志 |
| 访问日志 | `logs/access.log` | API 请求访问日志 |
| 错误日志 | `logs/error.log` | 错误和异常日志 |
| 审计日志 | `logs/audit.log` | 业务操作审计日志 |

### 1.3 日志级别

| 级别 | 值 | 使用场景 |
|------|-----|----------|
| DEBUG | 10 | 开发调试，SQL 语句，详细的变量值 |
| INFO | 20 | 正常业务流程，关键节点 |
| WARNING | 30 | 可恢复的异常，参数警告 |
| ERROR | 40 | 业务错误，需要关注 |
| CRITICAL | 50 | 系统级重大问题，服务不可用 |

### 1.4 日志保留策略

- **保留周期**: 7 天
- **轮转策略**: 每天轮转一次
- **压缩**: 超过 1MB 的历史日志自动 gzip 压缩
- **清理**: 定时任务每日凌晨清理过期日志

```yaml
# config/settings.yaml
logging:
  level: "INFO"
  format: "json"
  files:
    app: "logs/app.log"
    access: "logs/access.log"
    error: "logs/error.log"
    audit: "logs/audit.log"
  rotation:
    max_bytes: 10485760  # 10MB
    backup_count: 7      # 保留7天
  loggers:
    - name: "app"
      level: "INFO"
      file: "logs/app.log"
    - name: "access"
      level: "INFO"
      file: "logs/access.log"
    - name: "error"
      level: "ERROR"
      file: "logs/error.log"
    - name: "audit"
      level: "INFO"
      file: "logs/audit.log"
```

---

## 二、审计日志设计

### 2.1 审计事件

记录以下业务操作：

| 事件 | 说明 | 字段 |
|------|------|------|
| api_request | API 请求 | method, path, user, result |
| generate | 文档生成 | wybs, template, result |
| batch_generate | 批量生成 | wybs_list, count, result |
| task_create | 任务创建 | task_id, wybs_list |
| task_cancel | 任务取消 | task_id, reason |

### 2.2 审计日志格式

```json
{
  "timestamp": "2026-03-10T12:00:00.123Z",
  "event": "generate",
  "user": "dev_key_001",
  "resource": "20240301001",
  "action": "document_generation",
  "result": "success",
  "details": {
    "templates_used": ["模板1", "模板2"],
    "file_count": 2,
    "duration_ms": 1500
  },
  "request_id": "req_abc123"
}
```

### 2.3 审计日志存储

- **存储位置**: 本地文件 `logs/audit.log`
- **格式**: JSON Lines (每行一个 JSON 对象)
- **保留周期**: 7 天（与应用日志一致）

---

## 三、错误处理设计

### 3.1 错误分类

| 错误类型 | 说明 | HTTP 状态码 |
|----------|------|-------------|
| 业务错误 | 报价单不存在、模板不匹配等 | 4xx |
| 验证错误 | 参数校验失败 | 400 |
| 认证错误 | API Key 无效 | 401 |
| 限流错误 | 请求过于频繁 | 429 |
| 系统错误 | 数据库故障、未知异常 | 500 |

### 3.2 统一错误响应

Phase 6 已定义统一响应格式：

```python
# src/exceptions/base.py
class AppException(Exception):
    """应用基础异常类"""
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict = None,
        status_code: int = 500
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

class ValidationError(AppException):
    """验证错误"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=400
        )

class NotFoundError(AppException):
    """资源不存在错误"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code=ErrorCode.QUOTE_NOT_FOUND,
            message=f"{resource}不存在",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )

class AuthenticationError(AppException):
    """认证错误"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=401
        )

class RateLimitError(AppException):
    """限流错误"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="请求过于频繁，请稍后重试",
            details={"retry_after": retry_after},
            status_code=429
        )
```

### 3.3 异常映射

| 异常类 | 错误码 | 状态码 |
|--------|--------|--------|
| ValidationError | VALIDATION_ERROR | 400 |
| NotFoundError | QUOTE_NOT_FOUND | 404 |
| AuthenticationError | UNAUTHORIZED | 401 |
| RateLimitError | RATE_LIMIT_EXCEEDED | 429 |
| TemplateMatchError | TEMPLATE_NOT_MATCHED | 400 |
| GenerationError | GENERATION_FAILED | 500 |
| DatabaseException | INTERNAL_ERROR | 500 |

---

## 四、中间件设计

### 4.1 请求日志中间件

```python
# src/api/middleware/logging.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start_time = time.time()

        # 记录请求开始
        logger.info(
            "API request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None
            }
        )

        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # 记录请求完成
        logger.info(
            "API request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }
        )

        # 添加 request_id 到响应头
        response.headers["X-Request-ID"] = request_id
        return response
```

### 4.2 错误处理中间件

```python
# src/api/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from src.exceptions import AppException

async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "details": exc.details
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", None)}
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "内部错误，请稍后重试"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

---

## 五、任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 7.1 | 结构化日志配置 | `src/utils/structured_logger.py` | 日志配置模块 | Phase 6 |
| 7.2 | 日志轮转配置 | `src/utils/log_rotation.py` | 日志轮转工具 | 7.1 |
| 7.3 | 请求日志中间件 | `src/api/middleware/logging.py` | 请求日志中间件 | 7.1 |
| 7.4 | 错误处理中间件 | `src/api/middleware/error_handler.py` | 错误处理中间件 | 7.1 |
| 7.5 | 异常类定义 | `src/exceptions/*.py` | 异常类层次 | Phase 6 |
| 7.6 | 审计日志服务 | `src/services/audit_logger.py` | 审计日志记录 | 7.1 |
| 7.7 | 日志清理任务 | `src/tasks/log_cleanup.py` | 定时清理任务 | 7.2 |

---

## 六、文件结构

```
src/
├── api/
│   └── middleware/
│       ├── logging.py          # 请求日志中间件
│       └── error_handler.py   # 错误处理中间件
├── exceptions/
│   ├── __init__.py
│   ├── base.py                 # 基础异常类
│   ├── config.py               # 配置异常
│   ├── database.py             # 数据库异常
│   ├── template.py             # 模板异常
│   └── api.py                  # API 异常
├── services/
│   └── audit_logger.py         # 审计日志服务
├── utils/
│   ├── structured_logger.py    # 结构化日志配置
│   └── log_rotation.py         # 日志轮转工具
└── tasks/
    └── log_cleanup.py          # 日志清理定时任务
```

---

## 七、配置说明

```yaml
# config/settings.yaml
logging:
  level: "INFO"
  format: "json"
  log_dir: "logs"
  files:
    app: "app.log"
    access: "access.log"
    error: "error.log"
    audit: "audit.log"
  rotation:
    max_bytes: 10485760  # 10MB
    backup_count: 7      # 保留7天
  handlers:
    console:
      enabled: true
      level: "INFO"
    file:
      enabled: true
      level: "INFO"
```

---

## 八、风险点

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 日志文件过大 | 低 | 7天自动清理，10MB轮转 |
| 日志写入性能 | 低 | 异步写入，缓冲处理 |
| 磁盘空间不足 | 中 | 监控告警，提前预留空间 |

---

*讨论完成时间：2026-03-10*
