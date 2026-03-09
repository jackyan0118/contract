"""日志模块测试."""

import logging
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.utils.logger import ColoredFormatter, get_logger, setup_logger
from src.config.settings import LoggingSettings


class TestColoredFormatter:
    """ColoredFormatter 测试类."""

    def test_format_debug(self):
        """测试 DEBUG 级别格式化."""
        formatter = ColoredFormatter("[%(levelname)s] %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="debug message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "DEBUG" in result
        assert "debug message" in result

    def test_format_info(self):
        """测试 INFO 级别格式化."""
        formatter = ColoredFormatter("[%(levelname)s] %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="info message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "info message" in result

    def test_format_warning(self):
        """测试 WARNING 级别格式化."""
        formatter = ColoredFormatter("[%(levelname)s] %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="warning message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "WARNING" in result

    def test_format_error(self):
        """测试 ERROR 级别格式化."""
        formatter = ColoredFormatter("[%(levelname)s] %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "ERROR" in result

    def test_format_critical(self):
        """测试 CRITICAL 级别格式化."""
        formatter = ColoredFormatter("[%(levelname)s] %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=1,
            msg="critical message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "CRITICAL" in result


class TestSetupLogger:
    """setup_logger 函数测试类."""

    def test_setup_logger_basic(self):
        """测试基本日志设置."""
        config = LoggingSettings(
            level="INFO",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test.log",
        )
        logger = setup_logger("test_logger", config)

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1

    def test_setup_logger_console_handler(self):
        """测试控制台 handler."""
        config = LoggingSettings(
            level="DEBUG",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test.log",
        )
        logger = setup_logger("test_console", config)

        # 检查是否有 StreamHandler
        has_console = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )
        assert has_console

    def test_setup_logger_file_handler(self):
        """测试文件 handler."""
        config = LoggingSettings(
            level="INFO",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test_handler.log",
        )
        logger = setup_logger("test_file", config)

        # 检查是否有 FileHandler
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert has_file

    def test_setup_logger_default_config(self):
        """测试使用默认配置."""
        with patch("src.utils.logger.settings") as mock_settings:
            mock_settings.logging = LoggingSettings(level="INFO")
            logger = setup_logger("test_default")
            assert logger.level == logging.INFO

    def test_setup_logger_no_duplicate_handlers(self):
        """测试不重复添加 handler."""
        config = LoggingSettings(
            level="INFO",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test_dup.log",
        )
        logger = setup_logger("test_dup_handler", config)

        # 再次调用 setup_logger 不应添加新的 handler
        original_handler_count = len(logger.handlers)
        logger2 = setup_logger("test_dup_handler", config)
        assert len(logger2.handlers) == original_handler_count

    def test_setup_logger_creates_log_directory(self):
        """测试创建日志目录."""
        config = LoggingSettings(
            level="INFO",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test_dir/app.log",
        )

        with patch("src.utils.logger.Path.mkdir") as mock_mkdir:
            with patch("src.utils.logger.RotatingFileHandler"):
                setup_logger("test_dir", config)
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestGetLogger:
    """get_logger 函数测试类."""

    def test_get_logger_returns_logger(self):
        """测试返回 logger 实例."""
        logger = get_logger("test_get_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_get_logger"

    def test_get_logger_cached(self):
        """测试 logger 缓存."""
        logger1 = get_logger("test_cache")
        logger2 = get_logger("test_cache")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """测试不同名称返回不同 logger."""
        logger1 = get_logger("test_name1")
        logger2 = get_logger("test_name2")
        assert logger1 is not logger2


class TestLoggerIntegration:
    """日志集成测试类."""

    def test_logger_output_to_console(self):
        """测试日志输出到控制台."""
        config = LoggingSettings(
            level="DEBUG",
            format_console="%(message)s",
            format_file="%(message)s",
            file_path="logs/test_output.log",
        )

        # 捕获 stdout
        captured_output = StringIO()
        handler = logging.StreamHandler(captured_output)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = logging.getLogger("test_output_console")
        logger.handlers.clear()  # 清除已有的 handlers
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("test message")
        assert "test message" in captured_output.getvalue()

    def test_logger_level_mapping(self):
        """测试日志级别映射."""
        for level_str, expected_level in [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]:
            config = LoggingSettings(level=level_str)
            logger = setup_logger(f"test_level_{level_str}", config)
            assert logger.level == expected_level
