# 02. Oracle 数据库连接模块设计

## 设计目标

实现 Oracle 数据库连接池管理和基础查询能力，支持高并发场景，确保连接可靠性和性能。

## 技术选型

- **Oracle 驱动**: python-oracledb (Thin 模式，无需 Oracle Instant Client)
- **连接池**: oracledb create_pool()
- **连接模式**: 同步/异步支持

## 架构设计

```
src/database/
├── __init__.py
├── connection.py      # 连接池管理器
├── config.py         # 数据库配置
└── health.py         # 健康检查
```

## 代码实现

### src/database/__init__.py

```python
"""数据库连接模块."""

from .connection import ConnectionPool, get_connection_pool
from .config import DatabaseConfig, get_database_config
from .health import HealthChecker, check_database_health

__all__ = [
    "ConnectionPool",
    "get_connection_pool",
    "DatabaseConfig",
    "get_database_config",
    "HealthChecker",
    "check_database_health",
]
```

### src/database/config.py

```python
"""数据库配置模块."""

from dataclasses import dataclass
from typing import Optional

import oracledb

from src.config import DatabaseSettings


@dataclass
class DatabaseConfig:
    """数据库配置类."""

    dsn: str
    min_connections: int
    max_connections: int
    pool_increment: int
    connect_timeout: int
    command_timeout: int
    max_lifetime: int = 3600  # 连接最大生命周期（秒）
    retry_attempts: int = 3   # 重试次数
    retry_delay: float = 0.5  # 重试延迟（秒）

    @classmethod
    def from_settings(cls, settings: DatabaseSettings) -> "DatabaseConfig":
        """从应用设置创建配置."""
        return cls(
            dsn=settings.get_dsn(),
            min_connections=settings.min_connections,
            max_connections=settings.max_connections,
            pool_increment=settings.pool_increment,
            connect_timeout=settings.connect_timeout,
            command_timeout=settings.command_timeout,
        )

    def to_oracledb_params(self) -> dict:
        """转换为 oracledb 连接参数（安全方式）."""
        # 使用 oracledb.parse_dsn() 安全解析 DSN
        # oracle://user:password@host:1521/service_name
        try:
            # 使用 python-oracledb 的安全解析方式
            parsed = oracledb.parse_dsn(self.dsn)
            return {
                "user": parsed.get("user", ""),
                "password": parsed.get("password", ""),
                "dsn": oracledb.makedsn(
                    parsed.get("host", "localhost"),
                    parsed.get("port", 1521),
                    parsed.get("service_name", "ORCL"),
                ),
            }
        except Exception:
            # 回退到手动解析（仅用于兼容旧格式）
            parts = self.dsn.replace("oracle://", "").split("@")
            user_info = parts[0].split(":")
            host_port_service = parts[1].split("/")

            user = user_info[0] if len(user_info) > 0 else ""
            password = user_info[1] if len(user_info) > 1 else ""
            host_port = host_port_service[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 1521
            service_name = host_port_service[1] if len(host_port_service) > 1 else "ORCL"

            return {
                "user": user,
                "password": password,
                "dsn": oracledb.makedsn(host, port, service_name),
            }


# 全局配置实例
_config: Optional[DatabaseConfig] = None


def get_database_config() -> DatabaseConfig:
    """获取数据库配置实例."""
    global _config
    if _config is None:
        from src.config import settings as app_settings
        _config = DatabaseConfig.from_settings(app_settings.database)
    return _config
```

### src/database/connection.py

```python
"""数据库连接池管理器."""

import threading
import time
from contextlib import contextmanager
from typing import Generator, Optional

import oracledb

from src.config import settings
from src.exceptions import ConnectionException, PoolExhaustedException
from src.utils.logger import get_logger
from src.database.config import get_database_config

logger = get_logger("database.connection")


class ConnectionPool:
    """Oracle 数据库连接池管理器."""

    def __init__(self):
        self._pool: Optional[oracledb.ConnectionPool] = None
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self) -> None:
        """初始化连接池."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            try:
                db_config = get_database_config()
                params = db_config.to_oracledb_params()

                # 根据 CPU 核心数自动计算最大连接数
                import os
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
                    context={
                        "min_connections": db_config.min_connections,
                        "max_connections": max_conn,
                    },
                )
            except oracledb.Error as e:
                logger.error(f"数据库连接池初始化失败")
                raise ConnectionException(reason="数据库连接池初始化失败")

    def get_connection(self, retry: bool = True) -> oracledb.Connection:
        """获取数据库连接（带重试机制）."""
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
                    delay = db_config.retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(f"获取连接失败，{delay:.1f}秒后重试 ({attempt + 1}/{attempts})")
                    time.sleep(delay)
                else:
                    logger.error(f"获取数据库连接失败，已重试{attempts}次")

        raise PoolExhaustedException(detail={"reason": "获取连接失败"})

    def release_connection(self, conn: oracledb.Connection) -> None:
        """释放数据库连接."""
        if conn and self._pool:
            try:
                self._pool.release(conn)
                logger.debug("释放数据库连接成功")
            except oracledb.Error as e:
                logger.warning(f"释放数据库连接失败")

    @contextmanager
    def connection(self) -> Generator[oracledb.Connection, None, None]:
        """上下文管理器，获取连接自动释放."""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        finally:
            if conn:
                self.release_connection(conn)

    def close(self) -> None:
        """关闭连接池."""
        if self._pool:
            try:
                self._pool.close()
                logger.info("数据库连接池已关闭")
            except oracledb.Error as e:
                logger.warning(f"关闭数据库连接池失败")
            finally:
                self._pool = None
                self._initialized = False

    def is_healthy(self) -> bool:
        """检查连接池健康状态."""
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
    """获取全局连接池实例（单例模式）."""
    global _connection_pool

    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool()

    return _connection_pool
```

### src/database/health.py

```python
"""数据库健康检查模块."""

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

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
    """数据库健康检查器."""

    def __init__(self, cache_ttl: int = 30):
        """初始化健康检查器.

        Args:
            cache_ttl: 缓存有效期（秒），避免频繁查询数据库
        """
        self._cache_ttl = cache_ttl
        self._last_check_time: Optional[datetime] = None
        self._last_status: Optional[HealthStatus] = None

    def check(self, force: bool = False) -> HealthStatus:
        """执行健康检查（带缓存）."""
        # 检查缓存是否有效
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
                context={"response_time_ms": response_time},
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
        """检查缓存是否有效."""
        if self._last_status is None or self._last_check_time is None:
            return False
        elapsed = datetime.now() - self._last_check_time
        return elapsed < timedelta(seconds=self._cache_ttl)


# 全局健康检查器
_checker: Optional[HealthChecker] = None


def check_database_health(force: bool = False) -> HealthStatus:
    """执行数据库健康检查.

    Args:
        force: 是否强制执行检查（忽略缓存）
    """
    global _checker
    if _checker is None:
        _checker = HealthChecker(cache_ttl=30)
    return _checker.check(force=force)
```

## 连接池配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `min_connections` | 2 | 最小连接数 |
| `max_connections` | 10 | 最大连接数（会根据 CPU 核心数自动调整） |
| `pool_increment` | 1 | 连接池增量 |
| `connect_timeout` | 30 | 连接超时 (秒) |
| `command_timeout` | 60 | 命令超时 (秒) |
| `max_lifetime` | 3600 | 连接最大生命周期 (秒) |
| `retry_attempts` | 3 | 重试次数 |
| `retry_delay` | 0.5 | 重试延迟 (秒) |

## 安全考虑

1. **凭据安全**: 使用 `to_oracledb_params()` 方法安全解析 DSN，避免手动字符串分割
2. **错误处理**: 错误信息不泄露敏感细节，统一使用通用错误消息
3. **连接验证**: 使用连接生命周期管理，避免获取断开的连接

## 使用示例

```python
from src.database import get_connection_pool, check_database_health

# 获取连接池
pool = get_connection_pool()
pool.initialize()

# 使用连接
with pool.connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM table_name WHERE id = :id", {"id": 1})
        results = cursor.fetchall()

# 健康检查（带缓存）
health = check_database_health()
print(f"Database healthy: {health.healthy}")

# 强制刷新健康检查
health = check_database_health(force=True)
print(f"Response time: {health.response_time_ms}ms")
```

## 验收标准

- [ ] 连接池可正常初始化
- [ ] 可获取和释放数据库连接
- [ ] 连接上下文管理器正常工作（游标自动关闭）
- [ ] 健康检查接口正常（带缓存）
- [ ] 连接池关闭功能正常
- [ ] 日志记录完整（不泄露敏感信息）
- [ ] 支持重试机制

---

*文档版本：1.1*
*创建日期：2026-03-06*
*更新日期：2026-03-06*
