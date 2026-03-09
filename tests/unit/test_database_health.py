"""数据库健康检查模块测试."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.database.health import HealthChecker, HealthStatus, check_database_health


class TestHealthStatus:
    """HealthStatus 数据类测试类."""

    def test_health_status_creation(self):
        """测试健康状态创建."""
        status = HealthStatus(
            healthy=True,
            message="数据库连接正常",
            response_time_ms=10.5,
            timestamp=datetime.now(),
        )

        assert status.healthy is True
        assert status.message == "数据库连接正常"
        assert status.response_time_ms == 10.5
        assert status.timestamp is not None

    def test_health_status_creation_defaults(self):
        """测试健康状态创建 - 默认值."""
        status = HealthStatus(
            healthy=False,
            message="数据库连接异常",
        )

        assert status.healthy is False
        assert status.message == "数据库连接异常"
        assert status.response_time_ms is None
        assert status.timestamp is None


class TestHealthChecker:
    """HealthChecker 测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        import src.database.health as health_module

        health_module._checker = None

    def test_init(self):
        """测试初始化."""
        checker = HealthChecker(cache_ttl=60)

        assert checker._cache_ttl == 60
        assert checker._last_check_time is None
        assert checker._last_status is None

    def test_check_cache_valid(self):
        """测试缓存有效时返回缓存结果."""
        checker = HealthChecker(cache_ttl=30)
        mock_status = HealthStatus(
            healthy=True,
            message="数据库连接正常",
            response_time_ms=10.0,
            timestamp=datetime.now(),
        )
        checker._last_status = mock_status
        checker._last_check_time = datetime.now()

        result = checker.check(force=False)

        assert result is mock_status

    @patch("src.database.health.get_connection_pool")
    def test_check_force(self, mock_get_pool):
        """测试强制检查."""
        # 创建 mock 状态（过期）
        old_time = datetime.now() - timedelta(seconds=60)
        old_status = HealthStatus(
            healthy=True,
            message="Old status",
            response_time_ms=10.0,
            timestamp=old_time,
        )

        checker = HealthChecker(cache_ttl=30)
        checker._last_status = old_status
        checker._last_check_time = old_time

        # 模拟连接池
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]

        # 使用 context manager 方式
        mock_cursor_cm = MagicMock()
        mock_cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor_cm.__exit__ = MagicMock(return_value=False)

        mock_conn.cursor.return_value = mock_cursor_cm

        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        result = checker.check(force=True)

        assert result.healthy is True
        assert result.message == "数据库连接正常"

    @patch("src.database.health.get_connection_pool")
    def test_check_healthy(self, mock_get_pool):
        """测试健康检查 - 健康."""
        checker = HealthChecker(cache_ttl=30)

        # 模拟连接池
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]

        mock_cursor_cm = MagicMock()
        mock_cursor_cm.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor_cm.__exit__ = MagicMock(return_value=False)

        mock_conn.cursor.return_value = mock_cursor_cm

        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        result = checker.check(force=True)

        assert result.healthy is True
        assert result.message == "数据库连接正常"
        assert result.response_time_ms is not None

    @patch("src.database.health.get_connection_pool")
    def test_check_unhealthy(self, mock_get_pool):
        """测试健康检查 - 不健康."""
        checker = HealthChecker(cache_ttl=30)

        # 模拟连接池抛出异常
        mock_pool = MagicMock()
        mock_pool.connection.side_effect = Exception("Connection failed")
        mock_get_pool.return_value = mock_pool

        result = checker.check(force=True)

        assert result.healthy is False
        assert result.message == "数据库连接异常"

    def test_is_cache_valid_no_cache(self):
        """测试缓存有效性 - 无缓存."""
        checker = HealthChecker(cache_ttl=30)

        result = checker._is_cache_valid()

        assert result is False

    def test_is_cache_valid_expired(self):
        """测试缓存有效性 - 已过期."""
        checker = HealthChecker(cache_ttl=30)

        old_time = datetime.now() - timedelta(seconds=60)
        checker._last_check_time = old_time
        checker._last_status = HealthStatus(
            healthy=True,
            message="Old",
            timestamp=old_time,
        )

        result = checker._is_cache_valid()

        assert result is False

    def test_is_cache_valid_valid(self):
        """测试缓存有效性 - 有效."""
        checker = HealthChecker(cache_ttl=30)

        checker._last_check_time = datetime.now()
        checker._last_status = HealthStatus(
            healthy=True,
            message="Valid",
            timestamp=datetime.now(),
        )

        result = checker._is_cache_valid()

        assert result is True


class TestCheckDatabaseHealth:
    """check_database_health 函数测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        import src.database.health as health_module

        health_module._checker = None

    @patch("src.database.health.HealthChecker")
    def test_check_database_health_singleton(self, mock_checker_class):
        """测试单例模式."""
        mock_checker = MagicMock()
        mock_checker_class.return_value = mock_checker

        check_database_health()
        check_database_health()

        assert mock_checker_class.call_count == 1

    @patch("src.database.health.HealthChecker")
    def test_check_database_health_default(self, mock_checker_class):
        """测试默认参数."""
        mock_checker = MagicMock()
        mock_checker.check.return_value = HealthStatus(
            healthy=True,
            message="OK",
        )
        mock_checker_class.return_value = mock_checker

        result = check_database_health(force=False)

        assert result.healthy is True
        mock_checker.check.assert_called_once_with(force=False)

    @patch("src.database.health.HealthChecker")
    def test_check_database_health_force(self, mock_checker_class):
        """测试强制检查参数."""
        mock_checker = MagicMock()
        mock_checker.check.return_value = HealthStatus(
            healthy=True,
            message="OK",
        )
        mock_checker_class.return_value = mock_checker

        result = check_database_health(force=True)

        assert result.healthy is True
        mock_checker.check.assert_called_once_with(force=True)
