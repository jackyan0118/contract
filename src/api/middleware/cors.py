"""CORS 中间件配置."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import get_settings


def setup_cors(app: FastAPI) -> None:
    """配置 CORS 中间件"""
    settings = get_settings()

    # 生产环境应配置具体的允许来源
    if settings.app.debug:
        # 开发环境允许所有来源
        allow_origins = ["*"]
        allow_credentials = True
    else:
        # 生产环境从配置读取（默认只允许本域）
        allow_origins = getattr(settings.security, "cors_origins", None) or ["/"]
        allow_credentials = False

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
