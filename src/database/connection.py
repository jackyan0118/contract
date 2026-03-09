"""数据库连接池管理器."""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from typing import Generator, Optional

import oracledb

from src.database.config import get_database_config
from src.exceptions import ConnectionException, PoolExhaustedException
from src.utils.logger import get_logger

logger = get_logger("database.connection")


class ConnectionPool:
    """Oracle 数据库连接池管理器.

    提供连接池的初始化、获取、释放和关闭功能。
    支持懒加载、线程安全、重试机制。
    """

    def __init__(self) -> None:
        """初始化连接池管理器."""
        self._pool: Optional[oracledb.ConnectionPool] = None
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        """初始化连接池.

        根据配置创建 Oracle 连接池。
        使用双重检查锁定确保线程安全。
        """
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            try:
                db_config = get_database_config()
                params = db_config.to_oracledb_params()

                # 根据 CPU 核心数自动计算最大连接数
                cpu_count = os.cpu_count() or 4
                max_conn = max(db_config.max_connections, cpu_count * 2)

                self._pool = oracledb.create_pool(
                    **params,
                    min=db_config.min_connections,
                    max=max_conn,
                    increment=db_config.pool_increment,
                    timeout=db_config.connect_timeout,
                    wait_timeout=db_config.command_timeout * 1000,
                    getmode=oracledb.POOL_GETMODE_WAIT,
                    max_lifetime=db_config.max_lifetime,
                )
                self._initialized = True
                logger.info(
                    "数据库连接池初始化成功",
                    extra={
                        "min_connections": db_config.min_connections,
                        "max_connections": max_conn,
                    },
                )
            except oracledb.Error:
                logger.error("数据库连接池初始化失败")
                raise ConnectionException(reason="数据库连接池初始化失败")

    def get_connection(self, retry: bool = True) -> oracledb.Connection:
        """获取数据库连接（带重试机制，自动初始化）.

        Args:
            retry: 是否启用重试机制

        Returns:
            Oracle 数据库连接对象

        Raises:
            PoolExhaustedException: 获取连接失败且重试耗尽
        """
        # 自动初始化（懒加载，线程安全）
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self.initialize()

        db_config = get_database_config()
        attempts = db_config.retry_attempts if retry else 1

        last_error = None
        for attempt in range(attempts):
            try:
                conn = self._pool.acquire()
                logger.debug("获取数据库连接成功")
                return conn
            except oracledb.Error as e:
                last_error = e
                if attempt < attempts - 1:
                    delay = db_config.retry_delay * (2**attempt)  # 指数退避
                    logger.warning(
                        "获取连接失败，将重试",
                        extra={
                            "attempt": attempt + 1,
                            "total": attempts,
                            "delay_seconds": delay,
                        },
                    )
                    time.sleep(delay)
                else:
                    logger.error("获取数据库连接失败，已重试多次")

        raise PoolExhaustedException(detail={"reason": "获取连接失败"})

    def release_connection(self, conn: oracledb.Connection) -> None:
        """释放数据库连接.

        Args:
            conn: 要释放的数据库连接
        """
        if conn and self._pool:
            try:
                self._pool.release(conn)
                logger.debug("释放数据库连接成功")
            except oracledb.Error:
                logger.warning("释放数据库连接失败")

    @contextmanager
    def connection(self) -> Generator[oracledb.Connection, None, None]:
        """上下文管理器，获取连接自动释放.

        Yields:
            Oracle 数据库连接对象

        Example:
            >>> with pool.connection() as conn:
            ...     with conn.cursor() as cursor:
            ...         cursor.execute("SELECT 1 FROM DUAL")
        """
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        finally:
            if conn:
                self.release_connection(conn)

    def close(self) -> None:
        """关闭连接池.

        关闭所有连接并释放资源。
        """
        if self._pool:
            try:
                self._pool.close()
                logger.info("数据库连接池已关闭")
            except oracledb.Error:
                logger.warning("关闭数据库连接池失败")
            finally:
                self._pool = None
                self._initialized = False

    def is_healthy(self) -> bool:
        """检查连接池健康状态.

        Returns:
            连接池是否健康
        """
        if not self._initialized or not self._pool:
            return False

        try:
            with self.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1 FROM DUAL")
                    cursor.fetchone()
            return True
        except Exception:
            return False


# 全局连接池实例
_connection_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool() -> ConnectionPool:
    """获取全局连接池实例（单例模式）.

    Returns:
        ConnectionPool 实例
    """
    global _connection_pool

    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool()

    return _connection_pool
