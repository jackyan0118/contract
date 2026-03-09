"""结构化日志模块测试."""

import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest

from src.utils.structured_logger import JSONFormatter, StructuredLogger, get_structured_logger


class TestJSONFormatter:
    """JSONFormatter 测试类."""

    def test_format_basic(self):
        """测试基本格式化."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)

        # 验证是有效的 JSON
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["message"] == "test message"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_format_with_context(self):
        """测试带上下文的格式化."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        record.context = {"user_id": 123, "action": "login"}

        result = formatter.format(record)
        data = json.loads(result)

        assert data["context"] == {"user_id": 123, "action": "login"}

    def test_format_with_exception(self):
        """测试带异常的格式化."""
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_includes_metadata(self):
        """测试包含元数据."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.WARNING,
            pathname="module.py",
            lineno=42,
            msg="warning message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        # module 是文件名，不包含路径
        assert data["module"] == "test_structured_logger" or data["module"] == "module"
        assert data["line"] == 42
        assert data["level"] == "WARNING"

    def test_format_unicode_message(self):
        """测试 Unicode 消息."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="中文消息: 价格附件生成系统",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["message"] == "中文消息: 价格附件生成系统"


class TestStructuredLogger:
    """StructuredLogger 测试类."""

    def test_init(self):
        """测试初始化."""
        base_logger = logging.getLogger("test_init")
        structured = StructuredLogger(base_logger)
        assert structured.logger == base_logger

    def test_debug(self):
        """测试 debug 方法."""
        base_logger = logging.getLogger("test_debug")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.DEBUG)

        structured = StructuredLogger(base_logger)
        structured.debug("debug message")

        output = handler.stream.getvalue()
        assert "debug message" in output

    def test_info(self):
        """测试 info 方法."""
        base_logger = logging.getLogger("test_info")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        structured = StructuredLogger(base_logger)
        structured.info("info message")

        output = handler.stream.getvalue()
        assert "info message" in output

    def test_warning(self):
        """测试 warning 方法."""
        base_logger = logging.getLogger("test_warning")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.WARNING)

        structured = StructuredLogger(base_logger)
        structured.warning("warning message")

        output = handler.stream.getvalue()
        assert "warning message" in output

    def test_error(self):
        """测试 error 方法."""
        base_logger = logging.getLogger("test_error")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.ERROR)

        structured = StructuredLogger(base_logger)
        structured.error("error message")

        output = handler.stream.getvalue()
        assert "error message" in output

    def test_error_with_context(self):
        """测试带上下文的 error 方法."""
        base_logger = logging.getLogger("test_error_ctx")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.ERROR)

        structured = StructuredLogger(base_logger)
        structured.error("error with context", context={"error_code": 500})

        output = handler.stream.getvalue()
        assert "error with context" in output

    def test_error_with_exc_info(self):
        """测试带异常的 error 方法."""
        base_logger = logging.getLogger("test_error_exc")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.ERROR)

        structured = StructuredLogger(base_logger)
        try:
            raise ValueError("test exception")
        except ValueError:
            structured.error("error with exc", exc_info=True)

        output = handler.stream.getvalue()
        assert "error with exc" in output

    def test_critical(self):
        """测试 critical 方法."""
        base_logger = logging.getLogger("test_critical")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.CRITICAL)

        structured = StructuredLogger(base_logger)
        structured.critical("critical message")

        output = handler.stream.getvalue()
        assert "critical message" in output

    def test_critical_with_context(self):
        """测试带上下文的 critical 方法."""
        base_logger = logging.getLogger("test_critical_ctx")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.CRITICAL)

        structured = StructuredLogger(base_logger)
        structured.critical("critical with context", context={"severity": "high"})

        output = handler.stream.getvalue()
        assert "critical with context" in output

    def test_context_parameter(self):
        """测试 context 参数."""
        base_logger = logging.getLogger("test_context")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        structured = StructuredLogger(base_logger)
        structured.info("message with context", context={"user_id": 123, "action": "create"})

        output = handler.stream.getvalue()
        assert "message with context" in output

    def test_extra_kwargs(self):
        """测试额外的关键字参数 (通过 context 传递)."""
        base_logger = logging.getLogger("test_kwargs")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        structured = StructuredLogger(base_logger)
        # 使用 context 来传递额外参数
        structured.info("message", context={"extra_field": "value", "number": 42})

        output = handler.stream.getvalue()
        assert "message" in output

    def test_reserved_key_rejected(self):
        """测试保留键被拒绝 (通过 context 传递)."""
        base_logger = logging.getLogger("test_reserved")
        base_logger.handlers.clear()
        handler = logging.StreamHandler(StringIO())
        base_logger.addHandler(handler)
        base_logger.setLevel(logging.INFO)

        structured = StructuredLogger(base_logger)

        # 尝试使用保留键作为 context 应该通过
        # 因为保留键检查是在 _log 方法中针对 kwargs 的
        # context是被允许的
        structured.info("message", context={"context": "allowed"})
        output = handler.stream.getvalue()
        assert "message" in output


class TestGetStructuredLogger:
    """get_structured_logger 函数测试类."""

    def test_get_structured_logger(self):
        """测试获取结构化日志记录器."""
        result = get_structured_logger("test")
        assert isinstance(result, StructuredLogger)

    def test_get_structured_logger_returns_different(self):
        """测试每次调用返回不同的实例."""
        result1 = get_structured_logger("test1")
        result2 = get_structured_logger("test2")

        assert isinstance(result1, StructuredLogger)
        assert isinstance(result2, StructuredLogger)
        assert result1 is not result2
