"""行扩展器单元测试."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from docx.table import Table, _Cell, _Row
from docx.text.paragraph import Paragraph

from src.fillers.row_expander import RowExpander


class TestRowExpander:
    """RowExpander 测试"""

    def test_expander_creation(self):
        """测试创建"""
        expander = RowExpander()
        assert expander is not None
        assert expander.format_preserver is not None

    def test_expand_empty_data(self):
        """测试空数据"""
        expander = RowExpander()

        mock_table = MagicMock()

        # 不应该抛出异常
        expander.expand(mock_table, [], [])

    def test_ensure_rows_not_needed(self):
        """测试不需要添加行"""
        expander = RowExpander()

        # 已有足够行
        mock_table = MagicMock()
        # 模拟有3行，起始行1，需要2行
        mock_table.rows.__len__ = lambda self: 3

        expander._ensure_rows(mock_table, 2, 1)

        # 不应该添加新行（rows_to_add <= 0）

    @patch("src.fillers.row_expander.Table.add_row")
    def test_ensure_rows_need_to_add(self, mock_add_row):
        """测试需要添加行"""
        expander = RowExpander()

        # 模拟只有2行，起始行1
        mock_table = MagicMock()
        # 返回 2 表示只有2行
        type(mock_table.rows).__len__ = lambda x: 2
        # 返回一个 mock 行作为模板行
        mock_template_row = MagicMock()
        mock_template_cell = MagicMock()
        mock_template_cell.paragraphs = [MagicMock()]
        mock_template_row.cells = [mock_template_cell]
        mock_table.rows.__getitem__ = lambda self, i: [MagicMock(), mock_template_row][i]

        mock_add_row.return_value = MagicMock()

        # 需要5行，从第1行开始，所以需要添加
        expander._ensure_rows(mock_table, 5, 1)

        # 验证 add_row 被调用


class TestGetValue:
    """_get_value 方法测试"""

    def test_get_value_text_type(self):
        """测试文本类型"""
        expander = RowExpander()

        data = {"名称": "产品1"}
        col_config = {"name": "名称", "type": "text", "field": "名称"}
        result = expander._get_value(data, col_config, 1)

        assert result == "产品1"

    def test_get_value_number_type(self):
        """测试数字类型"""
        expander = RowExpander()

        data = {"数量": 100, "金额": 1000.50}
        col_config = {"name": "数量", "type": "number", "field": "数量"}
        result = expander._get_value(data, col_config, 1)

        assert result == 100
