"""数据填充引擎 - 将数据填充到 Word 模板."""

import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)


# 字段映射配置
FIELD_MAPPING = {
    "产品细分": ("CPXF", None),
    "定价组": ("DJZ", "DJZMC"),
    "定价组名称": ("DJZ", "DJZMC"),
    "是否集采": ("SFJC", None),
    "供货价类型": ("BNGHJLX", "BNGHHJLXZ"),
    "物料生成来源": ("LYXH", None),
}


@dataclass
class FilterCondition:
    """过滤条件"""
    field: str
    operator: str  # =, !=, contains, in, not_in, >, <, >=, <=
    value: Any


@dataclass
class FilterRule:
    """过滤规则"""
    id: str
    name: str
    conditions: List[FilterCondition] = field(default_factory=list)


@dataclass
class SpeechConfig:
    """话术配置"""
    id: str
    type: str  # conditional, fixed
    mutex_group: Optional[str] = None
    conditions: List[FilterCondition] = field(default_factory=list)
    content: str = ""
    variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class ColumnConfig:
    """列配置"""
    name: str
    source_field: str
    source_table: str = "UF_HTJGKST_DT1"
    transform: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)


class DataFiller:
    """数据填充引擎"""

    def __init__(self):
        self.operators = {
            "=": self._op_equals,
            "!=": self._op_not_equals,
            "contains": self._op_contains,
            "in": self._op_in,
            "not_in": self._op_not_in,
            ">": self._op_greater,
            "<": self._op_less,
            ">=": self._op_greater_equal,
            "<=": self._op_less_equal,
        }

    def fill_paragraphs(
        self,
        doc: Document,
        placeholders: Dict[str, str],
        data: Dict[str, Any]
    ) -> None:
        """填充段落占位符

        Args:
            doc: Word 文档对象
            placeholders: 占位符字典
            data: 数据字典
        """
        for para in doc.paragraphs:
            text = para.text

            # 替换占位符
            for key, value in placeholders.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in text:
                    # 优先使用传入的值，否则使用占位符配置的值
                    actual_value = data.get(key, value)
                    text = text.replace(placeholder, str(actual_value))

            # 替换变量占位符
            text = self._replace_variables(text, data)

            # 更新段落文本（保留格式）
            if text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = text
                else:
                    para.add_run(text)

    def fill_table(
        self,
        table: Table,
        columns: List[ColumnConfig],
        data_list: List[Dict[str, Any]],
        start_row: int = 1
    ) -> None:
        """填充表格数据

        Args:
            table: Word 表格对象
            columns: 列配置列表
            data_list: 数据行列表
            start_row: 数据起始行索引
        """
        if not data_list:
            logger.warning("No data to fill in table")
            return

        # 确保表格有足够的行
        required_rows = start_row + len(data_list)
        self._ensure_table_rows(table, required_rows)

        # 填充数据行
        for row_idx, data in enumerate(data_list):
            table_row_idx = start_row + row_idx

            if table_row_idx >= len(table.rows):
                break

            row = table.rows[table_row_idx]

            for col_idx, col_config in enumerate(columns):
                if col_idx >= len(row.cells):
                    break

                cell = row.cells[col_idx]
                value = self._get_cell_value(data, col_config)

                # 更新单元格文本
                for para in cell.paragraphs:
                    para.text = ""
                cell.text = str(value)

    def filter_data(
        self,
        data_list: List[Dict[str, Any]],
        conditions: List[FilterCondition]
    ) -> List[Dict[str, Any]]:
        """过滤数据

        Args:
            data_list: 原始数据列表
            conditions: 过滤条件列表

        Returns:
            过滤后的数据列表
        """
        if not conditions:
            return data_list

        filtered = []
        for data in data_list:
            if self._match_conditions(data, conditions):
                filtered.append(data)

        logger.info(f"Filtered {len(data_list)} rows to {len(filtered)} rows")
        return filtered

    def _match_conditions(
        self,
        data: Dict[str, Any],
        conditions: List[FilterCondition]
    ) -> bool:
        """检查数据是否满足所有条件"""
        for cond in conditions:
            if not self._match_condition(data, cond):
                return False
        return True

    def _match_condition(
        self,
        data: Dict[str, Any],
        condition: FilterCondition
    ) -> bool:
        """检查单个条件"""
        # 获取字段值（考虑字段映射）
        field_value = self._get_field_value(data, condition.field)

        # 获取操作符函数
        op_func = self.operators.get(condition.operator)
        if not op_func:
            logger.warning(f"Unknown operator: {condition.operator}")
            return True

        return op_func(field_value, condition.value)

    def _get_field_value(
        self,
        data: Dict[str, Any],
        field: str
    ) -> Any:
        """获取字段值（考虑字段映射）"""
        # 直接查找
        if field in data:
            return data[field]

        # 查找映射字段
        if field in FIELD_MAPPING:
            id_field, name_field = FIELD_MAPPING[field]
            if id_field and id_field in data:
                return data[id_field]
            if name_field and name_field in data:
                return data[name_field]

        return None

    def _op_equals(self, field_value: Any, expected: Any) -> bool:
        """等于操作符"""
        return str(field_value).strip() == str(expected).strip()

    def _op_not_equals(self, field_value: Any, expected: Any) -> bool:
        """不等于操作符"""
        return str(field_value).strip() != str(expected).strip()

    def _op_contains(self, field_value: Any, expected: Any) -> bool:
        """包含操作符"""
        return str(expected) in str(field_value)

    def _op_in(self, field_value: Any, expected: List[Any]) -> bool:
        """在列表中操作符"""
        return field_value in expected

    def _op_not_in(self, field_value: Any, expected: List[Any]) -> bool:
        """不在列表中操作符"""
        return field_value not in expected

    def _op_greater(self, field_value: Any, expected: Any) -> bool:
        """大于操作符"""
        try:
            return float(field_value) > float(expected)
        except (TypeError, ValueError):
            return False

    def _op_less(self, field_value: Any, expected: Any) -> bool:
        """小于操作符"""
        try:
            return float(field_value) < float(expected)
        except (TypeError, ValueError):
            return False

    def _op_greater_equal(self, field_value: Any, expected: Any) -> bool:
        """大于等于操作符"""
        try:
            return float(field_value) >= float(expected)
        except (TypeError, ValueError):
            return False

    def _op_less_equal(self, field_value: Any, expected: Any) -> bool:
        """小于等于操作符"""
        try:
            return float(field_value) <= float(expected)
        except (TypeError, ValueError):
            return False

    def _get_cell_value(
        self,
        data: Dict[str, Any],
        col_config: ColumnConfig
    ) -> Any:
        """获取单元格值"""
        field = col_config.source_field

        # 自动编号
        if col_config.type == "auto_number":
            return ""

        # 获取原始值
        value = data.get(field)

        # 应用转换
        if value is None:
            return ""

        if col_config.transform == "substring":
            start = col_config.params.get("start", 0)
            length = col_config.params.get("length")
            if length:
                return str(value)[start:start + length]
            return str(value)[start:]

        if col_config.transform == "currency":
            decimals = col_config.params.get("decimals", 2)
            try:
                return f"{float(value):.{decimals}f}"
            except (TypeError, ValueError):
                return value

        return value

    def _replace_variables(self, text: str, data: Dict[str, Any]) -> str:
        """替换变量占位符"""
        # 匹配 {{变量名}} 格式
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, text)

        for var_name in matches:
            placeholder = f"{{{{{var_name}}}}}"
            value = data.get(var_name, "")
            text = text.replace(placeholder, str(value))

        return text

    def _ensure_table_rows(self, table: Table, required_rows: int) -> None:
        """确保表格有足够的行"""
        current_rows = len(table.rows)

        if current_rows < required_rows:
            # 复制最后一行作为模板
            template_row = table.rows[-1] if table.rows else None

            for _ in range(required_rows - current_rows):
                if template_row:
                    # 复制模板行
                    new_row = table.add_row()
                    for src_cell, dst_cell in zip(template_row.cells, new_row.cells):
                        for src_para, dst_para in zip(src_cell.paragraphs, dst_cell.paragraphs):
                            for src_run, dst_run in zip(src_para.runs, dst_para.runs):
                                new_run = dst_para.add_run(src_run.text)
                                # 复制格式
                                if src_run.font.name:
                                    new_run.font.name = src_run.font.name
                                if src_run.font.size:
                                    new_run.font.size = src_run.font.size
                else:
                    table.add_row()
