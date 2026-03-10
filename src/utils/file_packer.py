"""文件打包器 - 将生成的文档打包成 ZIP."""

import logging
import zipfile
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


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
        """打包单个文件（直接返回或打包）

        Args:
            file_path: 文件路径
            output_name: 输出文件名

        Returns:
            文件路径（如果只有一个文件则原样返回，否则返回 ZIP 路径）
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 如果只需要一个文件，直接返回
        return str(path)

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
