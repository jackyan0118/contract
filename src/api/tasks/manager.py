"""异步任务管理器."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("api.tasks")


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """任务对象"""

    task_id: str
    user_id: str  # 绑定用户，用于权限控制
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total: int = 0
    processed: int = 0
    failed: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class TaskManager:
    """异步任务管理器（内存实现）"""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = Lock()

    def create_task(self, user_id: str, total: int = 0) -> Task:
        """创建新任务

        Args:
            user_id: 用户标识（API Key）
            total: 任务总数
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = Task(
            task_id=task_id,
            user_id=user_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            total=total,
        )
        with self._lock:
            self._tasks[task_id] = task
        logger.info(f"Created task: {task_id} for user: {user_id}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        processed: Optional[int] = None,
        failed: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Optional[Task]:
        """更新任务状态"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None

            if status:
                task.status = status
            if processed is not None:
                task.processed = processed
            if failed is not None:
                task.failed = failed
            if result:
                task.results.append(result)
            if error:
                task.error = error

            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.completed_at = datetime.now()

            return task

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                return False
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False

    def check_task_access(self, task_id: str, user_id: str) -> bool:
        """检查用户是否有权限访问任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            True 如果用户有权限，否则 False
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            # 任务创建者才能访问
            return task.user_id == user_id


# 全局任务管理器
_task_manager: Optional[TaskManager] = None
_manager_lock = Lock()


def get_task_manager() -> TaskManager:
    """获取全局任务管理器"""
    global _task_manager
    if _task_manager is None:
        with _manager_lock:
            if _task_manager is None:
                _task_manager = TaskManager()
    return _task_manager
