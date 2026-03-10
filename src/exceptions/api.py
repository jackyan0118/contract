"""API 相关异常."""

from .base import AppException, ErrorCode


class APIException(AppException):
    """API 异常基类."""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.SERVICE_ERROR, **kwargs):
        super().__init__(message, error_code=error_code, **kwargs)


class ValidationError(APIException):
    """请求验证失败."""

    def __init__(self, field: str, reason: str, **kwargs):
        detail = {"field": field, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"请求验证失败：{field} - {reason}",
            error_code=ErrorCode.VALIDATION_ERROR,
            detail=detail,
        )


class NotFoundException(APIException):
    """资源未找到."""

    def __init__(self, resource: str, identifier: str, **kwargs):
        detail = {"resource": resource, "identifier": identifier, **kwargs.get("detail", {})}
        super().__init__(
            message=f"{resource}未找到：{identifier}",
            error_code=ErrorCode.NOT_FOUND,
            detail=detail,
        )


class ServiceException(APIException):
    """服务内部错误."""

    def __init__(self, service: str, reason: str, **kwargs):
        detail = {"service": service, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"服务内部错误：{service} - {reason}",
            error_code=ErrorCode.SERVICE_ERROR,
            detail=detail,
        )


class ExternalServiceException(APIException):
    """外部服务调用失败."""

    def __init__(self, service: str, reason: str, **kwargs):
        detail = {"service": service, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"外部服务调用失败：{service} - {reason}",
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            detail=detail,
        )


class AuthenticationError(APIException):
    """认证错误 - API Key 无效或过期"""

    def __init__(self, message: str = "认证失败：无效的 API Key", **kwargs):
        detail = {"type": "authentication", **kwargs.get("detail", {})}
        super().__init__(
            message=message,
            error_code=ErrorCode.PERMISSION_DENIED,
            detail=detail,
        )


class RateLimitError(APIException):
    """限流错误 - 请求过于频繁"""

    def __init__(self, retry_after: int = 60, **kwargs):
        detail = {"type": "rate_limit", "retry_after": retry_after, **kwargs.get("detail", {})}
        super().__init__(
            message=f"请求过于频繁，请 {retry_after} 秒后重试",
            error_code=ErrorCode.SERVICE_ERROR,
            detail=detail,
        )
