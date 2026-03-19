"""单文件生成接口."""

import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies.file import get_output_dir
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
from src.exceptions.document import DiskSpaceException
from src.generators.document_generator import DocumentGenerator
from src.matchers.template_matcher import TemplateMatcher
from src.models.template_rule import TemplateRule
from src.queries.quotation import get_quotation_by_wybs
from src.queries.quotation_detail import get_quotation_details
from src.services.rule_loader import RuleLoader
from src.services.weaver_service import WeaverService
from src.transformers.data_transformer import get_transformer
from src.utils.file_packer import FilePacker
from src.utils.file_cleaner import FileCleaner
from src.utils.logger import get_logger

logger = get_logger("api.routes.generate")

router = APIRouter()


@router.post("/generate", response_model=ApiResponse[GenerateSuccessData])
async def generate_document(
    request: GenerateRequest,
    user: str = Depends(verify_api_key),
) -> ApiResponse[GenerateSuccessData]:
    """单文件生成接口

    根据报价单号生成价格附件文档，返回下载 URL 的 ZIP 压缩包。
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
        # 将所有key转换为大写，与模板配置保持一致
        quote_dict = asdict(quotation) if hasattr(quotation, '__dataclass_fields__') else quotation
        if quote_dict:
            quote_dict = {k.upper(): v for k, v in quote_dict.items()}

        details_dict = []
        for d in details:
            if hasattr(d, '__dataclass_fields__'):
                d_dict = asdict(d)
            else:
                d_dict = d
            # 将所有key转换为大写
            d_dict_upper = {k.upper(): v for k, v in d_dict.items()}
            details_dict.append(d_dict_upper)

        logger.info(f"明细数据字段: {list(details_dict[0].keys()) if details_dict else 'none'}")

        # 从明细数据中提取产品细分等信息用于模板匹配
        if details_dict:
            # 获取唯一的产品细分信息
            # CPXF_BM: 产品细分BM编码（如"22"），直接从明细SQL关联查询获取
            cpxf_bm_values = set()
            djzmc_values = set()
            cpxf_name = None  # 产品细分名称

            for d in details_dict:
                # CPXF_BM - 产品细分BM编码，直接从SQL关联查询获取
                cpxf_bm = d.get('CPXF_BM') or d.get('cpxf_bm')
                if cpxf_bm:
                    cpxf_bm_values.add(str(cpxf_bm))

                # CPXF_NAME - 产品细分名称，也从SQL关联查询获取
                cpxf_name = d.get('CPXF_NAME') or d.get('cpxf_name')

                # DJZMC - 等级名称（定价组）
                djzmc = d.get('DJZMC') or d.get('djzmc')
                if djzmc:
                    djzmc_values.add(djzmc)

            logger.info(f"CPXF_BM: {cpxf_bm_values}, DJZMC_COUNT: {len(djzmc_values)}")

            # 设置产品细分名称和编号（直接从明细数据获取，无需额外查询和映射）
            if cpxf_name:
                quote_dict['产品细分'] = cpxf_name
            if cpxf_bm_values:
                quote_dict['产品细分编号'] = list(cpxf_bm_values)[0]

            # DJZMC就是定价组名称
            if djzmc_values:
                quote_dict['定价组名称'] = list(djzmc_values)[0]

            # 是否集采字段（从明细数据中获取 SFJC）
            # SFJC: 0=是（集采），1=否（非集采）
            sfjc_value = None
            for d in details_dict:
                sfjc = d.get('SFJC') or d.get('sfjc')
                if sfjc is not None:
                    sfjc_value = str(sfjc)
                    break
            # 如果明细中没有，则默认为非集采
            quote_dict['是否集采'] = sfjc_value if sfjc_value is not None else '1'

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
                wybs=wybs,
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

        # 6. 打包成 ZIP
        settings = get_settings()

        # 使用配置中的下载目录
        downloads_dir = Path(settings.downloads.storage_dir)
        downloads_dir.mkdir(parents=True, exist_ok=True)

        # 按日期组织子目录
        date_dir = datetime.now().strftime('%Y%m%d')
        full_download_dir = downloads_dir / date_dir
        full_download_dir.mkdir(parents=True, exist_ok=True)

        # 检查磁盘空间
        cleaner = FileCleaner(storage_dir=str(downloads_dir))
        if cleaner.is_disk_space_low(threshold=settings.downloads.disk_space_threshold):
            raise HTTPException(
                status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                detail={
                    "code": ErrorCode.DISK_SPACE_ERROR,
                    "message": f"磁盘空间不足，当前已超过 {settings.downloads.disk_space_threshold}%",
                },
            )

        # 生成 ZIP 文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        zip_filename = f"{wybs}_{timestamp}"
        zip_output_dir = str(full_download_dir)

        # 打包文件
        packer = FilePacker(output_dir=zip_output_dir)
        zip_path = packer.pack(successful_files, zip_filename)

        # 生成相对路径和完整URL
        relative_path = f"{date_dir}/{Path(zip_path).name}"
        download_url = f"{settings.downloads.url_path}/{relative_path}"
        full_download_url = f"{settings.downloads.base_url}{download_url}"

        # OA回写（如果启用）
        weaver_result = None
        if request.weaver_enabled:
            try:
                weaver_service = WeaverService(settings.weaver)
                weaver_result = await weaver_service.write_attachment(
                    jgqdbh=wybs,
                    file_url=full_download_url,
                    filename=Path(zip_path).name,
                    operator_id=request.weaver_operator_id
                )
                await weaver_service.close()

                if not weaver_result.get("success"):
                    logger.warning(f"OA回写失败: {weaver_result.get('message')}")
                else:
                    logger.info(f"OA回写成功: billid={weaver_result.get('billid')}")
            except Exception as e:
                logger.error(f"OA回写异常: {e}")

        # 返回数据
        data = GenerateSuccessData(
            download_url=full_download_url,
            filename=Path(zip_path).name,
            file_count=len(successful_files),
            expires_in=settings.downloads.expires_in,
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
