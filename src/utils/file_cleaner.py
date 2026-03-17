"""文件清理器 - 清理过期的下载文件."""

import logging
import time
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """清理结果"""
    deleted_count: int
    deleted_files: List[str]
    errors: List[str]


class FileCleaner:
    """文件清理器 - 清理过期的下载文件"""

    def __init__(self, storage_dir: str = "output/downloads", expires_in: int = 86400):
        """初始化清理器

        Args:
            storage_dir: 存储目录
            expires_in: 过期时间（秒），默认24小时
        """
        self.storage_dir = Path(storage_dir)
        self.expires_in = expires_in

    def should_cleanup(self, file_path: Path) -> bool:
        """判断文件是否过期

        Args:
            file_path: 文件路径

        Returns:
            是否应该清理
        """
        if not file_path.exists() or not file_path.is_file():
            return False

        try:
            file_age = time.time() - file_path.stat().st_mtime
            return file_age > self.expires_in
        except OSError as e:
            logger.warning(f"Failed to get file stat {file_path}: {e}")
            return False

    def cleanup(self) -> CleanupResult:
        """执行清理操作

        Returns:
            清理结果
        """
        deleted_files: List[str] = []
        errors: List[str] = []

        if not self.storage_dir.exists():
            logger.info(f"Storage directory does not exist: {self.storage_dir}")
            return CleanupResult(
                deleted_count=0,
                deleted_files=[],
                errors=[f"Directory not found: {self.storage_dir}"]
            )

        # 遍历所有文件
        for file_path in self.storage_dir.rglob("*.zip"):
            if self.should_cleanup(file_path):
                try:
                    file_path.unlink()
                    deleted_files.append(str(file_path))
                    logger.info(f"Deleted expired file: {file_path}")
                except OSError as e:
                    error_msg = f"Failed to delete {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        # 清理空目录
        self._cleanup_empty_dirs()

        result = CleanupResult(
            deleted_count=len(deleted_files),
            deleted_files=deleted_files,
            errors=errors
        )

        logger.info(f"Cleanup completed: {result.deleted_count} files deleted")
        return result

    def _cleanup_empty_dirs(self) -> None:
        """清理空目录"""
        if not self.storage_dir.exists():
            return

        # 从内到外遍历，删除空目录
        for dir_path in sorted(self.storage_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.debug(f"Removed empty directory: {dir_path}")
                except OSError as e:
                    logger.warning(f"Failed to remove directory {dir_path}: {e}")

    def get_disk_usage(self) -> Tuple[int, int]:
        """获取磁盘使用情况

        Returns:
            (已使用字节, 总字节)
        """
        import shutil
        try:
            stat = shutil.disk_usage(self.storage_dir)
            return (stat.used, stat.total)
        except OSError as e:
            logger.error(f"Failed to get disk usage: {e}")
            return (0, 0)

    def is_disk_space_low(self, threshold: int = 80) -> bool:
        """检查磁盘空间是否不足

        Args:
            threshold: 告警阈值（百分比）

        Returns:
            是否空间不足
        """
        used, total = self.get_disk_usage()
        if total == 0:
            return False

        usage_percent = (used / total) * 100
        return usage_percent >= threshold


def run_cleanup(
    storage_dir: str = "output/downloads",
    expires_in: int = 86400,
    threshold: int = 80
) -> CleanupResult:
    """便捷函数：运行清理

    Args:
        storage_dir: 存储目录
        expires_in: 过期时间（秒）
        threshold: 磁盘空间告警阈值

    Returns:
        清理结果
    """
    cleaner = FileCleaner(storage_dir, expires_in)

    # 先检查磁盘空间
    if cleaner.is_disk_space_low(threshold):
        logger.warning(f"Disk space is below threshold ({threshold}%)")

    return cleaner.cleanup()


if __name__ == "__main__":
    # 命令行运行
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s'
    )

    storage_dir = sys.argv[1] if len(sys.argv) > 1 else "output/downloads"
    expires_in = int(sys.argv[2]) if len(sys.argv) > 2 else 86400

    result = run_cleanup(storage_dir, expires_in)
    print(f"Deleted: {result.deleted_count} files")
