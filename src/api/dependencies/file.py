"""文件处理依赖模块."""

import base64
import os
import tempfile
from pathlib import Path
from typing import Optional

from src.config.settings import get_settings


def get_output_dir() -> Path:
    """获取输出目录"""
    settings = get_settings()
    output_dir = Path(settings.template.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_temp_dir() -> Path:
    """获取临时文件目录"""
    temp_dir = Path("/tmp/price_attachments")
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def read_file_as_base64(file_path: str) -> str:
    """读取文件并转换为 Base64"""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def cleanup_temp_files(max_age_seconds: int = 3600) -> int:
    """清理临时文件

    Args:
        max_age_seconds: 文件最大存活时间（秒）

    Returns:
        清理的文件数量
    """
    temp_dir = get_temp_dir()
    cleaned = 0
    import time

    current_time = time.time()

    for file in temp_dir.glob("*"):
        if file.is_file():
            file_age = current_time - file.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file.unlink()
                    cleaned += 1
                except Exception:
                    pass

    return cleaned
