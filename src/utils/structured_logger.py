"""结构化日志模块 - JSON 格式日志输出."""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON 格式化器 - 用于结构化日志输出."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加额外字段
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """结构化日志记录器."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _log(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """记录日志."""
        extra: Dict[str, Any] = {}
        if context:
            extra["context"] = context
        # 防止覆盖保留字段
        reserved_keys = {"context"}
        for key, value in kwargs.items():
            if key in reserved_keys:
                raise ValueError(f"Cannot override reserved key: {key}")
            extra[key] = value
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.WARNING, message, context)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        if exc_info:
            self.logger.error(message, exc_info=True, extra={"context": context})
        else:
            self._log(logging.ERROR, message, context)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        if exc_info:
            self.logger.critical(message, exc_info=True, extra={"context": context})
        else:
            self._log(logging.CRITICAL, message, context)


def get_structured_logger(name: str) -> StructuredLogger:
    """获取结构化日志记录器."""
    from src.utils.logger import get_logger

    return StructuredLogger(get_logger(name))
