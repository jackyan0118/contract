"""数据库配置模块测试."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from src.database.config import DatabaseConfig, get_database_config


class TestDatabaseConfig:
    """DatabaseConfig 测试类."""

    @patch("src.database.config.get_database_config")
    def test_from_settings(self, mock_get_config):
        """测试从设置创建配置."""
        # 创建模拟的 DatabaseSettings
        mock_db_settings = MagicMock()
        mock_db_settings.get_dsn.return_value = "oracle://user:pass@localhost:1521/orcl"
        mock_db_settings.min_connections = 2
        mock_db_settings.max_connections = 10
        mock_db_settings.pool_increment = 1
        mock_db_settings.connect_timeout = 30
        mock_db_settings.command_timeout = 60

        config = DatabaseConfig.from_settings(mock_db_settings)

        assert config.dsn == "oracle://user:pass@localhost:1521/orcl"
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.pool_increment == 1
        assert config.connect_timeout == 30
        assert config.command_timeout == 60
        # 测试默认值
        assert config.max_lifetime == 3600
        assert config.retry_attempts == 3
        assert config.retry_delay == 0.5

    @patch("src.database.config.oracledb")
    def test_to_oracledb_params_standard_dsn(self, mock_oracledb):
        """测试标准 DSN 解析."""
        # 模拟 oracledb.parse_dsn 返回标准格式
        mock_oracledb.parse_dsn.return_value = {
            "user": "testuser",
            "password": "testpass",
            "host": "localhost",
            "port": 1521,
            "service_name": "orcl",
        }
        mock_oracledb.makedsn.return_value = "localhost:1521/orcl"

        config = DatabaseConfig(
            dsn="(description=(address=(protocol=tcp)(host=localhost)(port=1521))(connect_data=(service_name=orcl)))",
            min_connections=2,
            max_connections=10,
            pool_increment=1,
            connect_timeout=30,
            command_timeout=60,
        )

        result = config.to_oracledb_params()

        assert result["user"] == "testuser"
        assert result["password"] == "testpass"
        mock_oracledb.makedsn.assert_called_once_with("localhost", 1521, "orcl")

    @patch("src.database.config.oracledb")
    def test_to_oracledb_params_fallback(self, mock_oracledb):
        """测试回退解析 - oracle:// 格式."""
        mock_oracledb.parse_dsn.side_effect = Exception("Parse error")

        config = DatabaseConfig(
            dsn="oracle://user:password@localhost:1521/orcl",
            min_connections=2,
            max_connections=10,
            pool_increment=1,
            connect_timeout=30,
            command_timeout=60,
        )

        result = config.to_oracledb_params()

        assert result["user"] == "user"
        assert result["password"] == "password"
        mock_oracledb.makedsn.assert_called_with("localhost", 1521, "orcl")

    @patch("src.database.config.oracledb")
    def test_to_oracledb_params_fallback_no_port(self, mock_oracledb):
        """测试回退解析 - 无端口."""
        mock_oracledb.parse_dsn.side_effect = Exception("Parse error")

        config = DatabaseConfig(
            dsn="oracle://user:password@localhost/orcl",
            min_connections=2,
            max_connections=10,
            pool_increment=1,
            connect_timeout=30,
            command_timeout=60,
        )

        result = config.to_oracledb_params()

        assert result["user"] == "user"
        assert result["password"] == "password"
        mock_oracledb.makedsn.assert_called_with("localhost", 1521, "orcl")

    @patch("src.database.config.oracledb")
    def test_to_oracledb_params_invalid_format(self, mock_oracledb):
        """测试无效 DSN 格式."""
        mock_oracledb.parse_dsn.side_effect = Exception("Parse error")

        config = DatabaseConfig(
            dsn="invalid-dsn",
            min_connections=2,
            max_connections=10,
            pool_increment=1,
            connect_timeout=30,
            command_timeout=60,
        )

        result = config.to_oracledb_params()

        assert result == {"dsn": "invalid-dsn"}


class TestGetDatabaseConfig:
    """get_database_config 函数测试类."""

    def test_get_database_config_singleton(self):
        """测试单例模式."""
        # 重置全局配置
        import src.database.config as config_module

        original_config = config_module._config
        config_module._config = None

        try:
            with patch("src.database.config.settings") as mock_settings:
                mock_settings.database.get_dsn.return_value = "oracle://test:test@localhost:1521/orcl"

                config1 = get_database_config()
                config2 = get_database_config()

                assert config1 is config2
        finally:
            config_module._config = original_config

    def test_get_database_config_thread_safety(self):
        """测试线程安全."""
        import src.database.config as config_module

        original_config = config_module._config
        config_module._config = None

        try:
            with patch("src.database.config.settings") as mock_settings:
                mock_settings.database.get_dsn.return_value = "oracle://test:test@localhost:1521/orcl"

                config = get_database_config()
                assert isinstance(config, DatabaseConfig)
        finally:
            config_module._config = original_config
