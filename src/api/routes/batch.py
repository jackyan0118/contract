"""批量生成接口."""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.api.dependencies.file import get_output_dir, read_file_as_base64
from src.api.middleware.auth import verify_api_key
from src.api.schemas import (
    ApiResponse,
    BatchRequest,
    BatchResultItem,
    BatchSuccessData,
    ErrorCode,
    error_response,
    success_response,
)
from src.api.tasks import TaskStatus, get_task_manager
from src.config.settings import get_settings
from src.exceptions import QueryException
from src.generators.document_generator import DocumentGenerator
from src.matchers.template_matcher import TemplateMatcher
from src.queries.quotation import get_quotation_by_wybs
from src.queries.quotation_detail import get_quotation_details
from src.services.rule_loader import RuleLoader
from src.transformers.data_transformer import get_transformer
from src.utils.file_packer import pack_files_to_base64_zip
from src.utils.logger import get_logger

logger = get_logger("api.routes.batch")

router = APIRouter()


def process_batch_task(task_id: str, wybs_list: List[str]) -> None:
    """处理批量生成任务（后台运行）"""
    task_manager = get_task_manager()
    settings = get_settings()

    # 更新任务状态
    task_manager.update_task(task_id, status=TaskStatus.PROCESSING, processed=0)

    generator = DocumentGenerator(
        template_dir=settings.template.path,
        config_dir="config/template_metadata/templates",
    )
    rule_loader = RuleLoader()
    rules = rule_loader.load_rules()
    matcher = TemplateMatcher(rules)
    transformer = get_transformer()

    all_results = []
    total = len(wybs_list)
    processed = 0
    failed = 0

    for wybs in wybs_list:
        try:
            # 查询数据
            quote_data = get_quotation_by_wybs(wybs)
            if not quote_data:
                result = BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="报价单不存在",
                )
                failed += 1
                all_results.append(result.model_dump())
                task_manager.update_task(task_id, processed=processed + 1, failed=failed)
                continue

            # 查询明细
            detail_data_list = get_quotation_details(wybs)

            # 转换数据
            quotation = transformer.transform_quotation(quote_data)
            details = transformer.transform_quotation_details(detail_data_list)
            quote_dict = quotation.model_dump()
            details_dict = [d.model_dump() for d in details]

            # 匹配模板
            match_result = matcher.match(quote_dict)
            if not match_result.success or not match_result.templates:
                result = BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="无匹配模板",
                )
                failed += 1
                all_results.append(result.model_dump())
                task_manager.update_task(task_id, processed=processed + 1, failed=failed)
                continue

            # 生成文档
            file_paths = []
            for template in match_result.templates:
                gen_result = generator.generate(
                    template=template,
                    quote_data=quote_dict,
                    detail_data_list=details_dict,
                    output_dir=settings.template.output_dir,
                )
                if gen_result.success and gen_result.file_path:
                    file_paths.append({
                        "filename": gen_result.file_path.split("/")[-1],
                        "base64": read_file_as_base64(gen_result.file_path),
                    })

            if file_paths:
                result = BatchResultItem(
                    wybs=wybs,
                    files=file_paths,
                    success=True,
                    error=None,
                )
            else:
                result = BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="文档生成失败",
                )
                failed += 1

            all_results.append(result.model_dump())

        except Exception as e:
            logger.error(f"Failed to process {wybs}: {e}")
            result = BatchResultItem(
                wybs=wybs,
                files=[],
                success=False,
                error=str(e),
            )
            failed += 1
            all_results.append(result.model_dump())

        processed += 1
        task_manager.update_task(task_id, processed=processed, failed=failed)

    # 生成 ZIP 包
    all_files = []
    for r in all_results:
        if r.get("success"):
            for f in r.get("files", []):
                # 需要保存临时文件再打包
                import tempfile
                import os
                from pathlib import Path

                # 保存临时文件
                temp_dir = Path("/tmp/price_attachments")
                temp_dir.mkdir(parents=True, exist_ok=True)

                from base64 import b64decode

                file_path = temp_dir / f["filename"]
                with open(file_path, "wb") as fp:
                    fp.write(b64decode(f["base64"]))
                all_files.append(str(file_path))

    zip_base64 = None
    if all_files:
        zip_base64 = pack_files_to_base64_zip(all_files)

    # 清理临时文件
    for file_path in all_files:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    # 更新任务完成
    task_manager.update_task(
        task_id,
        status=TaskStatus.COMPLETED,
        processed=total,
        failed=failed,
        result={"results": all_results, "zip_base64": zip_base64},
    )


@router.post("/api/v1/batch", response_model=ApiResponse)
async def batch_generate(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
    user: str = Depends(verify_api_key),
) -> ApiResponse:
    """批量生成接口

    根据报价单号列表批量生成价格附件文档。
    支持同步和异步两种模式。
    """
    wybs_list = request.wybs_list

    # 小于10个采用同步模式
    if not request.is_async and len(wybs_list) < 10:
        return await _process_sync(wybs_list, user)

    # 大于等于10个或明确要求异步，采用异步模式
    task_manager = get_task_manager()
    task = task_manager.create_task(total=len(wybs_list))

    # 启动后台任务
    background_tasks.add_task(process_batch_task, task.task_id, wybs_list)

    from src.api.schemas import AsyncTaskData

    data = AsyncTaskData(
        task_id=task.task_id,
        status=task.status.value,
        total=task.total,
    )

    return success_response(
        data=data.model_dump(),
        message="任务已创建",
    )


async def _process_sync(wybs_list: List[str], user: str) -> ApiResponse:
    """同步处理批量生成"""
    settings = get_settings()
    generator = DocumentGenerator(
        template_dir=settings.template.path,
        config_dir="config/template_metadata/templates",
    )
    rule_loader = RuleLoader()
    rules = rule_loader.load_rules()
    matcher = TemplateMatcher(rules)
    transformer = get_transformer()

    results = []
    all_files = []

    for wybs in wybs_list:
        try:
            # 查询数据
            quote_data = get_quotation_by_wybs(wybs)
            if not quote_data:
                results.append(BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="报价单不存在",
                ))
                continue

            # 查询明细
            detail_data_list = get_quotation_details(wybs)

            # 转换数据
            quotation = transformer.transform_quotation(quote_data)
            details = transformer.transform_quotation_details(detail_data_list)
            quote_dict = quotation.model_dump()
            details_dict = [d.model_dump() for d in details]

            # 匹配模板
            match_result = matcher.match(quote_dict)
            if not match_result.success or not match_result.templates:
                results.append(BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="无匹配模板",
                ))
                continue

            # 生成文档
            file_paths = []
            files_info = []
            for template in match_result.templates:
                gen_result = generator.generate(
                    template=template,
                    quote_data=quote_dict,
                    detail_data_list=details_dict,
                    output_dir=settings.template.output_dir,
                )
                if gen_result.success and gen_result.file_path:
                    file_base64 = read_file_as_base64(gen_result.file_path)
                    filename = gen_result.file_path.split("/")[-1]
                    file_paths.append(gen_result.file_path)
                    files_info.append({"filename": filename, "base64": file_base64})
                    all_files.append(gen_result.file_path)

            if files_info:
                results.append(BatchResultItem(
                    wybs=wybs,
                    files=files_info,
                    success=True,
                    error=None,
                ))
            else:
                results.append(BatchResultItem(
                    wybs=wybs,
                    files=[],
                    success=False,
                    error="文档生成失败",
                ))

        except Exception as e:
            logger.error(f"Failed to process {wybs}: {e}")
            results.append(BatchResultItem(
                wybs=wybs,
                files=[],
                success=False,
                error=str(e),
            ))

    # 打包 ZIP
    zip_base64 = None
    if all_files:
        zip_base64 = pack_files_to_base64_zip(all_files)

    # 清理临时文件（生成的文档保留在 output 目录，只清理临时文件）
    for file_path in all_files:
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

    data = BatchSuccessData(
        status="completed",
        results=[r.model_dump() for r in results],
        zip_base64=zip_base64,
    )

    return success_response(
        data=data.model_dump(),
        message=f"完成，成功 {sum(1 for r in results if r.success)} 个",
    )
