"""API Key 认证中间件."""

import secrets
from threading import Lock
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("api.middleware.auth")

# API Key 请求头
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)


class AuthService:
    """认证服务"""

    def __init__(self):
        self._valid_keys: set = set()
        self._load_keys()

    def _load_keys(self):
        """从配置加载有效的 API Key"""
        settings = get_settings()
        for key_config in settings.security.api_keys:
            if key_config.get("enabled", True):
                key = key_config.get("key", "")
                if key:
                    self._valid_keys.add(key)
        logger.info(f"Loaded {len(self._valid_keys)} API keys")

    def validate_key(self, api_key: Optional[str]) -> bool:
        """验证 API Key（常量时间比较，防止时间攻击）"""
        if not api_key:
            return False
        # 支持 Bearer 格式
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]
        # 使用常量时间比较防止时间攻击
        return any(secrets.compare_digest(api_key, key) for key in self._valid_keys)


# 全局认证服务
_auth_service: Optional[AuthService] = None
_auth_lock = Lock()


def get_auth_service() -> AuthService:
    """获取认证服务（线程安全）"""
    global _auth_service
    if _auth_service is None:
        with _auth_lock:
            if _auth_service is None:
                _auth_service = AuthService()
    return _auth_service


async def verify_api_key(request: Request, authorization: Optional[str] = Depends(API_KEY_HEADER)) -> str:
    """验证 API Key 依赖"""
    settings = get_settings()

    # API 认证未启用时跳过验证
    if not settings.security.enabled:
        return "auth_disabled_user"

    # Debug 模式下跳过认证（仅用于开发调试）
    if settings.app.debug:
        return "debug_user"

    # 生产环境必须配置 API Key
    if not settings.security.api_keys:
        logger.error("生产环境未配置 API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "服务器配置错误：未设置 API Key"},
        )

    auth_service = get_auth_service()
    if not auth_service.validate_key(authorization):
        logger.warning(f"Invalid API key: {authorization}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "无效的 API Key"},
        )

    # 返回用户标识
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization or "unknown"


async def get_optional_api_key(request: Request, authorization: Optional[str] = Depends(API_KEY_HEADER)) -> Optional[str]:
    """可选的 API Key 验证（健康检查等公开接口不需要认证）"""
    if not authorization:
        return None

    auth_service = get_auth_service()
    if not auth_service.validate_key(authorization):
        return None

    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization
