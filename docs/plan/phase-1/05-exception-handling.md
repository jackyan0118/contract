# 05. 异常处理体系设计

## 设计目标

建立统一的异常处理体系，定义清晰的异常层次结构，提供友好的错误响应，便于问题定位和用户理解。

## 异常层次结构

```
Exception
    └── AppException (应用基础异常)
        ├── ConfigException (配置异常)
        │   ├── ConfigNotFoundError
        │   └── ConfigValidationError
        ├── DatabaseException (数据库异常)
        │   ├── ConnectionException
        │   ├── QueryException
        │   └── PoolExhaustedException
        ├── TemplateException (模板异常)
        │   ├── TemplateNotFoundError
        │   ├── MatchException
        │   └── RuleParseException
        ├── DocumentException (文档异常)
        │   ├── DocumentGenerateException
        │   └── FileWriteException
        └── APIException (API 异常)
            ├── ValidationError
            ├── NotFoundException
            ├── ServiceException
            └── ExternalServiceException
```

## 代码实现

### src/exceptions/__init__.py

```python
"""异常处理模块 - 统一的异常层次结构."""

from .base import AppException, ErrorCode
from .config import ConfigException, ConfigNotFoundError, ConfigValidationError
from .database import (
    DatabaseException,
    ConnectionException,
    QueryException,
    PoolExhaustedException,
)
from .template import (
    TemplateException,
    TemplateNotFoundError,
    MatchException,
    RuleParseException,
)
from .document import (
    DocumentException,
    DocumentGenerateException,
    FileWriteException,
)
from .api import (
    APIException,
    ValidationError,
    NotFoundException,
    ServiceException,
    ExternalServiceException,
)

__all__ = [
    # 基础异常
    "AppException",
    "ErrorCode",
    # 配置异常
    "ConfigException",
    "ConfigNotFoundError",
    "ConfigValidationError",
    # 数据库异常
    "DatabaseException",
    "ConnectionException",
    "QueryException",
    "PoolExhaustedException",
    # 模板异常
    "TemplateException",
    "TemplateNotFoundError",
    "MatchException",
    "RuleParseException",
    # 文档异常
    "DocumentException",
    "DocumentGenerateException",
    "FileWriteException",
    # API 异常
    "APIException",
    "ValidationError",
    "NotFoundException",
    "ServiceException",
    "ExternalServiceException",
]
```

### src/exceptions/base.py

```python
"""基础异常类定义."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(str, Enum):
    """错误代码枚举."""

    # 通用错误 (1000-1999)
    SUCCESS = "0"
    UNKNOWN_ERROR = "1000"
    VALIDATION_ERROR = "1001"
    NOT_FOUND = "1002"
    PERMISSION_DENIED = "1003"

    # 配置错误 (2000-2999)
    CONFIG_ERROR = "2000"
    CONFIG_NOT_FOUND = "2001"
    CONFIG_VALIDATION_ERROR = "2002"

    # 数据库错误 (3000-3999)
    DATABASE_ERROR = "3000"
    CONNECTION_ERROR = "3001"
    QUERY_ERROR = "3002"
    POOL_EXHAUSTED = "3003"

    # 模板错误 (4000-4999)
    TEMPLATE_ERROR = "4000"
    TEMPLATE_NOT_FOUND = "4001"
    MATCH_ERROR = "4002"
    RULE_PARSE_ERROR = "4003"

    # 文档错误 (5000-5999)
    DOCUMENT_ERROR = "5000"
    DOCUMENT_GENERATE_ERROR = "5001"
    FILE_WRITE_ERROR = "5002"

    # 服务错误 (6000-6999)
    SERVICE_ERROR = "6000"
    EXTERNAL_SERVICE_ERROR = "6001"


@dataclass
class ErrorDetail:
    """错误详情."""

    code: ErrorCode
    message: str
    detail: Optional[Dict[str, Any]] = None


class AppException(Exception):
    """应用基础异常类."""

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
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "detail": self.detail,
        }

    def to_error_detail(self) -> ErrorDetail:
        """转换为 ErrorDetail 对象."""
        return ErrorDetail(
            code=self.error_code,
            message=self.message,
            detail=self.detail,
        )
```

### src/exceptions/config.py

```python
"""配置相关异常."""

from .base import AppException, ErrorCode


class ConfigException(AppException):
    """配置异常基类."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIG_ERROR, **kwargs)


class ConfigNotFoundError(ConfigException):
    """配置未找到."""

    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"配置项未找到：{key}",
            error_code=ErrorCode.CONFIG_NOT_FOUND,
            detail={"key": key, **kwargs.get("detail", {})},
            **kwargs,
        )


class ConfigValidationError(ConfigException):
    """配置验证失败."""

    def __init__(self, key: str, reason: str, **kwargs):
        super().__init__(
            message=f"配置验证失败：{key} - {reason}",
            error_code=ErrorCode.CONFIG_VALIDATION_ERROR,
            detail={"key": key, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )
```

### src/exceptions/database.py

```python
"""数据库相关异常."""

from .base import AppException, ErrorCode


class DatabaseException(AppException):
    """数据库异常基类."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_ERROR, **kwargs)


class ConnectionException(DatabaseException):
    """数据库连接异常."""

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            message=f"数据库连接失败：{reason}",
            error_code=ErrorCode.CONNECTION_ERROR,
            detail={"reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )


class QueryException(DatabaseException):
    """数据库查询异常."""

    def __init__(self, query: str, reason: str, **kwargs):
        # SQL 脱敏处理，防止敏感数据泄露
        sanitized_query = self._sanitize_query(query)
        super().__init__(
            message=f"数据库查询失败：{reason}",
            error_code=ErrorCode.QUERY_ERROR,
            detail={"query": sanitized_query, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """脱敏 SQL 查询中的敏感信息."""
        import re
        # 移除字符串字面量，防止泄露敏感数据
        return re.sub(r"'[^']*'", "'***'", query)


class PoolExhaustedException(DatabaseException):
    """连接池耗尽异常."""

    def __init__(self, **kwargs):
        super().__init__(
            message="数据库连接池已耗尽，请稍后重试",
            error_code=ErrorCode.POOL_EXHAUSTED,
            **kwargs,
        )
```

### src/exceptions/template.py

```python
"""模板相关异常."""

from .base import AppException, ErrorCode


class TemplateException(AppException):
    """模板异常基类."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.TEMPLATE_ERROR, **kwargs)


class TemplateNotFoundError(TemplateException):
    """模板未找到."""

    def __init__(self, template_name: str, **kwargs):
        super().__init__(
            message=f"模板未找到：{template_name}",
            error_code=ErrorCode.TEMPLATE_NOT_FOUND,
            detail={"template_name": template_name, **kwargs.get("detail", {})},
            **kwargs,
        )


class MatchException(TemplateException):
    """模板匹配失败."""

    def __init__(self, wybs: str, reason: str, **kwargs):
        super().__init__(
            message=f"模板匹配失败：{reason}",
            error_code=ErrorCode.MATCH_ERROR,
            detail={"wybs": wybs, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )


class RuleParseException(TemplateException):
    """规则解析失败."""

    def __init__(self, file_name: str, reason: str, **kwargs):
        super().__init__(
            message=f"规则解析失败：{file_name} - {reason}",
            error_code=ErrorCode.RULE_PARSE_ERROR,
            detail={"file_name": file_name, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )
```

### src/exceptions/document.py

```python
"""文档相关异常."""

from .base import AppException, ErrorCode


class DocumentException(AppException):
    """文档异常基类."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DOCUMENT_ERROR, **kwargs)


class DocumentGenerateException(DocumentException):
    """文档生成失败."""

    def __init__(self, template_name: str, reason: str, **kwargs):
        super().__init__(
            message=f"文档生成失败：{template_name} - {reason}",
            error_code=ErrorCode.DOCUMENT_GENERATE_ERROR,
            detail={"template_name": template_name, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )


class FileWriteException(DocumentException):
    """文件写入失败."""

    def __init__(self, file_path: str, reason: str, **kwargs):
        super().__init__(
            message=f"文件写入失败：{file_path} - {reason}",
            error_code=ErrorCode.FILE_WRITE_ERROR,
            detail={"file_path": file_path, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )
```

### src/exceptions/api.py

```python
"""API 相关异常."""

from .base import AppException, ErrorCode


class APIException(AppException):
    """API 异常基类."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SERVICE_ERROR, **kwargs)


class ValidationError(APIException):
    """请求验证失败."""

    def __init__(self, field: str, reason: str, **kwargs):
        super().__init__(
            message=f"请求验证失败：{field} - {reason}",
            error_code=ErrorCode.VALIDATION_ERROR,
            detail={"field": field, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )


class NotFoundException(APIException):
    """资源未找到."""

    def __init__(self, resource: str, identifier: str, **kwargs):
        super().__init__(
            message=f"{resource}未找到：{identifier}",
            error_code=ErrorCode.NOT_FOUND,
            detail={"resource": resource, "identifier": identifier, **kwargs.get("detail", {})},
            **kwargs,
        )


class ServiceException(APIException):
    """服务内部错误."""

    def __init__(self, service: str, reason: str, **kwargs):
        super().__init__(
            message=f"服务内部错误：{service} - {reason}",
            error_code=ErrorCode.SERVICE_ERROR,
            detail={"service": service, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )


class ExternalServiceException(APIException):
    """外部服务调用失败."""

    def __init__(self, service: str, reason: str, **kwargs):
        super().__init__(
            message=f"外部服务调用失败：{service} - {reason}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            detail={"service": service, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )
```

### src/api/middleware/error_handler.py

```python
"""错误处理中间件."""

from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from src.exceptions.base import AppException, ErrorCode
from src.utils.logger import get_logger

logger = get_logger("api.error")


async def error_handler_middleware(
    request: Request,
    call_next: Callable,
) -> Response:
    """错误处理中间件."""
    try:
        return await call_next(request)
    except AppException as e:
        # 业务异常
        logger.error(f"业务异常：{e.message}", exc_info=False)
        return JSONResponse(
            status_code=_get_status_code(e.error_code),
            content={
                "error": True,
                "error_code": e.error_code.value,
                "message": e.message,
                "detail": e.detail,
            },
        )
    except Exception as e:
        # 未预期的异常
        logger.error(f"未预期的异常：{str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "error_code": "1000",
                "message": "服务器内部错误",
                "detail": "请稍后重试或联系技术支持",
            },
        )


def _get_status_code(error_code: ErrorCode) -> int:
    """根据错误代码返回 HTTP 状态码."""
    status_map = {
        ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCode.PERMISSION_DENIED: status.HTTP_403_FORBIDDEN,
        ErrorCode.CONFIG_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.TEMPLATE_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.DOCUMENT_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.SERVICE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return status_map.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## 异常使用示例

```python
from src.exceptions import (
    TemplateNotFoundError,
    MatchException,
    ConnectionException,
    NotFoundException,
)

# 抛出模板未找到异常
raise TemplateNotFoundError(template_name="模板 1：酶免和胶体金")

# 抛出匹配失败异常
raise MatchException(
    wybs="QTD20260306001",
    reason="未找到匹配的模板规则"
)

# 抛出数据库连接异常
raise ConnectionException(reason="连接超时")

# 捕获并转换异常
try:
    result = database.query(sql)
except Exception as e:
    raise QueryException(query=sql, reason=str(e), cause=e)
```

## API 响应格式

### 成功响应
```json
{
  "error": false,
  "data": {...}
}
```

### 错误响应
```json
{
  "error": true,
  "error_code": "4001",
  "message": "模板未找到：模板 1",
  "detail": {
    "template_name": "模板 1：酶免和胶体金"
  }
}
```

## 验收标准

- [ ] 异常层次结构清晰
- [ ] 所有异常继承自 AppException
- [ ] 错误代码枚举完整
- [ ] 错误处理中间件正常工作
- [ ] API 错误响应格式统一
- [ ] 日志记录异常信息完整

---

*文档版本：1.0*
*创建日期：2026-03-06*
