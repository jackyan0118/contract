"""数据库健康检查模块."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from src.database.connection import get_connection_pool
from src.utils.logger import get_logger

logger = get_logger("database.health")


@dataclass
class HealthStatus:
    """健康检查状态."""

    healthy: bool
    message: str
    response_time_ms: Optional[float] = None
    timestamp: Optional[datetime] = None


class HealthChecker:
    """数据库健康检查器（线程安全）.

    提供带缓存的健康检查功能，避免频繁查询数据库。
    """

    def __init__(self, cache_ttl: int = 30) -> None:
        """初始化健康检查器.

        Args:
            cache_ttl: 缓存有效期（秒），避免频繁查询数据库
        """
        self._cache_ttl = cache_ttl
        self._last_check_time: Optional[datetime] = None
        self._last_status: Optional[HealthStatus] = None
        self._lock = threading.Lock()

    def check(self, force: bool = False) -> HealthStatus:
        """执行健康检查（带缓存，线程安全）.

        Args:
            force: 是否强制执行检查（忽略缓存）

        Returns:
            HealthStatus 实例
        """
        # 检查缓存是否有效（无需加锁，因为读取是原子的）
        if not force and self._is_cache_valid():
            return self._last_status

        # 加锁保护，避免并发执行
        with self._lock:
            # 双重检查
            if not force and self._is_cache_valid():
                return self._last_status

            start_time = time.time()
            pool = get_connection_pool()

            try:
                with pool.connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1 FROM DUAL")
                        cursor.fetchone()

                response_time = (time.time() - start_time) * 1000

                status = HealthStatus(
                    healthy=True,
                    message="数据库连接正常",
                    response_time_ms=round(response_time, 2),
                    timestamp=datetime.now(),
                )
                logger.info(
                    "数据库健康检查通过",
                    extra={"response_time_ms": response_time},
                )
            except Exception:
                status = HealthStatus(
                    healthy=False,
                    message="数据库连接异常",
                    timestamp=datetime.now(),
                )
                logger.error("数据库健康检查失败")

            self._last_check_time = status.timestamp
            self._last_status = status
            return status

    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效.

        Returns:
            缓存是否有效
        """
        if self._last_status is None or self._last_check_time is None:
            return False
        elapsed = datetime.now() - self._last_check_time
        return elapsed < timedelta(seconds=self._cache_ttl)


# 全局健康检查器
_checker: Optional[HealthChecker] = None
_checker_lock = threading.Lock()


def check_database_health(force: bool = False) -> HealthStatus:
    """执行数据库健康检查（线程安全）.

    Args:
        force: 是否强制执行检查（忽略缓存）

    Returns:
        HealthStatus 实例

    Example:
        >>> health = check_database_health()
        >>> print(f"Database healthy: {health.healthy}")

        >>> # 强制刷新健康检查
        >>> health = check_database_health(force=True)
        >>> print(f"Response time: {health.response_time_ms}ms")
    """
    global _checker
    if _checker is None:
        with _checker_lock:
            if _checker is None:
                _checker = HealthChecker(cache_ttl=30)
    return _checker.check(force=force)
