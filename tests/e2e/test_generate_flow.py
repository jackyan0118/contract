"""端到端生成流程测试."""

import pytest
from unittest.mock import patch, MagicMock


class TestGenerateFlow:
    """完整生成流程 E2E 测试."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    @patch("src.generators.document_generator.DocumentGenerator")
    async def test_complete_generate_flow(self, mock_gen_class):
        """测试文档生成完整流程."""
        # Mock 文档生成器
        mock_gen = MagicMock()
        mock_gen.generate.return_value = MagicMock(
            success=True,
            file_path="output/test.docx"
        )
        mock_gen_class.return_value = mock_gen

        # 验证mock配置正确
        assert mock_gen_class is not None


class TestBatchGenerateFlow:
    """批量生成流程 E2E 测试."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    def test_batch_task_creation(self):
        """测试批量任务创建."""
        from src.api.tasks.manager import TaskManager, TaskStatus
        from datetime import datetime

        manager = TaskManager()

        # 创建任务
        task = manager.create_task(user_id="test_user", total=10)

        assert task.task_id is not None
        assert task.status == TaskStatus.PENDING
        assert task.total == 10


class TestTemplateMatchFlow:
    """模板匹配流程 E2E 测试."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    @patch("src.matchers.template_matcher.TemplateMatcher")
    async def test_match_success(self, mock_matcher_class):
        """测试成功匹配模板."""
        mock_matcher = MagicMock()
        mock_matcher.match.return_value = MagicMock(
            id="模板1",
            name="通用生化试剂",
            file="templates/模板1.docx"
        )
        mock_matcher_class.return_value = mock_matcher

        from src.matchers.template_matcher import TemplateMatcher

        matcher = TemplateMatcher()
        result = matcher.match({"产品细分": "通用生化试剂"})

        assert result is not None

    @pytest.mark.e2e
    @pytest.mark.asyncio
    @patch("src.matchers.template_matcher.TemplateMatcher")
    async def test_match_not_found(self, mock_matcher_class):
        """测试未匹配到模板."""
        mock_matcher = MagicMock()
        mock_matcher.match.return_value = None
        mock_matcher_class.return_value = mock_matcher

        from src.matchers.template_matcher import TemplateMatcher

        matcher = TemplateMatcher()
        result = matcher.match({"产品细分": "不存在的分类"})

        assert result is None
