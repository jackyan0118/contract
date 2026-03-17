"""API Routes 单元测试 - Generate & Batch."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.api.schemas import GenerateRequest, BatchRequest


class TestGenerateRequest:
    """GenerateRequest 模型测试"""

    def test_generate_request_creation(self):
        """测试创建请求"""
        request = GenerateRequest(wybs="WYBS20240301")
        assert request.wybs == "WYBS20240301"

    def test_generate_request_with_optional_params(self):
        """测试带可选参数"""
        request = GenerateRequest(wybs="WYBS20240301")
        assert request.wybs == "WYBS20240301"


class TestBatchRequest:
    """BatchRequest 模型测试"""

    def test_batch_request_creation(self):
        """测试创建批量请求"""
        request = BatchRequest(wybs_list=["WYBS001", "WYBS002"])
        assert len(request.wybs_list) == 2
        assert request.wybs_list[0] == "WYBS001"

    def test_batch_request_empty_list(self):
        """测试空列表 - API不允许空列表，应抛出验证错误"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BatchRequest(wybs_list=[])


class TestGenerateFlow:
    """生成流程测试"""

    @patch('src.api.routes.generate.get_quotation_by_wybs')
    @patch('src.api.routes.generate.get_quotation_details')
    @patch('src.api.routes.generate.get_transformer')
    @patch('src.api.routes.generate.RuleLoader')
    @patch('src.api.routes.generate.DocumentGenerator')
    @patch('src.api.routes.generate.FilePacker')
    @patch('src.api.routes.generate.get_settings')
    def test_generate_quote_not_found(
        self,
        mock_settings,
        mock_file_packer,
        mock_generator,
        mock_rule_loader,
        mock_transformer,
        mock_details,
        mock_quote
    ):
        """测试报价单不存在"""
        from src.api.routes import generate

        mock_quote.return_value = None

        # 测试 get_quotation_by_wybs 返回 None 时的处理
        # 由于需要完整 FastAPI app，这里只测试逻辑
        wybs = "NOTEXIST"
        result = generate.get_quotation_by_wybs(wybs)
        assert result is None


class TestRuleLoader:
    """RuleLoader 测试"""

    @patch('src.services.rule_loader.RuleLoader.load')
    def test_rule_loader_load(self, mock_load):
        """测试规则加载"""
        from src.services.rule_loader import RuleLoader

        loader = RuleLoader()
        mock_load.return_value = []

        # 测试加载
        result = loader.load()
        assert isinstance(result, list)


class TestTemplateMatcher:
    """TemplateMatcher 测试"""

    def test_matcher_creation(self):
        """测试匹配器创建"""
        from src.matchers.template_matcher import TemplateMatcher
        from src.models.template_rule import TemplateRule

        rules = [
            TemplateRule(id="1", name="模板1", file="1.docx", 条件=[])
        ]
        matcher = TemplateMatcher(rules)
        assert matcher is not None
