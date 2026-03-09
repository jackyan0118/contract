"""数据库相关异常."""

import re
from .base import AppException, ErrorCode


class DatabaseException(AppException):
    """数据库异常基类."""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DATABASE_ERROR, **kwargs):
        super().__init__(message, error_code=error_code, **kwargs)


class ConnectionException(DatabaseException):
    """数据库连接异常."""

    def __init__(self, reason: str, **kwargs):
        detail = {"reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"数据库连接失败：{reason}",
            error_code=ErrorCode.CONNECTION_ERROR,
            detail=detail,
        )


class QueryException(DatabaseException):
    """数据库查询异常."""

    def __init__(self, query: str, reason: str, **kwargs):
        # SQL 脱敏处理，防止敏感数据泄露
        sanitized_query = self._sanitize_query(query)
        detail = {"query": sanitized_query, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"数据库查询失败：{reason}",
            error_code=ErrorCode.QUERY_ERROR,
            detail=detail,
        )

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """脱敏 SQL 查询中的敏感信息."""
        # 移除字符串字面量，防止泄露敏感数据
        return re.sub(r"'[^']*'", "'***'", query)


class PoolExhaustedException(DatabaseException):
    """连接池耗尽异常."""

    def __init__(self, **kwargs):
        super().__init__(
            message="数据库连接池已耗尽，请稍后重试",
            error_code=ErrorCode.POOL_EXHAUSTED,
        )
