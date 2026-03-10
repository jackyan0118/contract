"""API Routes 单元测试."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi import HTTPException


class TestHealthRoutes:
    """健康检查路由测试"""

    @pytest.mark.asyncio
    @patch("src.api.routes.health.check_database_health")
    @patch("src.api.routes.health.get_settings")
    async def test_health_check_healthy(self, mock_settings, mock_db_health):
        """测试健康检查 - 健康状态"""
        mock_settings_instance = MagicMock()
        mock_settings_instance.app.version = "1.0.0"
        mock_settings_instance.template.path = "docs/template"
        mock_settings_instance.template.output_dir = "output"
        mock_settings.return_value = mock_settings_instance

        mock_health = MagicMock()
        mock_health.healthy = True
        mock_db_health.return_value = mock_health

        from src.api.routes import health
        result = await health.health_check(user=None)

        assert result.success is True
        assert result.data.status == "healthy"
        assert result.data.version == "1.0.0"

    @pytest.mark.asyncio
    @patch("src.api.routes.health.check_database_health")
    @patch("src.api.routes.health.get_settings")
    async def test_health_check_degraded(self, mock_settings, mock_db_health):
        """测试健康检查 - 降级状态"""
        mock_settings_instance = MagicMock()
        mock_settings_instance.app.version = "1.0.0"

        # 使用 tmp_path 来避免文件系统问题
        import tempfile
        tmpdir = tempfile.mkdtemp()

        mock_settings_instance.template.path = tmpdir
        mock_settings_instance.template.output_dir = tmpdir
        mock_settings.return_value = mock_settings_instance

        mock_health = MagicMock()
        mock_health.healthy = False
        mock_db_health.return_value = mock_health

        from src.api.routes import health
        result = await health.health_check(user=None)

        assert result.data.status == "degraded"


class TestTemplateRoutes:
    """模板路由测试"""

    @pytest.mark.asyncio
    @patch("src.api.routes.templates.TemplateLoader")
    async def test_list_templates(self, mock_loader_class):
        """测试模板列表"""
        mock_template = MagicMock()
        mock_template.id = "模板1"
        mock_template.name = "通用生化试剂价格"
        mock_template.category = "集采产品"
        mock_template.file = "templates/模板1.docx"
        mock_template.match_conditions = {"产品细分": "通用生化试剂"}

        mock_loader = MagicMock()
        mock_loader.load_all.return_value = [mock_template]
        mock_loader_class.return_value = mock_loader

        from src.api.routes import templates
        result = await templates.list_templates(category=None, user="sk_test_12345678")

        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.asyncio
    @patch("src.api.routes.templates.TemplateLoader")
    async def test_list_templates_empty(self, mock_loader_class):
        """测试模板列表为空"""
        mock_loader = MagicMock()
        mock_loader.load_all.return_value = []
        mock_loader_class.return_value = mock_loader

        from src.api.routes import templates
        result = await templates.list_templates(category=None, user="sk_test_12345678")

        assert result.success is True
        assert result.data == []


class TestTaskRoutes:
    """任务路由测试"""

    @pytest.mark.asyncio
    @patch("src.api.routes.tasks.get_task_manager")
    async def test_get_task_status_not_found(self, mock_manager):
        """测试获取任务 - 不存在"""
        mock_mgr = MagicMock()
        mock_mgr.get_task.return_value = None
        mock_manager.return_value = mock_mgr

        from src.api.routes import tasks

        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_task_status(task_id="nonexistent", user="sk_test_12345678")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("src.api.routes.tasks.get_task_manager")
    async def test_get_task_status_no_access(self, mock_manager):
        """测试获取任务 - 无访问权限"""
        mock_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.task_id = "task_123"
        mock_mgr.get_task.return_value = mock_task
        mock_mgr.check_task_access.return_value = False
        mock_manager.return_value = mock_mgr

        from src.api.routes import tasks

        with pytest.raises(HTTPException) as exc_info:
            await tasks.get_task_status(task_id="task_123", user="other_user")

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    @patch("src.api.routes.tasks.get_task_manager")
    async def test_cancel_task_not_found(self, mock_manager):
        """测试取消任务 - 不存在"""
        mock_mgr = MagicMock()
        mock_mgr.get_task.return_value = None
        mock_manager.return_value = mock_mgr

        from src.api.routes import tasks

        with pytest.raises(HTTPException) as exc_info:
            await tasks.cancel_task(task_id="nonexistent", user="sk_test_12345678")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("src.api.routes.tasks.get_task_manager")
    async def test_cancel_task_no_access(self, mock_manager):
        """测试取消任务 - 无访问权限"""
        mock_mgr = MagicMock()
        mock_task = MagicMock()
        mock_task.task_id = "task_123"
        mock_mgr.get_task.return_value = mock_task
        mock_mgr.check_task_access.return_value = False
        mock_manager.return_value = mock_mgr

        from src.api.routes import tasks

        with pytest.raises(HTTPException) as exc_info:
            await tasks.cancel_task(task_id="task_123", user="other_user")

        assert exc_info.value.status_code == 403
