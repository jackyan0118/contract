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
  "user": "sk_dev_***xxxx",  // API Key 脱敏
  "user_agent": "Mozilla/5.0...",
  "resource": "20240301001",
  "action": "document_generation",
  "result": "success",
  "error_message": null,
  "request_id": "req_abc123",
  "details": {
    "templates_used": ["模板1", "模板2"],
    "file_count": 2,
    "duration_ms": 1500
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | string | ISO 8601 时间戳 |
| event | string | 事件类型 |
| user | string | 用户标识（脱敏后的 API Key） |
| user_agent | string | 客户端标识 |
| resource | string | 关联资源（wybs/报价单号） |
| action | string | 操作类型 |
| result | string | 结果（success/failed） |
| error_message | string | 失败原因 |
| request_id | string | 请求追踪ID |
| details | object | 额外信息 |

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

复用 Phase 6 现有的异常类体系：

```python
# src/exceptions/base.py (已存在，复用)
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

class ErrorCode(str, Enum):
    """错误代码枚举 - 使用数值型错误码"""
    SUCCESS = "0"
    UNKNOWN_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    NOT_FOUND = "1002"
    PERMISSION_DENIED = "1003"
    # ... 其他错误码

class AppException(Exception):
    """应用基础异常类 - 复用现有实现"""
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        detail: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.detail = detail or {}
        self.cause = cause
```

**Phase 7 需要新增的异常类**：

```python
# src/exceptions/api.py - 补充缺失的异常类

class AuthenticationError(APIException):
    """认证错误 - 新增"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            error_code=ErrorCode.PERMISSION_DENIED,
            detail={"type": "authentication"}
        )

class RateLimitError(APIException):
    """限流错误 - 新增"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="请求过于频繁，请稍后重试",
            error_code=ErrorCode.SERVICE_ERROR,
            detail={"retry_after": retry_after, "type": "rate_limit"}
        )
```

### 3.3 异常映射 (复用现有)

| 异常类 | 错误码 | 状态码 |
|--------|--------|--------|
| ValidationError | 1001 | 400 |
| NotFoundError | 1002 | 404 |
| AuthenticationError (新增) | 1003 | 401 |
| RateLimitError (新增) | 6000 | 429 |
| MatchException | 4002 | 400 |
| DocumentGenerateException | 5001 | 500 |
| DatabaseException | 3000 | 500 |

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
        # 优先使用客户端传入的 request_id，否则生成新的
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        # 记录请求开始
        logger.info(
            "API request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
        )

        try:
            response = await call_next(request)
        except Exception as e:
            # 记录异常情况
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "API request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e)
                }
            )
            raise

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

复用 Phase 6 现有实现，使用 `app.add_exception_handler()` 注册：

```python
# src/api/middleware/error_handler.py (复用现有实现)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.exceptions import AppException, ErrorCode

async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理"""
    return JSONResponse(
        status_code=400,  # 根据具体异常类型确定
        content={
            "success": False,
            "error": exc.to_dict(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "error_code": str(exc.status_code),
                "message": exc.detail,
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Pydantic 验证异常处理"""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "error_code": ErrorCode.VALIDATION_ERROR.value,
                "message": "参数验证失败",
                "detail": exc.errors()
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(
        "Unhandled exception occurred",
        exc_info=True,
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "exception_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "error_code": ErrorCode.UNKNOWN_ERROR.value,
                "message": "内部错误，请稍后重试"
            },
            "request_id": getattr(request.state, "request_id", None)
        }
    )
```

---

## 五、任务列表

> **注意**: 部分功能已在 Phase 6 实现，复用现有代码

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 | 状态 |
|------|------|----------|--------|------|------|
| 7.1 | 结构化日志配置 | `src/utils/structured_logger.py` | 日志配置模块 | Phase 6 | ✅ 已实现 |
| 7.2 | 日志轮转配置 | `src/utils/logger.py` | 日志轮转工具 | 7.1 | ✅ 已实现 |
| 7.3 | 异常类定义 | `src/exceptions/*.py` | 异常类层次 | Phase 6 | ✅ 已实现 |
| 7.4 | 错误处理中间件 | `src/api/middleware/error_handler.py` | 错误处理中间件 | 7.3 | ✅ 已实现 |
| 7.5 | 请求日志中间件 | `src/api/middleware/logging.py` | 请求日志中间件 | 7.1 | 待实现 |
| 7.6 | 审计日志服务 | `src/services/audit_logger.py` | 审计日志记录 | 7.1 | 待实现 |
| 7.7 | 日志清理任务 | `src/tasks/log_cleanup.py` | 定时清理任务 | 7.2 | 待实现 |
| 7.8 | 新增认证异常 | `src/exceptions/api.py` | AuthenticationError | 7.3 | 待实现 |
| 7.9 | 新增限流异常 | `src/exceptions/api.py` | RateLimitError | 7.3 | 待实现 |

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

## 八、专家评审反馈（已采纳）

根据专家评审意见，已更新以下内容：

### 8.1 统一错误码体系

- 复用 Phase 6 现有的数值型错误码
- 使用现有的 `AppException` 类结构

### 8.2 完善异常类

- 补充 `AuthenticationError` 和 `RateLimitError`
- 统一使用 `error_code` 和 `detail` 参数

### 8.3 中间件优化

- 优化 request_id 生成逻辑（支持请求头继承）
- 添加异常处理的 try-except
- 增加 user_agent 字段记录

### 8.4 审计日志增强

- 补充 user_agent、error_message、request_id 字段
- 添加 API Key 脱敏说明

---

*文档版本：1.1*
*讨论完成时间：2026-03-10*
*评审完成时间：2026-03-10*
