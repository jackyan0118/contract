"""单文件生成接口."""

import io
from dataclasses import asdict

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


@router.post("/generate", response_model=ApiResponse[GenerateSuccessData])
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
        quote_dict = asdict(quotation) if hasattr(quotation, '__dataclass_fields__') else quotation
        details_dict = [asdict(d) if hasattr(d, '__dataclass_fields__') else d for d in details]

        logger.info(f"明细数据字段: {list(details_dict[0].keys()) if details_dict else 'none'}")

        # 从明细数据中提取产品细分等信息用于模板匹配
        if details_dict:
            # 获取唯一的产品细分信息
            cpxf_ids = set()  # UF_CPXF表的ID（如150）
            djzmc_values = set()

            for d in details_dict:
                # CPXF - 原始字段，存储的是UF_CPXF表的ID
                cpxf_id = d.get('CPXF') or d.get('cpxf')
                if cpxf_id:
                    cpxf_ids.add(str(cpxf_id))

                # DJZMC - 等级名称（定价组）
                djzmc = d.get('DJZMC') or d.get('djzmc')
                if djzmc:
                    djzmc_values.add(djzmc)

            logger.info(f"CPXF_IDS: {cpxf_ids}, DJZMC_COUNT: {len(djzmc_values)}")

            # 从UF_CPXF表查询产品细分名称
            cpxf_name = None
            if cpxf_ids:
                cpxf_id = list(cpxf_ids)[0]
                try:
                    from src.database import get_connection_pool
                    pool = get_connection_pool()
                    with pool.connection() as conn:
                        with conn.cursor() as cursor:
                            # 查询UF_CPXF表获取产品细分名称
                            cursor.execute(
                                "SELECT CPXF FROM ecology.UF_CPXF WHERE ID = :id",
                                {"id": int(cpxf_id)}
                            )
                            row = cursor.fetchone()
                            if row:
                                cpxf_name = str(row[0])
                                logger.info(f"查询到CPXF名称: {cpxf_name}")
                except Exception as e:
                    logger.warning(f"查询UF_CPXF表失败: {e}")

            # 产品细分名称到编号的映射（从测试脚本获取）
            cpxf_name_to_bm = {
                "酶免试剂": "11",
                "胶体金试剂": "41",
                "通用生化试剂": "21",
                "卓越生化试剂": "22",
                "化学发光试剂": "12",
                "北极星发光试剂": "14",
                "日立008试剂": "23",
                "北极星生化试剂": "24",
                "第三方试剂": "102",
            }

            # 设置产品细分名称和编号
            if cpxf_name:
                quote_dict['产品细分'] = cpxf_name
                if cpxf_name in cpxf_name_to_bm:
                    quote_dict['产品细分编号'] = cpxf_name_to_bm[cpxf_name]

            # DJZMC就是定价组名称
            if djzmc_values:
                quote_dict['定价组名称'] = list(djzmc_values)[0]

            # 是否集采字段（从主表或明细中获取）
            # 这里假设默认为非集采
            quote_dict['是否集采'] = '1'

        logger.info(f"报价单数据: {quote_dict}")
        logger.info(f"明细数据条数: {len(details_dict)}")

        # 4. 匹配模板 - 使用更灵活的匹配逻辑
        rule_loader = RuleLoader()
        rules = rule_loader.load()
        logger.info(f"加载了 {len(rules)} 条模板规则")

        # 简单匹配：只检查产品细分编号是否匹配
        matched_templates = []
        for rule in rules:
            for cond in rule.条件:
                # 只检查产品细分编号是否匹配
                if cond.产品细分编号 and str(cond.产品细分编号) == str(quote_dict.get('产品细分编号')):
                    matched_templates.append(rule)
                    logger.info(f"匹配成功: {rule.id}")
                    break

        logger.info(f"匹配结果: count={len(matched_templates)}")

        if not matched_templates:
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
        for template in matched_templates:
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
