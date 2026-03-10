"""错误处理集成测试."""

import pytest

from src.exceptions import (
    AppException,
    ConfigException,
    DatabaseException,
    TemplateException,
    APIException,
)


class TestExceptionHierarchy:
    """异常层次结构测试."""

    @pytest.mark.integration
    def test_app_exception_base(self):
        """测试基础异常."""
        error = AppException("基础错误")
        assert str(error) == "基础错误"
        assert isinstance(error, Exception)

    @pytest.mark.integration
    def test_config_exception(self):
        """测试配置异常."""
        error = ConfigException("配置错误")
        assert isinstance(error, AppException)

    @pytest.mark.integration
    def test_database_exception(self):
        """测试数据库异常."""
        error = DatabaseException("数据库错误")
        assert isinstance(error, AppException)

    @pytest.mark.integration
    def test_template_exception(self):
        """测试模板异常."""
        error = TemplateException("模板错误")
        assert isinstance(error, AppException)


class TestExceptionHandling:
    """异常处理测试."""

    @pytest.mark.integration
    def test_catch_specific_exception(self):
        """测试捕获特定异常."""
        def raise_template_error():
            raise TemplateException("模板未找到")

        with pytest.raises(TemplateException):
            raise_template_error()

    @pytest.mark.integration
    def test_catch_base_exception(self):
        """测试捕获基础异常."""
        def raise_any_error():
            raise DatabaseException("任何错误")

        with pytest.raises(AppException):
            raise_any_error()

    @pytest.mark.integration
    def test_catch_multiple_exceptions(self):
        """测试捕获多个异常类型."""
        exceptions = [
            ConfigException("配置错误"),
            DatabaseException("数据库错误"),
            TemplateException("模板错误"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AppException)
