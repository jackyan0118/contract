"""文档相关异常."""

from .base import AppException, ErrorCode


class DocumentException(AppException):
    """文档异常基类."""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.DOCUMENT_ERROR, **kwargs):
        super().__init__(message, error_code=error_code, **kwargs)


class DocumentGenerateException(DocumentException):
    """文档生成失败."""

    def __init__(self, template_name: str, reason: str, **kwargs):
        detail = {"template_name": template_name, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"文档生成失败：{template_name} - {reason}",
            error_code=ErrorCode.DOCUMENT_GENERATE_ERROR,
            detail=detail,
        )


class FileWriteException(DocumentException):
    """文件写入失败."""

    def __init__(self, file_path: str, reason: str, **kwargs):
        detail = {"file_path": file_path, "reason": reason, **kwargs.get("detail", {})}
        super().__init__(
            message=f"文件写入失败：{file_path} - {reason}",
            error_code=ErrorCode.FILE_WRITE_ERROR,
            detail=detail,
        )
