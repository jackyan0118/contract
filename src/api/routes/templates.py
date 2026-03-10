"""模板列表查询接口."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from src.api.middleware.auth import verify_api_key
from src.api.schemas import ApiResponse, TemplateInfo, success_response
from src.config.template_loader import TemplateLoader
from src.utils.logger import get_logger

logger = get_logger("api.routes.templates")

router = APIRouter()

# 模板分类列表
CATEGORIES = [
    "集采产品",
    "酶免胶体金",
    "通用生化",
    "外购试剂",
]


@router.get("/api/v1/templates", response_model=ApiResponse[List[TemplateInfo]])
async def list_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    user: str = Depends(verify_api_key),
) -> ApiResponse[List[TemplateInfo]]:
    """模板列表查询接口

    返回系统中可用的模板列表，支持按分类筛选。
    """
    try:
        # 加载所有模板配置
        loader = TemplateLoader()
        templates = loader.load_all()

        # 筛选分类
        if category:
            templates = [t for t in templates if t.category == category]

        # 转换为响应模型
        template_infos = [
            TemplateInfo(
                id=t.id,
                name=t.name,
                category=t.category,
                file=t.file,
                match_conditions=t.match_conditions,
            )
            for t in templates
        ]

        return success_response(
            data=template_infos,
            message=f"找到 {len(template_infos)} 个模板",
        )

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        return success_response(data=[])
