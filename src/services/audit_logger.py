"""审计日志服务 - 记录业务操作审计日志."""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from threading import Lock

from src.utils.logger import get_logger

logger = get_logger("audit")


class AuditEvent(str, Enum):
    """审计事件类型"""

    API_REQUEST = "api_request"
    GENERATE = "generate"
    BATCH_GENERATE = "batch_generate"
    TASK_CREATE = "task_create"
    TASK_CANCEL = "task_cancel"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"


class AuditLogger:
    """审计日志记录器

    记录业务操作到 JSON Lines 格式的日志文件。
    """

    def __init__(self, log_file: str = "logs/audit.log"):
        self._log_file = Path(log_file)
        self._lock = Lock()
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """确保日志目录存在"""
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event: AuditEvent,
        user: str,
        resource: str,
        action: str,
        result: str,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """记录审计日志

        Args:
            event: 事件类型
            user: 用户标识（建议传入脱敏后的 API Key）
            resource: 关联资源（如 wybs）
            action: 操作类型
            result: 结果（success/failed）
            request_id: 请求追踪ID
            error_message: 错误信息
            user_agent: 客户端标识
            details: 额外信息
        """
        # 脱敏用户标识
        safe_user = self._mask_user(user)

        log_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "event": event.value,
            "user": safe_user,
            "user_agent": user_agent or "unknown",
            "resource": resource,
            "action": action,
            "result": result,
            "error_message": error_message,
            "request_id": request_id,
            "details": details or {},
        }

        self._write(log_entry)

    def _mask_user(self, user: str) -> str:
        """脱敏用户标识

        例如: sk_dev_abc123 -> sk_dev_***
        """
        if not user:
            return "unknown"

        if len(user) <= 8:
            return user[:4] + "***"

        prefix = user[:7]
        return prefix + "***"

    def _write(self, log_entry: Dict[str, Any]) -> None:
        """写入日志文件"""
        with self._lock:
            try:
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}")

    def log_api_request(
        self,
        method: str,
        path: str,
        user: str,
        status_code: int,
        duration_ms: int,
        request_id: Optional[str] = None,
    ) -> None:
        """记录 API 请求"""
        result = "success" if status_code < 400 else "failed"
        self.log(
            event=AuditEvent.API_REQUEST,
            user=user,
            resource=path,
            action=f"{method} {path}",
            result=result,
            request_id=request_id,
            details={"status_code": status_code, "duration_ms": duration_ms},
        )

    def log_generate(
        self,
        wybs: str,
        user: str,
        templates_used: list[str],
        file_count: int,
        duration_ms: int,
        success: bool,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """记录文档生成操作"""
        self.log(
            event=AuditEvent.GENERATE,
            user=user,
            resource=wybs,
            action="document_generation",
            result="success" if success else "failed",
            request_id=request_id,
            error_message=error_message,
            details={
                "templates_used": templates_used,
                "file_count": file_count,
                "duration_ms": duration_ms,
            },
        )

    def log_batch_generate(
        self,
        wybs_list: list[str],
        user: str,
        count: int,
        success_count: int,
        duration_ms: int,
        request_id: Optional[str] = None,
    ) -> None:
        """记录批量生成操作"""
        self.log(
            event=AuditEvent.BATCH_GENERATE,
            user=user,
            resource=",".join(wybs_list[:3]) + ("..." if len(wybs_list) > 3 else ""),
            action="batch_document_generation",
            result="success",
            request_id=request_id,
            details={
                "total_count": count,
                "success_count": success_count,
                "duration_ms": duration_ms,
            },
        )

    def log_task_create(
        self,
        task_id: str,
        wybs_list: list[str],
        user: str,
        request_id: Optional[str] = None,
    ) -> None:
        """记录任务创建"""
        self.log(
            event=AuditEvent.TASK_CREATE,
            user=user,
            resource=task_id,
            action="task_creation",
            result="success",
            request_id=request_id,
            details={"wybs_count": len(wybs_list)},
        )

    def log_task_cancel(
        self,
        task_id: str,
        user: str,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """记录任务取消"""
        self.log(
            event=AuditEvent.TASK_CANCEL,
            user=user,
            resource=task_id,
            action="task_cancellation",
            result="success",
            request_id=request_id,
            error_message=reason,
        )


# 全局审计日志实例
_audit_logger: Optional[AuditLogger] = None
_audit_logger_lock = Lock()


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志实例（线程安全单例）"""
    global _audit_logger
    if _audit_logger is None:
        with _audit_logger_lock:
            if _audit_logger is None:
                _audit_logger = AuditLogger()
    return _audit_logger
