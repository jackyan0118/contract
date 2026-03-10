"""API Schemas 单元测试."""

import pytest
from datetime import datetime
from src.api.schemas import (
    ErrorCode,
    ErrorDetail,
    ApiResponse,
    GenerateRequest,
    BatchRequest,
    HealthStatusData,
    TemplateInfo,
    GenerateSuccessData,
    BatchResultItem,
    BatchSuccessData,
    AsyncTaskData,
    success_response,
    error_response,
)


class TestErrorCode:
    """ErrorCode 枚举测试"""

    def test_error_codes(self):
        """测试错误码定义"""
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.QUOTE_NOT_FOUND.value == "QUOTE_NOT_FOUND"
        assert ErrorCode.TEMPLATE_NOT_MATCHED.value == "TEMPLATE_NOT_MATCHED"
        assert ErrorCode.GENERATION_FAILED.value == "GENERATION_FAILED"
        assert ErrorCode.TASK_NOT_FOUND.value == "TASK_NOT_FOUND"
        assert ErrorCode.TASK_CANCELLED.value == "TASK_CANCELLED"
        assert ErrorCode.RATE_LIMIT_EXCEEDED.value == "RATE_LIMIT_EXCEEDED"
        assert ErrorCode.UNAUTHORIZED.value == "UNAUTHORIZED"
        assert ErrorCode.PERMISSION_DENIED.value == "PERMISSION_DENIED"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"


class TestErrorDetail:
    """ErrorDetail 测试"""

    def test_error_detail_creation(self):
        """测试错误详情创建"""
        detail = ErrorDetail(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数错误",
            details={"field": "wybs"},
        )

        assert detail.code == ErrorCode.VALIDATION_ERROR
        assert detail.message == "参数错误"
        assert detail.details == {"field": "wybs"}

    def test_error_detail_optional_details(self):
        """测试可选 details"""
        detail = ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="内部错误",
        )

        assert detail.details is None


class TestApiResponse:
    """ApiResponse 泛型测试"""

    def test_response_with_data(self):
        """测试带数据的响应"""
        data = {"key": "value"}
        response = ApiResponse(success=True, data=data)

        assert response.success is True
        assert response.data == data
        assert response.error is None

    def test_response_with_error(self):
        """测试带错误的响应"""
        error = ErrorDetail(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数错误"
        )
        response = ApiResponse(success=False, error=error)

        assert response.success is False
        assert response.error == error
        assert response.data is None


class TestGenerateRequest:
    """GenerateRequest 测试"""

    def test_valid_wybs(self):
        """测试有效报价单号"""
        request = GenerateRequest(wybs="20240301001")
        assert request.wybs == "20240301001"

    def test_wybs_uppercase(self):
        """测试自动转大写"""
        request = GenerateRequest(wybs="ABC123")
        assert request.wybs == "ABC123"

    def test_wybs_with_underscore(self):
        """测试带下划线的报价单号"""
        request = GenerateRequest(wybs="WYBS_2024")
        assert request.wybs == "WYBS_2024"

    def test_wybs_with_hyphen(self):
        """测试带连字符的报价单号"""
        request = GenerateRequest(wybs="WYBS-2024-001")
        assert request.wybs == "WYBS-2024-001"

    def test_invalid_wybs_special_chars(self):
        """测试无效报价单号（特殊字符）"""
        with pytest.raises(ValueError):
            GenerateRequest(wybs="abc@123")

    def test_invalid_wybs_spaces(self):
        """测试无效报价单号（空格）"""
        with pytest.raises(ValueError):
            GenerateRequest(wybs="abc 123")

    def test_wybs_max_length(self):
        """测试最大长度"""
        with pytest.raises(ValueError):
            GenerateRequest(wybs="A" * 51)


class TestBatchRequest:
    """BatchRequest 测试"""

    def test_valid_batch_request(self):
        """测试有效批量请求"""
        request = BatchRequest(
            wybs_list=["20240301001", "20240301002"],
            is_async=True
        )

        assert len(request.wybs_list) == 2
        assert request.is_async is True

    def test_batch_request_duplication_error(self):
        """测试重复项报错"""
        with pytest.raises(ValueError, match="重复项"):
            BatchRequest(
                wybs_list=["20240301001", "20240301001", "20240301002"]
            )

    def test_batch_request_uppercase(self):
        """测试自动转大写"""
        request = BatchRequest(wybs_list=["ABC", "DEF"])
        assert request.wybs_list == ["ABC", "DEF"]

    def test_empty_list_invalid(self):
        """测试空列表无效"""
        with pytest.raises(ValueError):
            BatchRequest(wybs_list=[])

    def test_list_max_length(self):
        """测试列表最大长度"""
        with pytest.raises(ValueError):
            BatchRequest(wybs_list=["ABC"] * 101)


class TestHealthStatusData:
    """HealthStatusData 测试"""

    def test_healthy_status(self):
        """测试健康状态"""
        data = HealthStatusData(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.now(),
            services={"database": "connected"},
        )

        assert data.status == "healthy"
        assert data.version == "1.0.0"
        assert data.services["database"] == "connected"

    def test_degraded_status(self):
        """测试降级状态"""
        data = HealthStatusData(
            status="degraded",
            version="1.0.0",
            timestamp=datetime.now(),
            services={"database": "disconnected"},
        )

        assert data.status == "degraded"


class TestTemplateInfo:
    """TemplateInfo 测试"""

    def test_template_info_creation(self):
        """测试模板信息创建"""
        info = TemplateInfo(
            id="模板1",
            name="通用生化试剂价格",
            category="集采产品",
            file="templates/模板1.docx",
            match_conditions={"产品细分": "通用生化试剂"},
        )

        assert info.id == "模板1"
        assert info.category == "集采产品"


class TestGenerateSuccessData:
    """GenerateSuccessData 测试"""

    def test_generate_success_data(self):
        """测试生成成功数据"""
        data = GenerateSuccessData(
            filename="报价单_20240301.docx",
            file_base64="UEsDBBQABgA...",
            templates_used=["模板1"],
        )

        assert data.filename == "报价单_20240301.docx"
        assert len(data.templates_used) == 1


class TestBatchResultItem:
    """BatchResultItem 测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = BatchResultItem(
            wybs="20240301001",
            files=[{"filename": "test.docx", "base64": "abc"}],
            success=True,
            error=None,
        )

        assert result.wybs == "20240301001"
        assert result.success is True

    def test_failed_result(self):
        """测试失败结果"""
        result = BatchResultItem(
            wybs="20240301001",
            files=[],
            success=False,
            error="报价单不存在",
        )

        assert result.success is False
        assert result.error == "报价单不存在"


class TestAsyncTaskData:
    """AsyncTaskData 测试"""

    def test_async_task_data(self):
        """测试异步任务数据"""
        data = AsyncTaskData(
            task_id="task_abc123",
            status="processing",
            progress=50,
            total=10,
            processed=5,
            failed=0,
        )

        assert data.task_id == "task_abc123"
        assert data.status == "processing"
        assert data.progress == 50


class TestHelperFunctions:
    """辅助函数测试"""

    def test_success_response(self):
        """测试成功响应创建"""
        response = success_response({"key": "value"}, message="操作成功", request_id="req_123")

        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message == "操作成功"
        assert response.request_id == "req_123"

    def test_error_response(self):
        """测试错误响应创建"""
        response = error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数错误",
            details={"field": "wybs"},
            request_id="req_123"
        )

        assert response.success is False
        assert response.error is not None
        assert response.error.code == ErrorCode.VALIDATION_ERROR
        assert response.request_id == "req_123"
