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
    AuthenticationError,
    RateLimitError,
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
    "AuthenticationError",
    "RateLimitError",
]
