"""错误处理中间件."""

from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.exceptions.base import AppException, ErrorCode
from src.utils.logger import get_logger

logger = get_logger("api.error")


def setup_error_handler(app: FastAPI) -> None:
    """配置错误处理中间件"""
    app.add_middleware(ErrorHandlerMiddleware)


async def error_handler_middleware(
    request: Request,
    call_next: Callable,
) -> Response:
    """错误处理中间件."""
    try:
        return await call_next(request)
    except AppException as e:
        # 业务异常：只记录脱敏后的信息
        logger.error(
            f"业务异常: {e.error_code.value}",
            extra={"error_code": e.error_code.value},
            exc_info=False,
        )
        return JSONResponse(
            status_code=_get_status_code(e.error_code),
            content={
                "success": False,
                "error": {
                    "code": e.error_code.value,
                    "message": e.message,
                    "details": e.detail,
                },
            },
        )
    except Exception as e:
        # 未预期的异常：只记录类型，不记录消息
        logger.error(
            f"未预期的异常: {type(e).__name__}",
            extra={"exception_type": type(e).__name__},
            exc_info=False,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误",
                    "details": None,
                },
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


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except AppException as e:
            logger.error(f"业务异常：{e.message}", exc_info=False)
            return JSONResponse(
                status_code=_get_status_code(e.error_code),
                content={
                    "success": False,
                    "error": {
                        "code": e.error_code.value,
                        "message": e.message,
                        "details": e.detail,
                    },
                },
            )
        except Exception as e:
            logger.error(f"未预期的异常：{str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "服务器内部错误",
                        "details": None,
                    },
                },
            )
