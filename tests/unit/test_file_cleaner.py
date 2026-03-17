"""文件清理器测试."""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.utils.file_cleaner import FileCleaner, CleanupResult, run_cleanup


class TestFileCleaner:
    """文件清理器测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    @pytest.fixture
    def cleaner(self, temp_dir):
        """创建清理器实例"""
        return FileCleaner(storage_dir=temp_dir, expires_in=2)  # 2秒过期

    def test_cleaner_creation(self, temp_dir):
        """测试清理器创建"""
        cleaner = FileCleaner(storage_dir=temp_dir, expires_in=3600)
        assert cleaner.storage_dir == Path(temp_dir)
        assert cleaner.expires_in == 3600

    def test_should_cleanup_expired_file(self, cleaner, temp_dir):
        """测试过期文件判断"""
        # 创建一个文件
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("content")

        # 等待文件过期
        time.sleep(3)

        assert cleaner.should_cleanup(test_file) is True

    def test_should_cleanup_fresh_file(self, cleaner, temp_dir):
        """测试未过期文件"""
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("content")

        # 不等待，文件未过期
        assert cleaner.should_cleanup(test_file) is False

    def test_should_cleanup_nonexistent_file(self, cleaner):
        """测试不存在的文件"""
        test_file = Path("/nonexistent/file.txt")
        assert cleaner.should_cleanup(test_file) is False

    def test_cleanup_empty_directory(self, cleaner, temp_dir):
        """测试清理空目录"""
        result = cleaner.cleanup()
        assert result.deleted_count == 0
        assert len(result.deleted_files) == 0

    def test_cleanup_expired_files(self, cleaner, temp_dir):
        """测试清理过期文件"""
        # 创建过期的 zip 文件
        for i in range(3):
            expired_file = Path(temp_dir) / f"expired_{i}.zip"
            expired_file.write_text(f"content{i}")

        # 等待过期
        time.sleep(3)

        # 创建未过期的文件
        fresh_file = Path(temp_dir) / "fresh.zip"
        fresh_file.write_text("fresh")

        # 等待1秒（文件未过期）
        time.sleep(1)

        result = cleaner.cleanup()

        assert result.deleted_count == 3
        assert len(result.deleted_files) == 3

    def test_cleanup_preserves_fresh_files(self, cleaner, temp_dir):
        """测试保留未过期文件"""
        # 创建未过期的文件
        fresh_file = Path(temp_dir) / "fresh.zip"
        fresh_file.write_text("fresh")

        result = cleaner.cleanup()

        assert result.deleted_count == 0
        assert fresh_file.exists()

    def test_cleanup_nested_directories(self, cleaner, temp_dir):
        """测试清理嵌套目录中的过期文件"""
        # 创建子目录和文件
        sub_dir = Path(temp_dir) / "20260317"
        sub_dir.mkdir()
        (sub_dir / "file1.zip").write_text("content1")
        (sub_dir / "file2.zip").write_text("content2")

        # 等待过期
        time.sleep(3)

        result = cleaner.cleanup()

        assert result.deleted_count == 2

    def test_get_disk_usage(self, cleaner, temp_dir):
        """测试磁盘使用情况"""
        Path(temp_dir).joinpath("test.txt").write_text("content")

        used, total = cleaner.get_disk_usage()

        assert used > 0
        assert total > 0

    def test_is_disk_space_low(self, cleaner, temp_dir):
        """测试磁盘空间检查"""
        is_low = cleaner.is_disk_space_low(threshold=100)
        assert is_low is False

    def test_run_cleanup_function(self, temp_dir):
        """测试便捷函数"""
        # 创建过期文件
        test_file = Path(temp_dir) / "test.zip"
        test_file.write_text("content")

        time.sleep(3)

        result = run_cleanup(temp_dir, expires_in=2)

        assert result.deleted_count >= 1


class TestPackSingleModification:
    """pack_single 方法修改后的测试"""

    @pytest.fixture
    def temp_output_dir(self):
        """创建临时输出目录"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)

    def test_pack_single_creates_zip(self, temp_output_dir):
        """测试单文件打包成ZIP"""
        from src.utils.file_packer import FilePacker

        # 创建一个测试文件
        test_dir = tempfile.mkdtemp()
        test_file = Path(test_dir) / "test.docx"
        test_file.write_text("test content")

        try:
            packer = FilePacker(output_dir=temp_output_dir)
            result = packer.pack_single(str(test_file))

            # 验证返回的是 ZIP 文件
            assert result.endswith(".zip")
            assert Path(result).exists()
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_pack_single_with_custom_name(self, temp_output_dir):
        """测试自定义输出文件名"""
        from src.utils.file_packer import FilePacker

        test_dir = tempfile.mkdtemp()
        test_file = Path(test_dir) / "test.docx"
        test_file.write_text("test content")

        try:
            packer = FilePacker(output_dir=temp_output_dir)
            result = packer.pack_single(str(test_file), output_name="custom_name")

            assert "custom_name" in result
            assert result.endswith(".zip")
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)
