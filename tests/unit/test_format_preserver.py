"""格式保持器单元测试."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.shared import Pt, RGBColor

from src.fillers.format_preserver import FormatPreserver


class TestFormatPreserver:
    """FormatPreserver 测试"""

    def test_preserver_creation(self):
        """测试创建"""
        preserver = FormatPreserver()
        assert preserver is not None

    def test_copy_run_format(self):
        """测试复制 Run 格式"""
        # Mock 源 Run
        source_run = MagicMock()
        source_run.font.name = "宋体"
        source_run.font.size = Pt(12)
        source_run.font.bold = True
        source_run.font.italic = False
        source_run.font.underline = False
        source_run.font.color.rgb = RGBColor(255, 0, 0)

        # Mock 目标 Run
        target_run = MagicMock()

        # 执行复制
        FormatPreserver.copy_run_format(source_run, target_run)

        # 验证
        assert target_run.font.name == "宋体"
        assert target_run.font.size == Pt(12)
        assert target_run.font.bold is True

    def test_copy_run_format_partial(self):
        """测试部分复制 Run 格式"""
        source_run = MagicMock()
        source_run.font.name = None
        source_run.font.size = Pt(12)
        source_run.font.bold = None
        source_run.font.italic = None
        source_run.font.underline = None
        source_run.font.color.rgb = None

        target_run = MagicMock()

        FormatPreserver.copy_run_format(source_run, target_run)

        # 只设置了 size
        assert target_run.font.size == Pt(12)

    def test_copy_paragraph_format(self):
        """测试复制段落格式"""
        # Mock 源段落
        source_para = MagicMock()
        source_para.alignment = "CENTER"
        source_para.paragraph_format.line_spacing = 1.5
        source_para.paragraph_format.space_before = Pt(6)
        source_para.paragraph_format.space_after = Pt(3)

        # Mock 目标段落
        target_para = MagicMock()

        # 执行复制
        FormatPreserver.copy_paragraph_format(source_para, target_para)

        # 验证
        assert target_para.alignment == "CENTER"
        assert target_para.paragraph_format.line_spacing == 1.5

    def test_copy_paragraph_format_partial(self):
        """测试部分复制段落格式"""
        source_para = MagicMock()
        # 返回 None 而不是设置为 None
        type(source_para).alignment = property(lambda self: None)
        type(source_para.paragraph_format).line_spacing = property(lambda self: None)
        type(source_para.paragraph_format).space_before = property(lambda self: None)
        type(source_para.paragraph_format).space_after = property(lambda self: None)

        target_para = MagicMock()

        # 不应该设置任何属性
        FormatPreserver.copy_paragraph_format(source_para, target_para)
