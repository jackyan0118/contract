"""健康检查接口."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends

from src.api.middleware.auth import get_optional_api_key
from src.api.schemas import (
    ApiResponse,
    HealthStatusData,
    success_response,
)
from src.config.settings import get_settings
from src.database.health import check_database_health
from src.utils.logger import get_logger

logger = get_logger("api.routes.health")

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthStatusData])
async def health_check(user: str = Depends(get_optional_api_key)) -> ApiResponse[HealthStatusData]:
    """健康检查接口

    检查系统各组件状态：
    - 数据库连接
    - 模板文件目录
    - 配置加载
    """
    settings = get_settings()

    # 检查服务状态
    services = {}

    # 检查数据库
    try:
        db_health = check_database_health()
        services["database"] = "connected" if db_health.healthy else "disconnected"
    except Exception:
        services["database"] = "error"

    # 检查模板目录
    template_path = Path(settings.template.path)
    services["templates"] = "exists" if template_path.exists() else "missing"

    # 检查输出目录
    output_path = Path(settings.template.output_dir)
    services["output"] = "writable" if output_path.exists() or output_path.mkdir(parents=True, exist_ok=True) else "error"

    # 判断整体状态
    all_healthy = all(
        status in ("connected", "exists", "writable")
        for status in services.values()
    )

    data = HealthStatusData(
        status="healthy" if all_healthy else "degraded",
        version=settings.app.version,
        timestamp=datetime.now(),
        services=services,
    )

    return success_response(data=data)
