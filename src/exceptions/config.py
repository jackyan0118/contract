"""配置相关异常."""

from .base import AppException, ErrorCode


class ConfigException(AppException):
    """配置异常基类."""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.CONFIG_ERROR, **kwargs):
        super().__init__(message, error_code=error_code, **kwargs)


class ConfigNotFoundError(ConfigException):
    """配置未找到."""

    def __init__(self, key: str, **kwargs):
        detail = {"key": key, **kwargs.get("detail", {})}
        super().__init__(
            message=f"配置项未找到：{key}",
            error_code=ErrorCode.CONFIG_NOT_FOUND,
            detail=detail,
        )


class ConfigValidationError(ConfigException):
    """配置验证失败."""

    def __init__(self, key: str, reason: str, **kwargs):
        detail = {"key": key, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"配置验证失败：{key} - {reason}",
            error_code=ErrorCode.CONFIG_VALIDATION_ERROR,
            detail=detail,
        )
