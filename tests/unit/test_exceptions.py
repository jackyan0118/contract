"""异常模块测试."""

import pytest

from src.exceptions.base import AppException, ErrorCode, ErrorDetail
from src.exceptions.config import ConfigException, ConfigNotFoundError, ConfigValidationError
from src.exceptions.database import (
    ConnectionException,
    DatabaseException,
    PoolExhaustedException,
    QueryException,
)
from src.exceptions.template import MatchException, RuleParseException, TemplateException, TemplateNotFoundError
from src.exceptions.document import DocumentException, DocumentGenerateException, FileWriteException
from src.exceptions.api import (
    APIException,
    ExternalServiceException,
    NotFoundException,
    ServiceException,
    ValidationError as ApiValidationError,
)


class TestErrorCode:
    """ErrorCode 枚举测试类."""

    def test_error_code_values(self):
        """测试错误代码值."""
        assert ErrorCode.SUCCESS.value == "0"
        assert ErrorCode.UNKNOWN_ERROR.value == "1000"
        assert ErrorCode.VALIDATION_ERROR.value == "1001"
        assert ErrorCode.NOT_FOUND.value == "1002"
        assert ErrorCode.PERMISSION_DENIED.value == "1003"
        assert ErrorCode.CONFIG_ERROR.value == "2000"
        assert ErrorCode.CONFIG_NOT_FOUND.value == "2001"
        assert ErrorCode.CONFIG_VALIDATION_ERROR.value == "2002"
        assert ErrorCode.DATABASE_ERROR.value == "3000"
        assert ErrorCode.CONNECTION_ERROR.value == "3001"
        assert ErrorCode.QUERY_ERROR.value == "3002"
        assert ErrorCode.POOL_EXHAUSTED.value == "3003"
        assert ErrorCode.TEMPLATE_ERROR.value == "4000"
        assert ErrorCode.TEMPLATE_NOT_FOUND.value == "4001"
        assert ErrorCode.MATCH_ERROR.value == "4002"
        assert ErrorCode.RULE_PARSE_ERROR.value == "4003"
        assert ErrorCode.DOCUMENT_ERROR.value == "5000"
        assert ErrorCode.DOCUMENT_GENERATE_ERROR.value == "5001"
        assert ErrorCode.FILE_WRITE_ERROR.value == "5002"
        assert ErrorCode.SERVICE_ERROR.value == "6000"
        assert ErrorCode.EXTERNAL_SERVICE_ERROR.value == "6001"


class TestErrorDetail:
    """ErrorDetail 测试类."""

    def test_creation(self):
        """测试创建."""
        detail = ErrorDetail(
            code=ErrorCode.SUCCESS,
            message="Success",
        )
        assert detail.code == ErrorCode.SUCCESS
        assert detail.message == "Success"
        assert detail.detail is None

    def test_creation_with_detail(self):
        """测试带详情的创建."""
        detail = ErrorDetail(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            detail={"field": "name", "reason": "required"},
        )
        assert detail.code == ErrorCode.VALIDATION_ERROR
        assert detail.detail == {"field": "name", "reason": "required"}


class TestAppException:
    """AppException 测试类."""

    def test_basic_creation(self):
        """测试基本创建."""
        exc = AppException("Test error")
        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert exc.detail == {}
        assert exc.cause is None

    def test_with_error_code(self):
        """测试带错误代码."""
        exc = AppException("Config error", error_code=ErrorCode.CONFIG_ERROR)
        assert exc.error_code == ErrorCode.CONFIG_ERROR

    def test_with_detail(self):
        """测试带详情."""
        exc = AppException("Error", detail={"key": "value"})
        assert exc.detail == {"key": "value"}

    def test_with_cause(self):
        """测试带原因."""
        original = ValueError("Original error")
        exc = AppException("Wrapper error", cause=original)
        assert exc.cause == original

    def test_to_dict(self):
        """测试转换为字典."""
        exc = AppException(
            "Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            detail={"field": "name"},
        )
        result = exc.to_dict()

        assert result["error_code"] == ErrorCode.VALIDATION_ERROR.value
        assert result["message"] == "Test error"
        assert result["detail"] == {"field": "name"}

    def test_to_error_detail(self):
        """测试转换为 ErrorDetail."""
        exc = AppException(
            "Test error",
            error_code=ErrorCode.NOT_FOUND,
            detail={"resource": "template"},
        )
        result = exc.to_error_detail()

        assert isinstance(result, ErrorDetail)
        assert result.code == ErrorCode.NOT_FOUND
        assert result.message == "Test error"
        assert result.detail == {"resource": "template"}

    def test_str_representation(self):
        """测试字符串表示."""
        exc = AppException("Test error")
        assert str(exc) == "Test error"


# === 配置异常测试 ===

class TestConfigException:
    """ConfigException 测试类."""

    def test_default_error_code(self):
        """测试默认错误代码."""
        exc = ConfigException("Config error")
        assert exc.error_code == ErrorCode.CONFIG_ERROR


class TestConfigNotFoundError:
    """ConfigNotFoundError 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ConfigNotFoundError("database.dsn")
        assert exc.error_code == ErrorCode.CONFIG_NOT_FOUND
        assert "database.dsn" in exc.message
        assert exc.detail["key"] == "database.dsn"

    def test_with_detail(self):
        """测试带详情."""
        exc = ConfigNotFoundError("db.host", detail={"source": "yaml"})
        assert exc.detail["key"] == "db.host"
        assert exc.detail["source"] == "yaml"


class TestConfigValidationError:
    """ConfigValidationError 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ConfigValidationError("port", "must be between 1 and 65535")
        assert exc.error_code == ErrorCode.CONFIG_VALIDATION_ERROR
        assert "port" in exc.message
        assert exc.detail["key"] == "port"
        assert exc.detail["reason"] == "must be between 1 and 65535"


# === 数据库异常测试 ===

class TestDatabaseException:
    """DatabaseException 测试类."""

    def test_default_error_code(self):
        """测试默认错误代码."""
        exc = DatabaseException("DB error")
        assert exc.error_code == ErrorCode.DATABASE_ERROR


class TestConnectionException:
    """ConnectionException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ConnectionException("connection refused")
        assert exc.error_code == ErrorCode.CONNECTION_ERROR
        assert "connection refused" in exc.message
        assert exc.detail["reason"] == "connection refused"


class TestQueryException:
    """QueryException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = QueryException("SELECT * FROM users", "timeout")
        assert exc.error_code == ErrorCode.QUERY_ERROR
        assert "timeout" in exc.message

    def test_sanitize_query(self):
        """测试 SQL 脱敏."""
        exc = QueryException("SELECT * FROM users WHERE name = 'admin'", "error")
        assert "'admin'" not in exc.detail["query"]
        assert "***" in exc.detail["query"]

    def test_sanitize_query_no_strings(self):
        """测试无字符串的 SQL."""
        exc = QueryException("SELECT id FROM users", "error")
        assert exc.detail["query"] == "SELECT id FROM users"


class TestPoolExhaustedException:
    """PoolExhaustedException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = PoolExhaustedException()
        assert exc.error_code == ErrorCode.POOL_EXHAUSTED
        assert "连接池已耗尽" in exc.message


# === 模板异常测试 ===

class TestTemplateException:
    """TemplateException 测试类."""

    def test_default_error_code(self):
        """测试默认错误代码."""
        exc = TemplateException("Template error")
        assert exc.error_code == ErrorCode.TEMPLATE_ERROR


class TestTemplateNotFoundError:
    """TemplateNotFoundError 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = TemplateNotFoundError("price_template.docx")
        assert exc.error_code == ErrorCode.TEMPLATE_NOT_FOUND
        assert "price_template.docx" in exc.message
        assert exc.detail["template_name"] == "price_template.docx"


class TestMatchException:
    """MatchException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = MatchException("WYBS001", "no matching template")
        assert exc.error_code == ErrorCode.MATCH_ERROR
        assert exc.detail["wybs"] == "WYBS001"
        assert exc.detail["reason"] == "no matching template"


class TestRuleParseException:
    """RuleParseException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = RuleParseException("rules.xlsx", "invalid format")
        assert exc.error_code == ErrorCode.RULE_PARSE_ERROR
        assert "rules.xlsx" in exc.message
        assert exc.detail["file_name"] == "rules.xlsx"


# === 文档异常测试 ===

class TestDocumentException:
    """DocumentException 测试类."""

    def test_default_error_code(self):
        """测试默认错误代码."""
        exc = DocumentException("Document error")
        assert exc.error_code == ErrorCode.DOCUMENT_ERROR


class TestDocumentGenerateException:
    """DocumentGenerateException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = DocumentGenerateException("template.docx", "render failed")
        assert exc.error_code == ErrorCode.DOCUMENT_GENERATE_ERROR
        assert "template.docx" in exc.message
        assert exc.detail["template_name"] == "template.docx"


class TestFileWriteException:
    """FileWriteException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = FileWriteException("/output/file.docx", "permission denied")
        assert exc.error_code == ErrorCode.FILE_WRITE_ERROR
        assert "file.docx" in exc.message
        assert exc.detail["file_path"] == "/output/file.docx"


# === API 异常测试 ===

class TestAPIException:
    """APIException 测试类."""

    def test_default_error_code(self):
        """测试默认错误代码."""
        exc = APIException("API error")
        assert exc.error_code == ErrorCode.SERVICE_ERROR


class TestApiValidationError:
    """API ValidationError 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ApiValidationError("email", "invalid format")
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert "email" in exc.message
        assert exc.detail["field"] == "email"


class TestNotFoundException:
    """NotFoundException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = NotFoundException("Template", "TPL001")
        assert exc.error_code == ErrorCode.NOT_FOUND
        assert "Template" in exc.message
        assert "TPL001" in exc.message


class TestServiceException:
    """ServiceException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ServiceException("TemplateService", "render failed")
        assert exc.error_code == ErrorCode.SERVICE_ERROR
        assert "TemplateService" in exc.message
        assert exc.detail["service"] == "TemplateService"


class TestExternalServiceException:
    """ExternalServiceException 测试类."""

    def test_creation(self):
        """测试创建."""
        exc = ExternalServiceException("Oracle DB", "connection timeout")
        assert exc.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR
        assert "Oracle DB" in exc.message
        assert exc.detail["service"] == "Oracle DB"


# === 异常继承关系测试 ===

class TestExceptionHierarchy:
    """异常继承关系测试类."""

    def test_config_exceptions_inherit(self):
        """测试配置异常继承."""
        assert issubclass(ConfigException, AppException)
        assert issubclass(ConfigNotFoundError, ConfigException)
        assert issubclass(ConfigValidationError, ConfigException)

    def test_database_exceptions_inherit(self):
        """测试数据库异常继承."""
        assert issubclass(DatabaseException, AppException)
        assert issubclass(ConnectionException, DatabaseException)
        assert issubclass(QueryException, DatabaseException)
        assert issubclass(PoolExhaustedException, DatabaseException)

    def test_template_exceptions_inherit(self):
        """测试模板异常继承."""
        assert issubclass(TemplateException, AppException)
        assert issubclass(TemplateNotFoundError, TemplateException)
        assert issubclass(MatchException, TemplateException)
        assert issubclass(RuleParseException, TemplateException)

    def test_document_exceptions_inherit(self):
        """测试文档异常继承."""
        assert issubclass(DocumentException, AppException)
        assert issubclass(DocumentGenerateException, DocumentException)
        assert issubclass(FileWriteException, DocumentException)

    def test_api_exceptions_inherit(self):
        """测试 API 异常继承."""
        assert issubclass(APIException, AppException)
        assert issubclass(ApiValidationError, APIException)
        assert issubclass(NotFoundException, APIException)
        assert issubclass(ServiceException, APIException)
        assert issubclass(ExternalServiceException, APIException)
