"""表格行扩展器 - 动态扩展表格行."""

import logging
from typing import List, Dict, Any

from docx import Document
from docx.table import Table

from src.fillers.format_preserver import FormatPreserver

logger = logging.getLogger(__name__)


class RowExpander:
    """表格行扩展器"""

    def __init__(self):
        self.format_preserver = FormatPreserver()

    def expand(
        self,
        table: Table,
        data_list: List[Dict[str, Any]],
        columns: List[Dict[str, str]],
        start_row: int = 1
    ) -> None:
        """扩展表格行

        Args:
            table: 表格对象
            data_list: 数据列表
            columns: 列配置列表
            start_row: 起始行索引
        """
        if not data_list:
            logger.warning("No data to expand")
            return

        # 确保有足够的行
        self._ensure_rows(table, len(data_list), start_row)

        # 填充数据
        for row_idx, data in enumerate(data_list):
            table_row_idx = start_row + row_idx

            if table_row_idx >= len(table.rows):
                break

            row = table.rows[table_row_idx]
            self._fill_row(row, data, columns, row_idx + 1)

        logger.info(f"Expanded table with {len(data_list)} rows")

    def _ensure_rows(self, table: Table, required_rows: int, start_row: int) -> None:
        """确保表格有足够的行"""
        # 计算需要的行数
        current_data_rows = len(table.rows) - start_row
        rows_to_add = required_rows - current_data_rows

        if rows_to_add <= 0:
            return

        # 复制模板行
        if start_row < len(table.rows):
            template_row = table.rows[start_row]

            for _ in range(rows_to_add):
                new_row = table.add_row()
                # 复制格式 - 使用索引遍历
                for cell_idx in range(len(template_row.cells)):
                    src_cell = template_row.cells[cell_idx]
                    dst_cell = new_row.cells[cell_idx]

                    # 复制每个段落（按索引）
                    src_paras = src_cell.paragraphs
                    dst_paras = dst_cell.paragraphs

                    if src_paras:
                        # 源单元格有段落
                        for para_idx in range(len(src_paras)):
                            src_para = src_paras[para_idx]

                            # 确保目标单元格有足够的段落
                            while len(dst_paras) <= para_idx:
                                dst_cell.add_paragraph()
                                dst_paras = dst_cell.paragraphs  # 刷新引用

                            dst_para = dst_paras[para_idx]

                            # 复制文本内容（清空）
                            for dst_run in dst_para.runs:
                                dst_run.text = ""

                            # 如果没有 Run，添加一个空的
                            if not dst_para.runs:
                                dst_para.add_run("")

                            # 复制格式到第一个 Run
                            if src_para.runs and dst_para.runs:
                                src_run = src_para.runs[0]
                                dst_run = dst_para.runs[0]
                                self._copy_run_format(src_run, dst_run)
                    else:
                        # 源单元格没有段落，添加一个空段落
                        dst_cell.add_paragraph()

            logger.debug(f"Added {rows_to_add} rows to table")
        else:
            # 没有模板行，直接添加
            for _ in range(rows_to_add):
                table.add_row()

    def _fill_row(
        self,
        row,
        data: Dict[str, Any],
        columns: List[Dict[str, str]],
        row_number: int
    ) -> None:
        """填充行数据"""
        for col_idx, col_config in enumerate(columns):
            if col_idx >= len(row.cells):
                break

            cell = row.cells[col_idx]
            value = self._get_value(data, col_config, row_number)

            # 更新单元格
            for para in cell.paragraphs:
                para.text = ""

            cell.text = str(value)

    def _get_value(
        self,
        data: Dict[str, Any],
        col_config: Dict[str, str],
        row_number: int
    ) -> Any:
        """获取单元格值"""
        col_type = col_config.get("type", "text")
        field = col_config.get("field", "")

        # 自动编号
        if col_type == "auto_number":
            return row_number

        # 获取字段值
        value = data.get(field, "")

        if value is None:
            return ""

        # 转换
        transform = col_config.get("transform")
        if transform == "substring":
            start = col_config.get("params", {}).get("start", 0)
            length = col_config.get("params", {}).get("length")
            if length:
                return str(value)[start:start + length]
            return str(value)[start:]

        if transform == "currency":
            decimals = col_config.get("params", {}).get("decimals", 2)
            try:
                return f"{float(value):.{decimals}f}"
            except (TypeError, ValueError):
                return value

        return value

    def _copy_run_format(self, source_run, target_run) -> None:
        """复制 Run 格式"""
        if source_run.font.name:
            target_run.font.name = source_run.font.name
        if source_run.font.size:
            target_run.font.size = source_run.font.size
        if source_run.font.bold is not None:
            target_run.font.bold = source_run.font.bold
        if source_run.font.italic is not None:
            target_run.font.italic = source_run.font.italic
