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


class ZipPackException(DocumentException):
    """ZIP打包失败."""

    def __init__(self, reason: str, file_paths: list = None, **kwargs):
        detail = {"reason": reason, "file_paths": file_paths or [], **kwargs.get("detail", {})}
        super().__init__(
            message=f"ZIP打包失败：{reason}",
            error_code=ErrorCode.ZIP_PACK_ERROR,
            detail=detail,
        )


class DiskSpaceException(DocumentException):
    """磁盘空间不足."""

    def __init__(self, required_mb: float, available_mb: float, threshold: int = 80, **kwargs):
        detail = {
            "required_mb": required_mb,
            "available_mb": available_mb,
            "threshold": threshold,
            **kwargs.get("detail", {})
        }
        super().__init__(
            message=f"磁盘空间不足：需要 {required_mb:.1f}MB，可用 {available_mb:.1f}MB",
            error_code=ErrorCode.DISK_SPACE_ERROR,
            detail=detail,
        )
