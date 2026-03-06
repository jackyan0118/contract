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
