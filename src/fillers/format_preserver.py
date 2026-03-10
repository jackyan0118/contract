"""格式保持器 - 保持 Word 文档格式."""

import logging
from typing import Optional
from copy import deepcopy

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.shared import Pt, RGBColor

logger = logging.getLogger(__name__)


class FormatPreserver:
    """格式保持器 - 复制和保持 Word 文档格式"""

    @staticmethod
    def copy_run_format(source_run: Run, target_run: Run) -> None:
        """复制 Run 格式

        Args:
            source_run: 源 Run
            target_run: 目标 Run
        """
        # 字体格式
        if source_run.font.name:
            target_run.font.name = source_run.font.name
        if source_run.font.size:
            target_run.font.size = source_run.font.size
        if source_run.font.bold is not None:
            target_run.font.bold = source_run.font.bold
        if source_run.font.italic is not None:
            target_run.font.italic = source_run.font.italic
        if source_run.font.underline is not None:
            target_run.font.underline = source_run.font.underline

        # 颜色
        if source_run.font.color.rgb:
            target_run.font.color.rgb = source_run.font.color.rgb

    @staticmethod
    def copy_paragraph_format(source_para: Paragraph, target_para: Paragraph) -> None:
        """复制段落格式

        Args:
            source_para: 源段落
            target_para: 目标段落
        """
        # 对齐方式
        if source_para.alignment:
            target_para.alignment = source_para.alignment

        # 行距
        if source_para.paragraph_format.line_spacing:
            target_para.paragraph_format.line_spacing = source_para.paragraph_format.line_spacing

        # 段前段后间距
        if source_paragraph_format := source_para.paragraph_format:
            if source_paragraph_format.space_before:
                target_para.paragraph_format.space_before = source_paragraph_format.space_before
            if source_paragraph_format.space_after:
                target_para.paragraph_format.space_after = source_paragraph_format.space_after

    @staticmethod
    def copy_cell_format(source_cell, target_cell) -> None:
        """复制单元格格式

        Args:
            source_cell: 源单元格
            target_cell: 目标单元格
        """
        # 复制段落格式
        for src_para, dst_para in zip(source_cell.paragraphs, target_cell.paragraphs):
            FormatPreserver.copy_paragraph_format(src_para, dst_para)

            # 复制 Run 格式
            for src_run, dst_run in zip(src_para.runs, dst_para.runs):
                FormatPreserver.copy_run_format(src_run, dst_run)

    @staticmethod
    def copy_row_format(source_row, target_row) -> None:
        """复制行格式

        Args:
            source_row: 源行
            target_row: 目标行
        """
        for src_cell, dst_cell in zip(source_row.cells, target_row.cells):
            FormatPreserver.copy_cell_format(src_cell, dst_cell)

    @staticmethod
    def copy_table_row(table: Table, row_index: int) -> Table:
        """复制表格行（用于扩展）

        Args:
            table: 表格对象
            row_index: 行索引

        Returns:
            新的表格行
        """
        if row_index >= len(table.rows):
            raise IndexError(f"Row index {row_index} out of range")

        # 添加新行
        new_row = table.add_row()

        # 复制格式
        source_row = table.rows[row_index]
        FormatPreserver.copy_row_format(source_row, new_row)

        return new_row

    @staticmethod
    def clear_table_data_rows(table: Table, start_row: int = 1) -> None:
        """清除表格数据行（保留表头）

        Args:
            table: 表格对象
            start_row: 数据起始行索引
        """
        for row_idx in range(start_row, len(table.rows)):
            row = table.rows[row_idx]
            for cell in row.cells:
                cell.text = ""

    @staticmethod
    def get_template_row(table: Table) -> Optional[Table]:
        """获取模板行（第一行数据行）

        Args:
            table: 表格对象

        Returns:
            模板行或 None
        """
        if len(table.rows) < 2:
            return None

        return table.rows[1]  # 第二行是模板行
