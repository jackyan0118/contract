"""API 请求和响应模型定义."""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ErrorCode(str, Enum):
    """API 错误码"""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    TEMPLATE_NOT_MATCHED = "TEMPLATE_NOT_MATCHED"
    GENERATION_FAILED = "GENERATION_FAILED"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_CANCELLED = "TASK_CANCELLED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED = "UNAUTHORIZED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """错误详情"""

    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""

    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    message: Optional[str] = None
    request_id: Optional[str] = None


# ============ 请求模型 ============


class GenerateRequest(BaseModel):
    """单文件生成请求"""

    wybs: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Z0-9_-]+$",
        description="报价单号",
    )

    @field_validator("wybs")
    @classmethod
    def validate_wybs(cls, v: str) -> str:
        if not v:
            raise ValueError("报价单号不能为空")
        return v.strip().upper()


class BatchRequest(BaseModel):
    """批量生成请求"""

    wybs_list: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="报价单号列表",
    )
    is_async: bool = Field(default=False, description="是否异步处理")

    @field_validator("wybs_list")
    @classmethod
    def validate_wybs_list(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("报价单号列表不能为空")
        # 去重
        unique_list = list(dict.fromkeys(v))
        if len(unique_list) != len(v):
            raise ValueError("报价单号列表中存在重复项")
        # 验证每个元素
        for item in unique_list:
            if not re.match(r"^[A-Z0-9_-]+$", item):
                raise ValueError(f"报价单号格式错误: {item}")
        return [item.strip().upper() for item in unique_list]


# ============ 响应模型 ============


class HealthStatusData(BaseModel):
    """健康检查数据"""

    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


class TemplateInfo(BaseModel):
    """模板信息"""

    id: str
    name: str
    category: str
    file: str
    match_conditions: Dict[str, Any] = Field(default_factory=dict)


class GenerateSuccessData(BaseModel):
    """单文件生成成功数据"""

    download_url: str
    filename: str
    file_count: int
    expires_in: int
    templates_used: List[str] = Field(default_factory=list)


class BatchResultItem(BaseModel):
    """批量生成单条结果"""

    wybs: str
    files: List[Dict[str, str]] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None


class BatchSuccessData(BaseModel):
    """批量生成成功数据"""

    status: str  # "completed" or "processing"
    results: List[BatchResultItem] = Field(default_factory=list)
    zip_base64: Optional[str] = None


class AsyncTaskData(BaseModel):
    """异步任务数据"""

    task_id: str
    status: str
    progress: Optional[int] = None
    total: Optional[int] = None
    processed: Optional[int] = None
    failed: Optional[int] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: List[BatchResultItem] = Field(default_factory=list)
    zip_base64: Optional[str] = None


# ============ 辅助函数 ============


def success_response(data: T, message: Optional[str] = None, request_id: Optional[str] = None) -> ApiResponse[T]:
    """创建成功响应"""
    return ApiResponse(success=True, data=data, message=message, request_id=request_id)


def error_response(code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None) -> ApiResponse:
    """创建错误响应"""
    return ApiResponse(
        success=False,
        error=ErrorDetail(code=code, message=message, details=details),
        request_id=request_id,
    )
