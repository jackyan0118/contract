"""文件打包器单元测试."""

import pytest
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

from src.utils.file_packer import FilePacker, validate_filename


@pytest.fixture
def temp_output_dir():
    """创建临时输出目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_files():
    """创建临时文件"""
    files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        for i in range(3):
            file_path = Path(tmpdir) / f"test_{i}.txt"
            file_path.write_text(f"Content {i}")
            files.append(str(file_path))
        yield files


class TestFilePacker:
    """FilePacker 测试"""

    def test_packer_creation(self, temp_output_dir):
        """测试打包器创建"""
        packer = FilePacker(output_dir=temp_output_dir)
        assert packer.output_dir == Path(temp_output_dir)

    def test_pack_files(self, temp_output_dir, temp_files):
        """测试打包文件"""
        packer = FilePacker(output_dir=temp_output_dir)
        result = packer.pack(temp_files, output_name="test_pack")

        assert result.endswith(".zip")
        assert Path(result).exists()

        # 验证 ZIP 内容
        with zipfile.ZipFile(result, 'r') as zipf:
            names = zipf.namelist()
            assert len(names) == 3

    def test_pack_empty_list(self, temp_output_dir):
        """测试打包空列表"""
        packer = FilePacker(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="No files"):
            packer.pack([])

    def test_pack_nonexistent_file(self, temp_output_dir):
        """测试打包不存在的文件"""
        packer = FilePacker(output_dir=temp_output_dir)

        # 不存在的文件会被警告但不会报错
        result = packer.pack(["/nonexistent/file.txt"], output_name="test")

        assert Path(result).exists()
        # ZIP 应该是空的（只包含不存在的文件）
        with zipfile.ZipFile(result, 'r') as zipf:
            assert len(zipf.namelist()) == 0

    def test_pack_auto_name(self, temp_output_dir, temp_files):
        """测试自动生成文件名"""
        packer = FilePacker(output_dir=temp_output_dir)
        result = packer.pack(temp_files)

        assert "报价单_" in result
        assert result.endswith(".zip")
        assert Path(result).exists()

    def test_pack_output_dir_creation(self, temp_files):
        """测试输出目录自动创建"""
        # 使用不存在的目录
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output" / "dir"

            packer = FilePacker(output_dir=str(output_dir))
            result = packer.pack(temp_files, output_name="test")

            assert output_dir.exists()
            assert Path(result).exists()

    def test_pack_single(self, temp_output_dir, temp_files):
        """测试单文件打包"""
        packer = FilePacker(output_dir=temp_output_dir)
        result = packer.pack_single(temp_files[0], output_name="single_test")

        assert result.endswith(".zip")
        assert Path(result).exists()

        # 验证 ZIP 内容
        with zipfile.ZipFile(result, 'r') as zipf:
            names = zipf.namelist()
            assert len(names) == 1

    def test_pack_single_auto_name(self, temp_output_dir, temp_files):
        """测试单文件打包自动生成文件名"""
        packer = FilePacker(output_dir=temp_output_dir)
        result = packer.pack_single(temp_files[0])

        # 应该包含原文件名和时间戳
        assert "test_0" in result
        assert result.endswith(".zip")
        assert Path(result).exists()

    def test_pack_with_path_traversal_attempt(self, temp_output_dir, temp_files):
        """测试目录遍历攻击防护"""
        packer = FilePacker(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="不安全字符"):
            packer.pack(temp_files, output_name="../../../etc/passwd")

        with pytest.raises(ValueError, match="不安全字符"):
            packer.pack(temp_files, output_name="/etc/passwd")

    def test_pack_single_with_path_traversal(self, temp_output_dir, temp_files):
        """测试单文件打包目录遍历防护"""
        packer = FilePacker(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="不安全字符"):
            packer.pack_single(temp_files[0], output_name="test/../../../etc")


class TestValidateFilename:
    """validate_filename 函数测试"""

    def test_normal_filename(self):
        """测试正常文件名"""
        assert validate_filename("normal_file.txt") is True
        assert validate_filename("报价单_20250317.docx") is True

    def test_empty_filename(self):
        """测试空文件名"""
        with pytest.raises(ValueError, match="不能为空"):
            validate_filename("")

    def test_parent_directory_traversal(self):
        """测试父目录遍历"""
        with pytest.raises(ValueError, match="不安全字符"):
            validate_filename("../etc/passwd")

        with pytest.raises(ValueError, match="不安全字符"):
            validate_filename("..\\Windows\\System32")

    def test_absolute_path(self):
        """测试绝对路径"""
        with pytest.raises(ValueError, match="不安全字符"):
            validate_filename("/etc/passwd")

        with pytest.raises(ValueError, match="不安全字符"):
            validate_filename("C:\\Windows\\System32")

    def test_dangerous_characters(self):
        """测试危险字符"""
        with pytest.raises(ValueError, match="危险字符"):
            validate_filename("file\nname.txt")

        with pytest.raises(ValueError, match="危险字符"):
            validate_filename("file\rname.txt")

        with pytest.raises(ValueError, match="危险字符"):
            validate_filename("file\x00name.txt")

    def test_malicious_filename_patterns(self):
        """测试恶意文件名模式"""
        malicious_names = [
            "....//etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "test/../../etc/passwd",
            "test\\..\\..\\Windows\\System32",
        ]
        for name in malicious_names:
            with pytest.raises(ValueError):
                validate_filename(name)
