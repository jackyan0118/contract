"""API 路由注册."""

from fastapi import APIRouter

from src.api.routes import batch, generate, health, tasks, templates

api_router = APIRouter(prefix="/api/v1")

# 注册路由
api_router.include_router(health.router, tags=["health"])
api_router.include_router(templates.router, tags=["templates"])
api_router.include_router(generate.router, tags=["generate"])
api_router.include_router(batch.router, tags=["batch"])
api_router.include_router(tasks.router, tags=["tasks"])
