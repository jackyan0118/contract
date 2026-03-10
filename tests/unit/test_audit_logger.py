"""审计日志服务单元测试."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from src.services.audit_logger import AuditLogger, AuditEvent, get_audit_logger


class TestAuditLogger:
    """AuditLogger 测试"""

    @pytest.fixture
    def temp_log_file(self):
        """创建临时日志文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # 清理
        Path(temp_path).unlink(missing_ok=True)

    def test_logger_creation(self, temp_log_file):
        """测试日志器创建"""
        logger = AuditLogger(log_file=temp_log_file)
        assert logger._log_file == Path(temp_log_file)

    def test_mask_user_short(self):
        """测试短用户标识脱敏"""
        logger = AuditLogger()
        # 3字符或更短
        assert logger._mask_user("abc") == "***"
        assert logger._mask_user("ab") == "***"
        assert logger._mask_user("a") == "***"

    def test_mask_user_medium(self):
        """测试中等长度用户标识脱敏"""
        logger = AuditLogger()
        # 4-6字符
        assert logger._mask_user("abcd") == "abc***"
        assert logger._mask_user("abcdef") == "abc***"

    def test_mask_user_long(self):
        """测试长用户标识脱敏"""
        logger = AuditLogger()
        # 7字符以上
        assert logger._mask_user("abcdefg") == "abc***"
        assert logger._mask_user("sk_dev_12345") == "sk_***"

    def test_mask_user_empty(self):
        """测试空用户标识"""
        logger = AuditLogger()
        assert logger._mask_user("") == "unknown"
        assert logger._mask_user(None) == "unknown"

    def test_mask_user_agent_chrome(self):
        """测试 User-Agent 脱敏 Chrome"""
        logger = AuditLogger()
        assert logger._mask_user_agent("Mozilla/5.0 Chrome/120.0.0.0") == "Chrome"

    def test_mask_user_agent_firefox(self):
        """测试 User-Agent 脱敏 Firefox"""
        logger = AuditLogger()
        assert logger._mask_user_agent("Mozilla/5.0 Firefox/120.0") == "Firefox"

    def test_mask_user_agent_safari(self):
        """测试 User-Agent 脱敏 Safari"""
        logger = AuditLogger()
        assert logger._mask_user_agent("Mozilla/5.0 Safari/120.0") == "Safari"

    def test_mask_user_agent_curl(self):
        """测试 User-Agent 脱敏 curl"""
        logger = AuditLogger()
        assert logger._mask_user_agent("curl/7.68.0") == "curl"

    def test_mask_user_agent_python(self):
        """测试 User-Agent 脱敏 Python"""
        logger = AuditLogger()
        assert logger._mask_user_agent("Python/3.11") == "Python"

    def test_mask_user_agent_unknown(self):
        """测试未知 User-Agent"""
        logger = AuditLogger()
        assert logger._mask_user_agent("Unknown/1.0") == "Other"
        assert logger._mask_user_agent("") == "unknown"
        assert logger._mask_user_agent(None) == "unknown"

    def test_sanitize_details(self):
        """测试敏感字段过滤"""
        logger = AuditLogger()

        # 包含敏感字段
        details = {
            "username": "john",
            "password": "secret123",
            "token": "abc123",
            "api_key": "key123",
            "action": "login",
        }
        sanitized = logger._sanitize_details(details)

        assert sanitized["username"] == "john"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["action"] == "login"

    def test_sanitize_details_empty(self):
        """测试空详情"""
        logger = AuditLogger()
        assert logger._sanitize_details({}) == {}
        assert logger._sanitize_details(None) == {}

    def test_sanitize_case_insensitive(self):
        """测试大小写不敏感"""
        logger = AuditLogger()
        details = {
            "PASSWORD": "secret",
            "Password": "secret",
            "passWord": "secret",
        }
        sanitized = logger._sanitize_details(details)

        assert all(v == "***REDACTED***" for v in sanitized.values())

    def test_log_basic(self, temp_log_file):
        """测试基础日志记录"""
        logger = AuditLogger(log_file=temp_log_file)

        logger.log(
            event=AuditEvent.API_REQUEST,
            user="sk_dev_123456",
            resource="/api/v1/generate",
            action="POST",
            result="success",
            request_id="req_abc123",
        )

        # 验证文件内容
        with open(temp_log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0])
            assert log_entry["event"] == "api_request"
            assert log_entry["user"] == "sk_***"  # 脱敏
            assert log_entry["resource"] == "/api/v1/generate"
            assert log_entry["result"] == "success"


class TestAuditEvent:
    """AuditEvent 枚举测试"""

    def test_event_values(self):
        """测试事件值"""
        assert AuditEvent.API_REQUEST.value == "api_request"
        assert AuditEvent.GENERATE.value == "generate"
        assert AuditEvent.BATCH_GENERATE.value == "batch_generate"
        assert AuditEvent.TASK_CREATE.value == "task_create"
        assert AuditEvent.TASK_CANCEL.value == "task_cancel"
        assert AuditEvent.AUTH_SUCCESS.value == "auth_success"
        assert AuditEvent.AUTH_FAILURE.value == "auth_failure"


class TestGetAuditLogger:
    """get_audit_logger 单例测试"""

    def test_singleton(self):
        """测试单例模式"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2
