"""FastAPI 应用入口."""

import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.middleware.cors import setup_cors
from src.api.middleware.error_handler import setup_error_handler
from src.api.middleware.logging import setup_logging
from src.api.middleware.rate_limit import setup_rate_limit
from src.api.router import api_router
from src.api.schemas import ApiResponse, ErrorCode
from src.config.settings import get_settings
from src.database.connection import get_connection_pool
from src.utils.file_cleaner import run_cleanup
from src.utils.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    settings = get_settings()

    # 启动时初始化数据库连接池
    logger.info("正在初始化数据库连接池...")
    pool = get_connection_pool()
    pool.initialize()
    logger.info("数据库连接池初始化完成")

    # 启动时清理过期文件
    if settings.downloads.auto_cleanup:
        logger.info("正在清理过期下载文件...")
        try:
            result = run_cleanup(
                storage_dir=settings.downloads.storage_dir,
                expires_in=settings.downloads.expires_in,
                threshold=settings.downloads.disk_space_threshold,
            )
            logger.info(f"清理完成: 删除 {result.deleted_count} 个过期文件")
        except Exception as e:
            logger.warning(f"清理过期文件失败: {e}")

    yield
    # 关闭时清理资源
    logger.info("正在关闭应用...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title="价格附件生成系统 API",
        description="基于模板规则自动生成 Word 价格附件的 RESTful API",
        version=settings.app.version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
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

    # 配置静态文件服务（下载目录）
    downloads_dir = Path(settings.downloads.storage_dir)
    if downloads_dir.exists():
        app.mount(
            settings.downloads.url_path,
            StaticFiles(directory=str(downloads_dir)),
            name="downloads",
        )
        logger.info(f"静态文件服务已启动: {settings.downloads.url_path} -> {downloads_dir}")
    else:
        logger.warning(f"下载目录不存在，跳过静态文件配置: {downloads_dir}")

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
