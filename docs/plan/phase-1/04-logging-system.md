# 04. 日志系统设计

## 设计目标

搭建结构化日志系统，支持控制台和文件输出，实现日志轮转和分级管理，便于问题排查和审计。

## 技术选型

- **Python logging** - 标准日志模块
- **RotatingFileHandler** - 日志轮转
- **JSON 格式化** - 结构化日志输出

## 日志级别定义

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发调试时的详细信息 |
| INFO | 一般信息 | 正常业务流程记录 |
| WARNING | 警告信息 | 不影响运行但需要注意的情况 |
| ERROR | 错误信息 | 业务逻辑错误，需要处理 |
| CRITICAL | 严重错误 | 系统故障，需要立即处理 |

## 代码实现

### src/utils/logger.py

```python
"""日志系统模块 - 结构化日志配置."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.config.settings import LoggingSettings, settings


class ColoredFormatter(logging.Formatter):
    """控制台彩色日志格式化器."""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",      # 青色
        "INFO": "\033[32m",       # 绿色
        "WARNING": "\033[33m",    # 黄色
        "ERROR": "\033[31m",      # 红色
        "CRITICAL": "\033[35m",   # 紫色
    }
    RESET = "\033[0m"  # 重置颜色

    def format(self, record: logging.LogRecord) -> str:
        # 保存原始值，避免影响其他 handler
        original_levelname = record.levelname
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        # 格式化
        result = super().format(record)
        # 恢复原始值
        record.levelname = original_levelname
        return result


def setup_logger(
    name: str,
    config: Optional[LoggingSettings] = None,
) -> logging.Logger:
    """
    设置并返回 logger 实例.

    Args:
        name: logger 名称
        config: 日志配置，默认使用全局配置

    Returns:
        配置好的 logger 实例
    """
    if config is None:
        config = settings.logging

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.level.upper()))

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.level.upper()))
    console_formatter = ColoredFormatter(config.format_console)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件 handler (带轮转)
    log_file = Path(config.file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, config.level.upper()))
    file_formatter = logging.Formatter(config.format_file)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例.

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        配置好的 logger 实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条日志信息")
    """
    return setup_logger(name)
```

### src/utils/structured_logger.py

```python
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
```

### src/api/middleware/request_logger.py

```python
"""请求日志中间件."""

import time
from typing import Callable

from fastapi import Request, Response
from src.utils.structured_logger import get_structured_logger

logger = get_structured_logger("api.request")


async def request_logging_middleware(
    request: Request,
    call_next: Callable,
) -> Response:
    """记录 HTTP 请求日志."""
    start_time = time.time()

    # 记录请求
    logger.info(
        "请求开始",
        context={
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client": request.client.host if request.client else None,
        },
    )

    # 处理请求
    response = await call_next(request)

    # 计算耗时
    duration = time.time() - start_time

    # 记录响应
    logger.info(
        "请求完成",
        context={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        },
    )

    return response
```

## 日志输出示例

### 控制台输出

```
[2026-03-06 10:00:00,000] [INFO] [api.generate] 开始处理价格附件生成请求
[2026-03-06 10:00:01,234] [INFO] [matcher.template] 匹配到模板：模板 1：酶免和胶体金
[2026-03-06 10:00:02,456] [INFO] [generator.word] Word 文件生成完成：output/QTD20260306001_模板 1.docx
```

### 文件输出（JSON）

```json
{
  "timestamp": "2026-03-06T10:00:00.000Z",
  "level": "INFO",
  "logger": "api.generate",
  "message": "开始处理价格附件生成请求",
  "context": {
    "wybs": "QTD20260306001",
    "client_ip": "192.168.1.100"
  }
}
```

### 业务日志示例

```python
from src.utils.structured_logger import get_structured_logger

logger = get_structured_logger("business.audit")

# 记录业务操作
logger.info(
    "价格附件生成成功",
    context={
        "wybs": "QTD20260306001",
        "templates_matched": ["模板 1：酶免和胶体金", "模板 2：通用生化"],
        "output_files": ["output/QTD20260306001_模板 1.docx"],
        "duration_ms": 2456,
    },
)
```

## 日志轮转配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `max_bytes` | 10MB | 单文件最大 10MB |
| `backup_count` | 5 | 保留 5 个备份文件 |
| 总容量 | 60MB | 最多 6 个文件×10MB |

## 验收标准

- [ ] 日志可正常输出到控制台
- [ ] 日志可正常输出到文件
- [ ] 日志轮转正常工作
- [ ] 彩色控制台日志正常
- [ ] 结构化日志 JSON 格式正确
- [ ] 请求日志中间件正常工作

---

*文档版本：1.0*
*创建日期：2026-03-06*
