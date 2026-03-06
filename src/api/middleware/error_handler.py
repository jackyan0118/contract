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
