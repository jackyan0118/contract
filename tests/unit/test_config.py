"""配置管理模块测试."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import SecretStr, ValidationError
from pydantic_settings import SettingsConfigDict

from src.config.settings import (
    AppSettings,
    DatabaseSettings,
    LoggingSettings,
    Settings,
    TemplateSettings,
    get_settings,
)


class TestAppSettings:
    """AppSettings 测试类."""

    def test_default_values(self, monkeypatch):
        """测试默认值."""
        # 模拟没有环境变量的情况
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("APP_DEBUG", raising=False)
        monkeypatch.delenv("APP_VERSION", raising=False)
        monkeypatch.delenv("APP_HOST", raising=False)
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = AppSettings(_env_file=None)
        assert settings.name == "价格附件生成系统"
        assert settings.debug is False
        assert settings.version == "0.1.0"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

    def test_custom_values(self, monkeypatch):
        """测试自定义值."""
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("APP_DEBUG", raising=False)
        monkeypatch.delenv("APP_VERSION", raising=False)
        monkeypatch.delenv("APP_HOST", raising=False)
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = AppSettings(
            name="测试应用",
            debug=True,
            version="1.0.0",
            host="127.0.0.1",
            port=9000,
            _env_file=None,
        )
        assert settings.name == "测试应用"
        assert settings.debug is True
        assert settings.version == "1.0.0"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000

    def test_port_validator_valid(self, monkeypatch):
        """测试端口验证器 - 有效值."""
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = AppSettings(port=8080, _env_file=None)
        assert settings.port == 8080

    def test_port_validator_min_boundary(self, monkeypatch):
        """测试端口验证器 - 最小边界."""
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = AppSettings(port=1, _env_file=None)
        assert settings.port == 1

    def test_port_validator_max_boundary(self, monkeypatch):
        """测试端口验证器 - 最大边界."""
        monkeypatch.delenv("APP_PORT", raising=False)
        settings = AppSettings(port=65535, _env_file=None)
        assert settings.port == 65535

    def test_port_validator_invalid_below_min(self, monkeypatch):
        """测试端口验证器 - 小于最小值."""
        monkeypatch.delenv("APP_PORT", raising=False)
        with pytest.raises(ValidationError):
            AppSettings(port=0, _env_file=None)

    def test_port_validator_invalid_above_max(self, monkeypatch):
        """测试端口验证器 - 大于最大值."""
        monkeypatch.delenv("APP_PORT", raising=False)
        with pytest.raises(ValidationError):
            AppSettings(port=65536, _env_file=None)

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖."""
        monkeypatch.setenv("APP_PORT", "3000")
        settings = AppSettings(_env_file=None)
        assert settings.port == 3000


class TestDatabaseSettings:
    """DatabaseSettings 测试类."""

    def test_default_values(self, monkeypatch):
        """测试默认值."""
        monkeypatch.delenv("DB_DSN", raising=False)
        # 需要设置有效的 DSN，否则会验证失败
        settings = DatabaseSettings(
            dsn=SecretStr("oracle://user:pass@host:1521/db"),
            _env_file=None,
        )
        assert settings.min_connections == 2
        assert settings.max_connections == 10
        assert settings.pool_increment == 1
        assert settings.connect_timeout == 30
        assert settings.command_timeout == 60

    def test_custom_values(self, monkeypatch):
        """测试自定义值."""
        monkeypatch.delenv("DB_DSN", raising=False)
        settings = DatabaseSettings(
            dsn=SecretStr("oracle://user:pass@host:1521/db"),
            min_connections=5,
            max_connections=20,
            pool_increment=2,
            connect_timeout=60,
            command_timeout=120,
            _env_file=None,
        )
        assert settings.min_connections == 5
        assert settings.max_connections == 20
        assert settings.pool_increment == 2
        assert settings.connect_timeout == 60
        assert settings.command_timeout == 120

    def test_validate_dsn_empty(self, monkeypatch):
        """测试 DSN 验证 - 空值."""
        monkeypatch.delenv("DB_DSN", raising=False)
        with pytest.raises(ValidationError):
            DatabaseSettings(dsn=SecretStr(""), _env_file=None)

    def test_validate_max_connections(self, monkeypatch):
        """测试最大连接数验证."""
        monkeypatch.delenv("DB_DSN", raising=False)
        settings = DatabaseSettings(
            dsn=SecretStr("oracle://user:pass@host:1521/db"),
            max_connections=50,
            _env_file=None,
        )
        assert settings.max_connections == 50

    def test_validate_max_connections_invalid(self, monkeypatch):
        """测试最大连接数验证 - 无效值."""
        monkeypatch.delenv("DB_DSN", raising=False)
        with pytest.raises(ValidationError):
            DatabaseSettings(
                dsn=SecretStr("oracle://user:pass@host:1521/db"),
                max_connections=0,
                _env_file=None,
            )

    def test_validate_pool_size(self, monkeypatch):
        """测试连接池大小验证 - 有效."""
        monkeypatch.delenv("DB_DSN", raising=False)
        settings = DatabaseSettings(
            dsn=SecretStr("oracle://user:pass@host:1521/db"),
            min_connections=2,
            max_connections=5,
            _env_file=None,
        )
        assert settings.max_connections >= settings.min_connections

    def test_validate_pool_size_invalid(self, monkeypatch):
        """测试连接池大小验证 - 无效."""
        monkeypatch.delenv("DB_DSN", raising=False)
        with pytest.raises(ValidationError):
            DatabaseSettings(
                dsn=SecretStr("oracle://user:pass@host:1521/db"),
                min_connections=10,
                max_connections=5,
                _env_file=None,
            )

    def test_get_dsn(self, monkeypatch):
        """测试获取解密后的 DSN."""
        monkeypatch.delenv("DB_DSN", raising=False)
        settings = DatabaseSettings(
            dsn=SecretStr("oracle://user:pass@host:1521/db"),
            _env_file=None,
        )
        assert settings.get_dsn() == "oracle://user:pass@host:1521/db"


class TestLoggingSettings:
    """LoggingSettings 测试类."""

    def test_default_values(self, monkeypatch):
        """测试默认值."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        settings = LoggingSettings(_env_file=None)
        assert settings.level == "INFO"
        assert settings.format_console == "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
        assert settings.format_file == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert settings.file_path == "logs/app.log"
        assert settings.max_bytes == 10485760
        assert settings.backup_count == 5

    def test_custom_values(self, monkeypatch):
        """测试自定义值."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        settings = LoggingSettings(
            level="DEBUG",
            format_console="%(message)s",
            format_file="%(asctime)s - %(message)s",
            file_path="logs/custom.log",
            max_bytes=2097152,
            backup_count=3,
            _env_file=None,
        )
        assert settings.level == "DEBUG"
        assert settings.format_console == "%(message)s"
        assert settings.file_path == "logs/custom.log"
        assert settings.max_bytes == 2097152
        assert settings.backup_count == 3

    def test_validate_level_valid(self, monkeypatch):
        """测试日志级别验证 - 有效值."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = LoggingSettings(level=level, _env_file=None)
            assert settings.level == level

    def test_validate_level_lowercase(self, monkeypatch):
        """测试日志级别验证 - 小写转大写."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        settings = LoggingSettings(level="info", _env_file=None)
        assert settings.level == "INFO"

    def test_validate_level_invalid(self, monkeypatch):
        """测试日志级别验证 - 无效值."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        with pytest.raises(ValidationError):
            LoggingSettings(level="INVALID", _env_file=None)


class TestTemplateSettings:
    """TemplateSettings 测试类."""

    def test_default_values(self, monkeypatch):
        """测试默认值."""
        monkeypatch.delenv("TEMPLATE_PATH", raising=False)
        monkeypatch.delenv("TEMPLATE_RULE_FILE", raising=False)
        monkeypatch.delenv("TEMPLATE_OUTPUT_DIR", raising=False)
        monkeypatch.delenv("TEMPLATE_MAX_FILE_SIZE", raising=False)
        settings = TemplateSettings(_env_file=None)
        assert settings.path == "templates"
        assert settings.rule_file == "价格模板规则 - 更新 2026306.xlsx"
        assert settings.output_dir == "output"
        assert settings.max_file_size == 10485760

    def test_custom_values(self, monkeypatch):
        """测试自定义值."""
        monkeypatch.delenv("TEMPLATE_PATH", raising=False)
        monkeypatch.delenv("TEMPLATE_RULE_FILE", raising=False)
        monkeypatch.delenv("TEMPLATE_OUTPUT_DIR", raising=False)
        monkeypatch.delenv("TEMPLATE_MAX_FILE_SIZE", raising=False)
        settings = TemplateSettings(
            path="/custom/templates",
            rule_file="rules.xlsx",
            output_dir="/custom/output",
            max_file_size=20971520,
            _env_file=None,
        )
        assert settings.path == "/custom/templates"
        assert settings.rule_file == "rules.xlsx"
        assert settings.output_dir == "/custom/output"
        assert settings.max_file_size == 20971520


class TestSettings:
    """Settings 聚合配置测试类."""

    def test_default_factory(self):
        """测试默认工厂."""
        # 直接测试默认值（使用 _env_file=None 来避免环境变量干扰）
        app = AppSettings(_env_file=None)
        database = DatabaseSettings(
            dsn=SecretStr("oracle://test:test@localhost:1521/orcl"),
            _env_file=None,
        )
        logging_settings = LoggingSettings(_env_file=None)
        template = TemplateSettings(_env_file=None)

        assert isinstance(app, AppSettings)
        assert isinstance(database, DatabaseSettings)
        assert isinstance(logging_settings, LoggingSettings)
        assert isinstance(template, TemplateSettings)

    def test_load_from_yaml(self):
        """测试从 YAML 加载配置."""
        config_data = {
            "app": {
                "name": "测试系统",
                "port": 9000,
            },
            "database": {
                "dsn": "oracle://test:test@localhost:1521/orcl",
            },
            "logging": {
                "level": "DEBUG",
            },
            "template": {
                "path": "/tmp/templates",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            settings = Settings.load_from_yaml(temp_path)
            assert settings.app.name == "测试系统"
            assert settings.app.port == 9000
            assert settings.logging.level == "DEBUG"
            assert settings.template.path == "/tmp/templates"
        finally:
            Path(temp_path).unlink()

    def test_load_from_yaml_partial(self):
        """测试从 YAML 加载配置 - 部分字段."""
        config_data = {
            "app": {
                "name": "部分配置",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            settings = Settings.load_from_yaml(temp_path)
            assert settings.app.name == "部分配置"
            # 其他字段应使用默认值
            assert settings.app.port == 8000
        finally:
            Path(temp_path).unlink()


class TestGetSettings:
    """get_settings 函数测试类."""

    @patch("src.config.settings.Settings.load_from_yaml")
    @patch("src.config.settings.Path.exists")
    def test_get_settings_yaml_exists(self, mock_exists, mock_load):
        """测试 YAML 文件存在时加载配置."""
        mock_exists.return_value = True
        mock_load.return_value = Settings()

        # 清除缓存
        get_settings.cache_clear()

        result = get_settings()
        assert isinstance(result, Settings)
        mock_load.assert_called_once()

    @patch("src.config.settings.Settings.load_from_yaml")
    @patch("src.config.settings.Path.exists")
    def test_get_settings_yaml_not_exists(self, mock_exists, mock_load):
        """测试 YAML 文件不存在时返回默认配置."""
        mock_exists.return_value = False
        # 清除缓存
        get_settings.cache_clear()

        result = get_settings()
        assert isinstance(result, Settings)
        mock_load.assert_not_called()
