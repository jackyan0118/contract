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

    def test_expand_single_row(self):
        """测试单行数据"""
        expander = RowExpander()

        mock_table = MagicMock()
        mock_table.rows = [MagicMock(), MagicMock()]  # 模板行 + 占位行

        data_list = [{"WLMS": "产品1", "GHJY": 100}]
        columns = [{"name": "产品名称", "field": "WLMS"}, {"name": "供货价", "field": "GHJY"}]

        # 不应该抛出异常
        expander.expand(mock_table, data_list, columns, start_row=1)



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

    def test_get_value_auto_number(self):
        """测试自动编号"""
        expander = RowExpander()

        data = {}
        col_config = {"name": "序号", "type": "auto_number", "field": ""}
        result = expander._get_value(data, col_config, 5)

        assert result == 5

    def test_get_value_with_transform_substring(self):
        """测试字符串截取转换"""
        expander = RowExpander()

        data = {"编码": "ABC12345"}
        col_config = {
            "name": "编码", "type": "text", "field": "编码",
            "transform": "substring", "params": {"start": 0, "length": 3}
        }
        result = expander._get_value(data, col_config, 1)

        assert result == "ABC"

    def test_get_value_with_transform_currency(self):
        """测试货币转换"""
        expander = RowExpander()

        data = {"价格": "99.999"}
        col_config = {
            "name": "价格", "type": "text", "field": "价格",
            "transform": "currency", "params": {"decimal_places": 2}
        }
        result = expander._get_value(data, col_config, 1)

        assert result == "100.00"

    def test_get_value_missing_field(self):
        """测试字段不存在"""
        expander = RowExpander()

        data = {"名称": "产品1"}
        col_config = {"name": "价格", "type": "text", "field": "价格"}
        result = expander._get_value(data, col_config, 1)

        assert result == ""

    def test_get_value_with_decimal(self):
        """测试小数类型"""
        expander = RowExpander()

        data = {"价格": 123.456}
        col_config = {"name": "价格", "type": "number", "field": "价格"}
        result = expander._get_value(data, col_config, 1)

        # 验证返回数字类型
        assert isinstance(result, (int, float))

    def test_get_value_none_value(self):
        """测试 None 值"""
        expander = RowExpander()

        data = {"价格": None}
        col_config = {"name": "价格", "type": "text", "field": "价格"}
        result = expander._get_value(data, col_config, 1)

        assert result == ""


class TestRowExpanderExpand:
    """RowExpander.expand 方法测试"""

    def test_expand_multiple_rows(self):
        """测试多行数据扩展"""
        expander = RowExpander()

        mock_table = MagicMock()
        mock_template_row = MagicMock()
        mock_placeholder_row = MagicMock()
        # 设置 _tr 属性以便内部代码可以操作
        mock_table.rows.__getitem__ = MagicMock(side_effect=lambda i: [mock_template_row, mock_placeholder_row][i])
        mock_table.rows.__len__ = MagicMock(return_value=2)
        mock_table._tr = [mock_template_row._tr, mock_placeholder_row._tr]

        data_list = [
            {"WLMS": "产品1", "GHJY": 100},
        ]
        columns = [
            {"name": "产品名称", "field": "WLMS"},
            {"name": "供货价", "field": "GHJY"}
        ]

        # 不应该抛出异常
        expander.expand(mock_table, data_list, columns, start_row=1)

    def test_expand_with_discount_template(self):
        """测试带折扣模板的扩展"""
        expander = RowExpander()

        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_table.rows = [mock_row]

        data_list = [{"WLMS": "产品1", "GHJY": 100, "JCJXJ": 85}]
        columns = [{"name": "产品名称", "field": "WLMS"}]
        discount_template = "扣率: {{JCJXJ}}%"

        # 不应该抛出异常
        expander.expand(mock_table, data_list, columns, discount_template=discount_template)

    def test_expand_with_merge_info(self):
        """测试带合并信息的扩展"""
        expander = RowExpander()

        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_table.rows = [mock_row]

        data_list = [{"WLMS": "产品1", "GHJY": 100}]
        columns = [{"name": "产品名称", "field": "WLMS"}]
        merge_info = {1: (85, 2)}

        # 不应该抛出异常
        expander.expand(mock_table, data_list, columns, start_row=1, merge_info=merge_info)

    def test_expand_replace_placeholder(self):
        """测试替换占位行"""
        expander = RowExpander()

        mock_table = MagicMock()
        mock_template_row = MagicMock()
        mock_placeholder_row = MagicMock()
        mock_table.rows = [mock_template_row, mock_placeholder_row]

        data_list = [{"WLMS": "产品1"}]
        columns = [{"name": "产品名称", "field": "WLMS"}]

        expander.expand(mock_table, data_list, columns, start_row=1, replace_placeholder=True)


class TestRowExpanderFill:
    """_fill_row 方法测试"""

    def test_fill_row(self):
        """测试填充行"""
        expander = RowExpander()

        mock_row = MagicMock()
        mock_cell1 = MagicMock()
        mock_cell1.paragraphs = [MagicMock()]
        mock_cell2 = MagicMock()
        mock_cell2.paragraphs = [MagicMock()]
        mock_row.cells = [mock_cell1, mock_cell2]

        data = {"WLMS": "产品1", "GHJY": 100}
        columns = [
            {"name": "产品名称", "field": "WLMS"},
            {"name": "供货价", "field": "GHJY"}
        ]

        # 不应该抛出异常
        expander._fill_row(mock_row, data, columns, 1)
