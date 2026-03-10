"""限流中间件."""

import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("api.middleware.rate_limit")


@dataclass
class RateLimitConfig:
    """限流配置"""

    requests: int  # 请求数
    window: int  # 时间窗口（秒）


class RateLimiter:
    """简单的内存限流器"""

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(
        self,
        key: str,
        limit: RateLimitConfig,
        whitelist: list[str],
    ) -> bool:
        """检查请求是否允许"""
        # 检查白名单
        if key in whitelist:
            return True

        now = time.time()
        window_start = now - limit.window

        with self._lock:
            # 清理过期的请求记录
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            # 检查是否超过限制
            if len(self._requests[key]) >= limit.requests:
                return False

            # 记录本次请求
            self._requests[key].append(now)
            return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""

    def __init__(self, app: FastAPI, path_limits: Optional[Dict[str, RateLimitConfig]] = None):
        super().__init__(app)
        self._limiter = RateLimiter()
        self._path_limits = path_limits or {}
        self._default_limit = RateLimitConfig(requests=100, window=60)
        self._load_config()

    def _load_config(self):
        """从配置加载限流规则"""
        settings = get_settings()
        rate_config = settings.rate_limit

        # 解析限流配置
        self._default_limit = self._parse_limit(rate_config.default)
        self._path_limits = {
            "/api/v1/generate": self._parse_limit(rate_config.generate),
            "/api/v1/batch": self._parse_limit(rate_config.batch),
        }
        self._whitelist = rate_config.whitelist or []
        self._by_ip = rate_config.by_ip

    def _parse_limit(self, limit_str: str) -> RateLimitConfig:
        """解析限流字符串，如 "100/minute" """
        parts = limit_str.split("/")
        if len(parts) != 2:
            return RateLimitConfig(requests=100, window=60)

        requests = int(parts[0])
        window_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400,
        }
        window = window_map.get(parts[1], 60)

        return RateLimitConfig(requests=requests, window=window)

    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        settings = get_settings()
        if settings.rate_limit.by_ip:
            # 尝试获取真实 IP（支持代理）
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        return "default"

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查
        if request.url.path == "/health":
            return await call_next(request)

        # 获取限流配置
        limit = self._default_limit
        for path, path_limit in self._path_limits.items():
            if request.url.path.startswith(path):
                limit = path_limit
                break

        # 检查限流
        client_key = self._get_client_key(request)
        if not self._limiter.is_allowed(client_key, limit, self._whitelist):
            logger.warning(f"Rate limit exceeded for {client_key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"请求过于频繁，请稍后再试",
                },
            )

        return await call_next(request)


def setup_rate_limit(app: FastAPI) -> None:
    """配置限流中间件"""
    app.add_middleware(RateLimitMiddleware)
