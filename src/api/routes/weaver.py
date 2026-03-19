"""
泛微OA集成API路由
"""

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.middleware.auth import verify_api_key
from src.api.schemas import ApiResponse
from src.config.settings import Settings, get_settings
from src.services.weaver_service import WeaverService

router = APIRouter(prefix="/weaver", tags=["weaver"])


class WeaverStatusData(BaseModel):
    """OA状态数据"""
    connected: bool = False
    host: str = ""
    message: str = ""


class WeaverValidateData(BaseModel):
    """OA验证数据"""
    success: bool
    message: str = ""


@router.get("/status", response_model=ApiResponse[WeaverStatusData])
async def get_status(
    settings: Settings = Depends(get_settings),
    user: str = Depends(verify_api_key)
) -> ApiResponse[WeaverStatusData]:
    """获取OA连接状态"""
    service = WeaverService(settings.weaver)
    result = await service.test_connection()
    await service.close()

    return ApiResponse(
        success=result.get("success", False),
        data=WeaverStatusData(
            connected=result.get("success", False),
            host=result.get("host", ""),
            message=result.get("message", "")
        )
    )


@router.post("/validate", response_model=ApiResponse[WeaverValidateData])
async def validate_connection(
    settings: Settings = Depends(get_settings),
    user: str = Depends(verify_api_key)
) -> ApiResponse[WeaverValidateData]:
    """测试OA连接"""
    service = WeaverService(settings.weaver)
    result = await service.test_connection()
    await service.close()

    return ApiResponse(
        success=result.get("success", False),
        data=WeaverValidateData(
            success=result.get("success", False),
            message=result.get("message", "")
        )
    )
