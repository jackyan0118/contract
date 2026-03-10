"""请求日志中间件."""

import time
import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger("api.middleware.logging")

# 请求 ID 上下文变量
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """获取当前请求的 ID"""
    return request_id_var.get()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        # 生成请求 ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request_id_var.set(request_id)

        # 记录请求开始
        start_time = time.time()

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
            )
            raise

        # 记录请求完成
        duration = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration, 2),
            },
        )

        # 添加请求 ID 到响应头
        response.headers["X-Request-ID"] = request_id

        return response


def setup_logging(app: FastAPI) -> None:
    """配置日志中间件"""
    app.add_middleware(RequestLoggingMiddleware)
