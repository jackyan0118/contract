"""任务管理接口."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.middleware.auth import verify_api_key
from src.api.schemas import (
    ApiResponse,
    AsyncTaskData,
    ErrorCode,
    success_response,
)
from src.api.tasks import TaskStatus, get_task_manager
from src.utils.logger import get_logger

logger = get_logger("api.routes.tasks")

router = APIRouter()


@router.get("/api/v1/tasks/{task_id}", response_model=ApiResponse[AsyncTaskData])
async def get_task_status(
    task_id: str,
    user: str = Depends(verify_api_key),
) -> ApiResponse[AsyncTaskData]:
    """查询任务状态"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.TASK_NOT_FOUND,
                "message": f"任务不存在: {task_id}",
            },
        )

    # 获取结果
    results = []
    zip_base64 = None
    if task.status == TaskStatus.COMPLETED and task.results:
        for r in task.results:
            if isinstance(r, dict):
                results.append(r)
        # 检查最后的 result
        if task.results and isinstance(task.results[-1], dict):
            results = task.results[-1].get("results", results)
            zip_base64 = task.results[-1].get("zip_base64")

    data = AsyncTaskData(
        task_id=task.task_id,
        status=task.status.value,
        progress=task.processed * 100 // task.total if task.total > 0 else 0,
        total=task.total,
        processed=task.processed,
        failed=task.failed,
        created_at=task.created_at,
        completed_at=task.completed_at,
        results=results,
        zip_base64=zip_base64,
    )

    return success_response(data=data.model_dump())


@router.delete("/api/v1/tasks/{task_id}", response_model=ApiResponse)
async def cancel_task(
    task_id: str,
    user: str = Depends(verify_api_key),
) -> ApiResponse:
    """取消任务"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": ErrorCode.TASK_NOT_FOUND,
                "message": f"任务不存在: {task_id}",
            },
        )

    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.TASK_CANCELLED,
                "message": f"任务已完成或失败，无法取消",
            },
        )

    success = task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "取消任务失败",
            },
        )

    return success_response(
        data={"task_id": task_id, "status": "cancelled"},
        message="任务已取消",
    )
