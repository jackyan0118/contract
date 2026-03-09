"""数据库连接池模块测试."""

from unittest.mock import MagicMock, patch

import pytest

from src.database.connection import ConnectionPool, get_connection_pool
from src.database import config as db_config_module
from src.exceptions import ConnectionException, PoolExhaustedException


class TestConnectionPool:
    """ConnectionPool 测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        # 重置全局连接池
        db_config_module._config = None
        db_config_module._config_lock = MagicMock()
        import src.database.connection as conn_module

        conn_module._connection_pool = None
        conn_module._pool_lock = MagicMock()

    @patch("src.database.connection.oracledb")
    @patch("src.database.connection.get_database_config")
    def test_initialize(self, mock_get_config, mock_oracledb):
        """测试连接池初始化."""
        # 模拟配置
        mock_config = MagicMock()
        mock_config.to_oracledb_params.return_value = {
            "user": "test",
            "password": "test",
            "dsn": "localhost:1521/orcl",
        }
        mock_config.min_connections = 2
        mock_config.max_connections = 10
        mock_config.pool_increment = 1
        mock_config.connect_timeout = 30
        mock_config.command_timeout = 60000
        mock_config.max_lifetime = 3600
        mock_get_config.return_value = mock_config

        # 模拟 oracledb.create_pool
        mock_pool = MagicMock()
        mock_oracledb.create_pool.return_value = mock_pool
        mock_oracledb.POOL_GETMODE_WAIT = 1

        pool = ConnectionPool()
        pool.initialize()

        assert pool._initialized is True
        mock_oracledb.create_pool.assert_called_once()

    @patch("src.database.connection.oracledb")
    @patch("src.database.connection.get_database_config")
    def test_initialize_already_initialized(self, mock_get_config, mock_oracledb):
        """测试重复初始化."""
        mock_config = MagicMock()
        mock_config.to_oracledb_params.return_value = {"user": "test", "password": "test", "dsn": "localhost:1521/orcl"}
        mock_config.min_connections = 2
        mock_config.max_connections = 10
        mock_config.pool_increment = 1
        mock_config.connect_timeout = 30
        mock_config.command_timeout = 60000
        mock_config.max_lifetime = 3600
        mock_get_config.return_value = mock_config

        mock_pool = MagicMock()
        mock_oracledb.create_pool.return_value = mock_pool
        mock_oracledb.POOL_GETMODE_WAIT = 1

        pool = ConnectionPool()
        pool._initialized = True

        pool.initialize()

        mock_oracledb.create_pool.assert_not_called()

    @patch("src.database.connection.oracledb")
    @patch("src.database.connection.get_database_config")
    def test_initialize_failure(self, mock_get_config, mock_oracledb):
        """测试初始化失败."""
        mock_config = MagicMock()
        mock_config.to_oracledb_params.return_value = {"user": "test", "password": "test", "dsn": "localhost:1521/orcl"}
        mock_config.min_connections = 2
        mock_config.max_connections = 10
        mock_config.pool_increment = 1
        mock_config.connect_timeout = 30
        mock_config.command_timeout = 60000
        mock_config.max_lifetime = 3600
        mock_get_config.return_value = mock_config

        # 模拟 oracledb.Error
        mock_oracledb.create_pool.side_effect = Exception("Connection failed")
        mock_oracledb.Error = Exception

        pool = ConnectionPool()

        with pytest.raises(ConnectionException):
            pool.initialize()

    def test_get_connection_with_pool(self):
        """测试获取连接 - 直接使用已初始化的池."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.acquire.return_value = mock_conn
        pool._initialized = True
        pool._pool = mock_pool

        # 模拟配置
        with patch("src.database.connection.get_database_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.retry_attempts = 1
            mock_config.retry_delay = 0.5
            mock_get_config.return_value = mock_config

            conn = pool.get_connection(retry=False)

        assert conn is mock_conn
        mock_pool.acquire.assert_called_once()

    def test_get_connection_exhausted(self):
        """测试连接池耗尽."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        mock_pool.acquire.side_effect = Exception("Pool exhausted")
        pool._initialized = True
        pool._pool = mock_pool

        with patch("src.database.connection.get_database_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.retry_attempts = 1
            mock_get_config.return_value = mock_config
            mock_oracledb = MagicMock()
            mock_oracledb.Error = Exception
            with patch("src.database.connection.oracledb", mock_oracledb):
                with pytest.raises(PoolExhaustedException):
                    pool.get_connection(retry=False)

    def test_release_connection(self):
        """测试释放连接."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        pool._pool = mock_pool

        mock_conn = MagicMock()
        pool.release_connection(mock_conn)

        mock_pool.release.assert_called_once_with(mock_conn)

    def test_release_connection_no_pool(self):
        """测试无连接池时释放连接."""
        pool = ConnectionPool()
        mock_conn = MagicMock()

        # 不应该抛出异常
        pool.release_connection(mock_conn)

    def test_release_connection_none(self):
        """测试释放 None 连接."""
        pool = ConnectionPool()

        # 不应该抛出异常
        pool.release_connection(None)

    def test_release_connection_exception(self):
        """测试释放连接时异常处理."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        mock_pool.release.side_effect = Exception("Release failed")
        pool._pool = mock_pool

        mock_conn = MagicMock()
        # 模拟 oracledb.Error
        with patch("src.database.connection.oracledb") as mock_oracledb:
            mock_oracledb.Error = Exception
            # 不应该抛出异常
            pool.release_connection(mock_conn)

    def test_connection_context_manager(self):
        """测试上下文管理器."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_pool.acquire.return_value = mock_conn
        pool._initialized = True
        pool._pool = mock_pool

        with patch("src.database.connection.get_database_config"):
            with pool.connection() as conn:
                assert conn is mock_conn

        mock_pool.release.assert_called_once_with(mock_conn)

    def test_close(self):
        """测试关闭连接池."""
        pool = ConnectionPool()
        mock_pool = MagicMock()
        pool._pool = mock_pool
        pool._initialized = True

        pool.close()

        mock_pool.close.assert_called_once()
        assert pool._pool is None
        assert pool._initialized is False

    def test_close_no_pool(self):
        """测试无连接池时关闭."""
        pool = ConnectionPool()
        pool._initialized = False

        # 不应该抛出异常
        pool.close()

    def test_is_healthy_not_initialized(self):
        """测试健康检查 - 未初始化."""
        pool = ConnectionPool()
        pool._initialized = False

        result = pool.is_healthy()

        assert result is False

    def test_is_healthy_no_pool(self):
        """测试健康检查 - 无连接池."""
        pool = ConnectionPool()
        pool._initialized = True
        pool._pool = None

        result = pool.is_healthy()

        assert result is False

    def test_is_healthy_healthy(self):
        """测试健康检查 - 健康."""
        pool = ConnectionPool()
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

        pool._initialized = True
        pool._pool = mock_pool

        result = pool.is_healthy()

        assert result is True


class TestGetConnectionPool:
    """get_connection_pool 函数测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        db_config_module._config = None
        db_config_module._config_lock = MagicMock()
        import src.database.connection as conn_module

        conn_module._connection_pool = None
        conn_module._pool_lock = MagicMock()

    def test_get_connection_pool_singleton(self):
        """测试单例模式."""
        pool1 = get_connection_pool()
        pool2 = get_connection_pool()

        assert pool1 is pool2

    def test_get_connection_pool_returns_connection_pool(self):
        """测试返回类型."""
        pool = get_connection_pool()

        assert isinstance(pool, ConnectionPool)
