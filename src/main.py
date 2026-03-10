"""FastAPI 应用入口."""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.middleware.cors import setup_cors
from src.api.middleware.error_handler import setup_error_handler
from src.api.middleware.logging import setup_logging
from src.api.middleware.rate_limit import setup_rate_limit
from src.api.router import api_router
from src.api.schemas import ApiResponse, ErrorCode
from src.config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("main")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title="价格附件生成系统 API",
        description="基于模板规则自动生成 Word 价格附件的 RESTful API",
        version=settings.app.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 配置中间件
    setup_cors(app)
    setup_logging(app)
    setup_error_handler(app)

    # 开发环境启用限流（生产环境建议使用 Redis 等分布式限流）
    if not settings.app.debug:
        setup_rate_limit(app)

    # 注册路由
    app.include_router(api_router)

    # 根路径
    @app.get("/", response_model=ApiResponse)
    async def root():
        return ApiResponse(
            success=True,
            data={
                "name": "价格附件生成系统 API",
                "version": settings.app.version,
                "docs": "/docs",
            },
        )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
    )
