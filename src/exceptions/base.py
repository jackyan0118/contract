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
