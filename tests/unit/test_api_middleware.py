"""API 中间件单元测试."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, Request
from fastapi.security import APIKeyHeader

from src.api.middleware.auth import AuthService, get_auth_service


class TestAuthService:
    """AuthService 测试"""

    def test_load_keys_empty(self):
        """测试加载空密钥列表"""
        with patch('src.api.middleware.auth.get_settings') as mock_settings:
            mock_settings.return_value.security.api_keys = []

            service = AuthService()
            assert len(service._valid_keys) == 0

    def test_load_keys_with_enabled(self):
        """测试加载启用的密钥"""
        with patch('src.api.middleware.auth.get_settings') as mock_settings:
            mock_settings.return_value.security.api_keys = [
                {"key": "sk_dev_123", "enabled": True, "name": "dev"},
                {"key": "sk_prod_456", "enabled": False, "name": "prod"},
            ]

            service = AuthService()
            assert "sk_dev_123" in service._valid_keys
            assert "sk_prod_456" not in service._valid_keys

    def test_validate_key_empty(self):
        """测试空密钥验证"""
        service = AuthService()
        assert service.validate_key(None) is False
        assert service.validate_key("") is False

    def test_validate_key_bearer_format(self):
        """测试 Bearer 格式"""
        with patch('src.api.middleware.auth.get_settings') as mock_settings:
            mock_settings.return_value.security.api_keys = [
                {"key": "sk_dev_123", "enabled": True, "name": "dev"},
            ]

            service = AuthService()
            # 不带 Bearer 前缀
            assert service.validate_key("sk_dev_123") is True
            # 带 Bearer 前缀
            assert service.validate_key("Bearer sk_dev_123") is True

    def test_validate_key_invalid(self):
        """测试无效密钥"""
        with patch('src.api.middleware.auth.get_settings') as mock_settings:
            mock_settings.return_value.security.api_keys = [
                {"key": "sk_dev_123", "enabled": True, "name": "dev"},
            ]

            service = AuthService()
            assert service.validate_key("invalid_key") is False
            assert service.validate_key("Bearer wrong_key") is False


class TestGetAuthService:
    """get_auth_service 单例测试"""

    def test_singleton(self):
        """测试单例模式"""
        # 清除全局变量
        import src.api.middleware.auth as auth_module
        original = auth_module._auth_service

        try:
            auth_module._auth_service = None

            with patch('src.api.middleware.auth.get_settings') as mock_settings:
                mock_settings.return_value.security.api_keys = []

                service1 = get_auth_service()
                service2 = get_auth_service()

                assert service1 is service2
        finally:
            auth_module._auth_service = original


class TestAPIKeyHeader:
    """APIKeyHeader 测试"""

    def test_header_creation(self):
        """测试请求头创建"""
        header = APIKeyHeader(name="Authorization", auto_error=False)
        # 验证创建成功
        assert header.auto_error is False

    def test_auto_error_false(self):
        """测试 auto_error 为 False"""
        header = APIKeyHeader(name="Authorization", auto_error=False)
        assert header.auto_error is False
