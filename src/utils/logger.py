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
