"""单文件生成接口."""

import io

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.file import get_output_dir, read_file_as_base64
from src.api.middleware.auth import verify_api_key
from src.api.schemas import (
    ApiResponse,
    ErrorCode,
    GenerateRequest,
    GenerateSuccessData,
    error_response,
    success_response,
)
from src.config.settings import get_settings
from src.exceptions import QueryException
from src.generators.document_generator import DocumentGenerator
from src.matchers.template_matcher import TemplateMatcher
from src.models.template_rule import TemplateRule
from src.queries.quotation import get_quotation_by_wybs
from src.queries.quotation_detail import get_quotation_details
from src.services.rule_loader import RuleLoader
from src.transformers.data_transformer import get_transformer
from src.utils.logger import get_logger

logger = get_logger("api.routes.generate")

router = APIRouter()


@router.post("/api/v1/generate", response_model=ApiResponse[GenerateSuccessData])
async def generate_document(
    request: GenerateRequest,
    user: str = Depends(verify_api_key),
) -> ApiResponse[GenerateSuccessData]:
    """单文件生成接口

    根据报价单号生成价格附件文档，返回 Base64 编码的 Word 文件。
    """
    wybs = request.wybs

    try:
        # 1. 查询报价单数据
        quote_data = get_quotation_by_wybs(wybs)
        if not quote_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": ErrorCode.QUOTE_NOT_FOUND,
                    "message": f"报价单不存在: {wybs}",
                },
            )

        # 2. 查询明细数据
        detail_data_list = get_quotation_details(wybs)

        # 3. 转换数据
        transformer = get_transformer()
        quotation = transformer.transform_quotation(quote_data)
        details = transformer.transform_quotation_details(detail_data_list)

        # 转换为字典格式供模板匹配使用
        quote_dict = quotation.model_dump()
        details_dict = [d.model_dump() for d in details]

        # 4. 匹配模板
        rule_loader = RuleLoader()
        rules = rule_loader.load_rules()
        matcher = TemplateMatcher(rules)
        match_result = matcher.match(quote_dict)

        if not match_result.success or not match_result.templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": ErrorCode.TEMPLATE_NOT_MATCHED,
                    "message": f"报价单 {wybs} 没有匹配的模板",
                },
            )

        # 5. 生成文档
        settings = get_settings()
        generator = DocumentGenerator(
            template_dir=settings.template.path,
            config_dir="config/template_metadata/templates",
        )

        results = []
        for template in match_result.templates:
            result = generator.generate(
                template=template,
                quote_data=quote_dict,
                detail_data_list=details_dict,
                output_dir=settings.template.output_dir,
            )
            results.append(result)

        # 收集成功的文件
        successful_files = []
        template_ids = []

        for result in results:
            if result.success and result.file_path:
                successful_files.append(result.file_path)
                template_ids.append(result.template_id)
            else:
                logger.warning(f"Failed to generate {result.template_id}: {result.error}")

        if not successful_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": ErrorCode.GENERATION_FAILED,
                    "message": "文档生成失败",
                },
            )

        # 6. 返回第一个文件（如果有多个模板，只返回第一个）
        # TODO: 如果有多个文件，可以打包成 ZIP
        first_file = successful_files[0]
        file_base64 = read_file_as_base64(first_file)

        # 生成文件名
        import os
        from datetime import datetime

        filename = os.path.basename(first_file)

        data = GenerateSuccessData(
            filename=filename,
            file_base64=file_base64,
            templates_used=template_ids,
        )

        return success_response(
            data=data,
            message=f"成功生成 {len(successful_files)} 个文档",
        )

    except HTTPException:
        raise
    except QueryException as e:
        logger.error(f"Query failed for {wybs}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.QUOTE_NOT_FOUND,
                "message": f"报价单不存在: {wybs}",
            },
        )
    except Exception as e:
        logger.error(f"Generate failed for {wybs}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.GENERATION_FAILED,
                "message": "文档生成失败，请稍后重试",
            },
        )
