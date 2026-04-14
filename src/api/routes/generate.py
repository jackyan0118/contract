"""单文件生成接口."""

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.middleware.auth import verify_api_key
from src.api.schemas import (
    ApiResponse,
    ErrorCode,
    GenerateRequest,
    GenerateSuccessData,
    success_response,
)
from src.config.settings import get_settings
from src.exceptions import QueryException
from src.generators.document_generator import DocumentGenerator
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


async def _do_generate_document(
    request: GenerateRequest,
) -> ApiResponse[GenerateSuccessData]:
    """执行文档生成的内部逻辑"""
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
        quote_dict = asdict(quotation) if hasattr(quotation, "__dataclass_fields__") else quotation
        if quote_dict:
            quote_dict = {k.upper(): v for k, v in quote_dict.items()}

        details_dict = []
        for d in details:
            if hasattr(d, "__dataclass_fields__"):
                d_dict = asdict(d)
            else:
                d_dict = d
            # 将所有key转换为大写
            d_dict_upper = {k.upper(): v for k, v in d_dict.items()}
            details_dict.append(d_dict_upper)

        logger.info(f"明细数据字段: {list(details_dict[0].keys()) if details_dict else 'none'}")

        # 4. 按关键词组合分组明细数据
        rule_loader = RuleLoader()
        rules = rule_loader.load()
        logger.info(f"加载了 {len(rules)} 条模板规则")

        # 定义分组关键词提取函数
        def get_detail_key(d: dict) -> tuple:
            """从明细中提取关键词组合"""
            cpxf_bm = str(
                d.get("CPXF_BM") if d.get("CPXF_BM") is not None else d.get("cpxf_bm") or ""
            )
            djz = str(d.get("DJZ") if d.get("DJZ") is not None else d.get("djz") or "")
            sfjc = str(d.get("SFJC") if d.get("SFJC") is not None else d.get("sfjc") or "")
            bnghjlxz = str(
                d.get("BNGHJLXZ") if d.get("BNGHJLXZ") is not None else d.get("bnghjlxz") or ""
            )
            wldm = str(d.get("WLDM") if d.get("WLDM") is not None else d.get("wldm") or "")
            pp = str(d.get("PP") if d.get("PP") is not None else d.get("pp") or "")
            lyxh = str(d.get("LYXH") if d.get("LYXH") is not None else d.get("lyxh") or "")
            return (cpxf_bm, djz, sfjc, bnghjlxz, wldm, pp, lyxh)

        # 按关键词组合分组
        detail_groups: dict[tuple, list] = {}
        for d in details_dict:
            key = get_detail_key(d)
            if key not in detail_groups:
                detail_groups[key] = []
            detail_groups[key].append(d)

        logger.info(f"明细分组结果: {len(detail_groups)} 组")
        for key, group in detail_groups.items():
            logger.info(f"  组 {key}: {len(group)} 条明细")

        # 5. 为每个分组匹配模板并生成文档
        #    构建每个分组的匹配数据
        template_groups: list[tuple[TemplateRule, list[dict]]] = []

        for key, group_details in detail_groups.items():
            cpxf_bm, djz, sfjc, bnghjlxz, wldm, pp, lyxh = key

            # 为该组构建匹配数据
            match_data = {
                "产品细分编号": cpxf_bm,
                "定价组编号": djz,
                "是否集采": sfjc,
                "供货价类型": bnghjlxz,
                "物料代码": wldm,
                "品牌编号": pp,
                "物料生成来源": lyxh,
            }
            logger.info(f"匹配数据: {match_data}")

            # 查找匹配的模板
            for rule in rules:
                for cond in rule.条件:
                    if cond.match(match_data):
                        template_groups.append((rule, group_details))
                        logger.info(f"匹配成功: {rule.id} -> {len(group_details)} 条明细")
                        break

        logger.info(f"模板匹配结果: {len(template_groups)} 个模板")

        if not template_groups:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": ErrorCode.TEMPLATE_NOT_MATCHED,
                    "message": f"报价单 {wybs} 没有匹配的模板",
                },
            )

        # 去重（同一个模板可能匹配多个组，合并其明细）
        unique_templates: dict[str, tuple[TemplateRule, list[dict]]] = {}
        for rule, group_details in template_groups:
            if rule.id not in unique_templates:
                unique_templates[rule.id] = (rule, [])
            unique_templates[rule.id][1].extend(group_details)

        logger.info(f"去重后模板数: {len(unique_templates)}")

        # 6. 生成文档
        settings = get_settings()
        generator = DocumentGenerator(
            template_dir=settings.template.path,
            config_dir="config/template_metadata/templates",
        )

        results = []
        for _template_id, (template, template_details) in unique_templates.items():
            result = generator.generate(
                template=template,
                quote_data=quote_dict,
                detail_data_list=template_details,  # 只传对应模板的明细
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
        date_dir = datetime.now().strftime("%Y%m%d")
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
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
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
        # 使用请求值或settings中的默认值
        weaver_enabled = (
            request.weaver_enabled
            if request.weaver_enabled is not None
            else settings.weaver.enabled
        )
        if weaver_enabled:
            try:
                weaver_service = WeaverService(settings.weaver)
                # 使用请求值或settings中的默认值
                operator_id = request.weaver_operator_id or settings.weaver.operator_id
                weaver_result = await weaver_service.write_attachment(
                    jgqdbh=wybs,
                    file_url=full_download_url,
                    filename=Path(zip_path).name,
                    operator_id=operator_id,
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


@router.post("/generate", response_model=ApiResponse[GenerateSuccessData])
async def generate_document(
    request: GenerateRequest,
    user: str = Depends(verify_api_key),
) -> ApiResponse[GenerateSuccessData]:
    """单文件生成接口 (POST)

    根据报价单号生成价格附件文档，返回下载 URL 的 ZIP 压缩包。
    请求体格式: {"wybs": "xxx", "weaver_enabled": true, "weaver_operator_id": "xxx"}
    """
    return await _do_generate_document(request)


@router.get("/generate", response_model=ApiResponse[GenerateSuccessData])
async def generate_document_get(
    wybs: str = Query(
        ..., description="报价单号", min_length=1, max_length=50, pattern=r"^[A-Z0-9_-]+$"
    ),
    weaver_enabled: Optional[bool] = Query(None, description="是否启用OA回写"),
    weaver_operator_id: Optional[str] = Query(None, description="OA操作人ID"),
    user: str = Depends(verify_api_key),
) -> ApiResponse[GenerateSuccessData]:
    """单文件生成接口 (GET)

    根据报价单号生成价格附件文档，返回下载 URL 的 ZIP 压缩包。

    示例: /api/generate?wybs=XXXX&weaver_enabled=true&weaver_operator_id=5288
    """
    request = GenerateRequest(
        wybs=wybs,
        weaver_enabled=weaver_enabled,
        weaver_operator_id=weaver_operator_id,
    )
    return await _do_generate_document(request)
