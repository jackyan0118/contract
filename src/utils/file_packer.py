"""文件打包器 - 将生成的文档打包成 ZIP."""

import logging
import re
import zipfile
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# 不安全的文件名模式（目录遍历）
UNSAFE_PATTERNS = [
    r'\.\.',  # .. 目录遍历
    r'^/',    # 绝对路径
    r'^[a-zA-Z]:\\',  # Windows 绝对路径
]


def validate_filename(filename: str) -> bool:
    """验证文件名是否安全

    Args:
        filename: 文件名

    Returns:
        是否安全

    Raises:
        ValueError: 文件名不安全
    """
    if not filename:
        raise ValueError("文件名不能为空")

    # 检查是否包含不安全的模式
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, filename):
            raise ValueError(f"文件名包含不安全字符: {filename}")

    # 检查是否包含其他危险字符
    dangerous_chars = ['\0', '\n', '\r']
    for char in dangerous_chars:
        if char in filename:
            raise ValueError(f"文件名包含危险字符: {filename}")

    return True


class FilePacker:
    """文件打包器"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def pack(
        self,
        file_paths: List[str],
        output_name: Optional[str] = None
    ) -> str:
        """打包文件为 ZIP

        Args:
            file_paths: 文件路径列表
            output_name: 输出文件名（不含扩展名）

        Returns:
            ZIP 文件路径
        """
        if not file_paths:
            raise ValueError("No files to pack")

        # 生成输出文件名
        if not output_name:
            output_name = f"报价单_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 验证输出文件名，防止目录遍历攻击
        validate_filename(output_name)

        output_path = self.output_dir / f"{output_name}.zip"

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                path = Path(file_path)

                if not path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                # 添加文件到 ZIP
                zipf.write(path, path.name)
                logger.debug(f"Added to ZIP: {path.name}")

        logger.info(f"Created ZIP: {output_path}")
        return str(output_path)

    def pack_single(
        self,
        file_path: str,
        output_name: Optional[str] = None
    ) -> str:
        """打包单个文件为ZIP

        Args:
            file_path: 文件路径
            output_name: 输出文件名（不含扩展名）

        Returns:
            ZIP 文件路径
        """
        if not output_name:
            # 从原文件名生成输出名
            original_name = Path(file_path).stem
            output_name = f"{original_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 调用 pack 方法打包成 ZIP
        return self.pack([file_path], output_name)

    def cleanup(self, file_paths: List[str]) -> None:
        """清理临时文件

        Args:
            file_paths: 要删除的文件路径列表
        """
        for file_path in file_paths:
            path = Path(file_path)

            if path.exists() and path.is_file():
                try:
                    path.unlink()
                    logger.debug(f"Deleted: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")


def pack_files_to_base64_zip(file_paths: List[str]) -> str:
    """将文件打包为 Base64 编码的 ZIP

    Args:
        file_paths: 文件路径列表

    Returns:
        Base64 编码的 ZIP 内容
    """
    import base64
    from io import BytesIO

    if not file_paths:
        return ""

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                zipf.write(path, path.name)

    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')
