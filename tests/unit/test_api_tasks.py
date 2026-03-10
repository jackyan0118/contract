"""API 任务管理器单元测试."""

import pytest
from datetime import datetime
from src.api.tasks.manager import Task, TaskManager, TaskStatus, get_task_manager


class TestTask:
    """Task 数据类测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            task_id="task_123",
            user_id="user_456",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            total=10,
        )
        assert task.task_id == "task_123"
        assert task.user_id == "user_456"
        assert task.status == TaskStatus.PENDING
        assert task.total == 10
        assert task.processed == 0
        assert task.failed == 0

    def test_task_default_values(self):
        """测试默认值"""
        task = Task(
            task_id="task_123",
            user_id="user_456",
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
        )
        assert task.total == 0
        assert task.processed == 0
        assert task.failed == 0
        assert task.completed_at is None
        assert task.results == []


class TestTaskManager:
    """TaskManager 测试"""

    def test_create_task(self):
        """测试任务创建"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=5)

        assert task.task_id.startswith("task_")
        assert task.user_id == "user_123"
        assert task.status == TaskStatus.PENDING
        assert task.total == 5

    def test_get_task(self):
        """测试获取任务"""
        manager = TaskManager()
        created_task = manager.create_task(user_id="user_123", total=5)
        retrieved_task = manager.get_task(created_task.task_id)

        assert retrieved_task is not None
        assert retrieved_task.task_id == created_task.task_id
        assert retrieved_task.user_id == "user_123"

    def test_get_task_not_found(self):
        """测试获取不存在的任务"""
        manager = TaskManager()
        task = manager.get_task("nonexistent_task")

        assert task is None

    def test_update_task_status(self):
        """测试更新任务状态"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)

        updated = manager.update_task(
            task_id=task.task_id,
            status=TaskStatus.PROCESSING,
            processed=3,
        )

        assert updated is not None
        assert updated.status == TaskStatus.PROCESSING
        assert updated.processed == 3

    def test_update_task_progress(self):
        """测试更新进度"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)

        manager.update_task(task.task_id, processed=5, failed=1)

        updated = manager.get_task(task.task_id)
        assert updated.processed == 5
        assert updated.failed == 1

    def test_cancel_task(self):
        """测试取消任务"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)

        success = manager.cancel_task(task.task_id)
        assert success is True

        cancelled_task = manager.get_task(task.task_id)
        assert cancelled_task.status == TaskStatus.CANCELLED
        assert cancelled_task.completed_at is not None

    def test_cancel_completed_task(self):
        """测试取消已完成的任务"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)
        manager.update_task(task.task_id, status=TaskStatus.COMPLETED)

        success = manager.cancel_task(task.task_id)
        assert success is False

    def test_delete_task(self):
        """测试删除任务"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)

        success = manager.delete_task(task.task_id)
        assert success is True

        assert manager.get_task(task.task_id) is None

    def test_check_task_access(self):
        """测试任务访问权限"""
        manager = TaskManager()
        task = manager.create_task(user_id="user_123", total=10)

        # 任务创建者可以访问
        assert manager.check_task_access(task.task_id, "user_123") is True

        # 其他用户不能访问
        assert manager.check_task_access(task.task_id, "user_456") is False

    def test_check_task_access_not_found(self):
        """测试访问不存在的任务"""
        manager = TaskManager()
        assert manager.check_task_access("nonexistent", "user_123") is False


class TestGetTaskManager:
    """get_task_manager 单例测试"""

    def test_singleton(self):
        """测试单例模式"""
        manager1 = get_task_manager()
        manager2 = get_task_manager()

        assert manager1 is manager2
