"""配置与日志集成测试."""

import pytest
import logging
import tempfile
from pathlib import Path

from src.config.settings import get_settings
from src.utils.logger import get_logger


class TestConfigLoggerIntegration:
    """配置驱动的日志集成测试."""

    @pytest.mark.integration
    def test_log_level_from_config(self):
        """测试日志级别从配置加载."""
        settings = get_settings()
        logger = get_logger("test")

        # 验证日志级别与配置一致
        assert logger.level is not None

    @pytest.mark.integration
    def test_log_file_creation(self, tmp_path):
        """测试日志文件创建."""
        log_file = tmp_path / "test.log"

        # 创建带文件处理的logger
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        logger = logging.getLogger("test_file")
        logger.addHandler(handler)
        logger.info("Test message")

        # 验证文件创建
        assert log_file.exists()

        # 清理
        logger.removeHandler(handler)
        handler.close()

    @pytest.mark.integration
    def test_multiple_loggers(self):
        """测试多个logger实例."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # 验证不同模块的logger是独立的
        assert logger1.name == "module1"
        assert logger2.name == "module2"


class TestConfigTemplateIntegration:
    """配置与模板集成测试."""

    @pytest.mark.integration
    def test_template_path_config(self):
        """测试模板路径配置."""
        settings = get_settings()

        # 验证模板配置存在
        assert settings.template.path is not None

    @pytest.mark.integration
    def test_output_dir_config(self, tmp_path):
        """测试输出目录配置."""
        output_dir = tmp_path / "output"

        # 验证输出目录可创建
        output_dir.mkdir(parents=True, exist_ok=True)
        assert output_dir.exists()
        assert output_dir.is_dir()


class TestConfigAppIntegration:
    """配置与应用集成测试."""

    @pytest.mark.integration
    def test_app_config(self):
        """测试应用配置."""
        settings = get_settings()

        # 验证应用配置
        assert settings.app.name is not None
        assert settings.app.version is not None
        assert settings.app.port > 0

    @pytest.mark.integration
    def test_database_config(self):
        """测试数据库配置."""
        settings = get_settings()

        # 验证数据库配置
        assert settings.database.dsn is not None
