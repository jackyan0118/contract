"""表格行扩展器 - 动态扩展表格行."""

import logging
from typing import List, Dict, Any
from copy import deepcopy

from docx import Document
from docx.table import Table
from docx.oxml import OxmlElement

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
        start_row: int = 1,
        template_row_idx: int = -1,
        replace_placeholder: bool = False,
        has_speech_row: bool = True
    ) -> None:
        """扩展表格行

        Args:
            table: 表格对象
            data_list: 数据列表
            columns: 列配置列表
            start_row: 起始行索引（从该行开始插入数据）
            template_row_idx: 模板行索引（作为数据行的格式模板）
            replace_placeholder: 是否替换占位行（True=清空占位行作为第一条数据）
            has_speech_row: 是否有话术行（话术行不参与数据填充，需保留在末尾）
        """
        if not data_list:
            logger.warning("No data to expand")
            return

        data_count = len(data_list)

        if data_count == 1:
            # 只有1条数据：清空占位行，填充该数据
            if start_row < len(table.rows):
                placeholder_row = table.rows[start_row]
                for cell in placeholder_row.cells:
                    cell.text = ""
                self._fill_row(placeholder_row, data_list[0], columns, 1)
            logger.info(f"Filled 1 row (replaced placeholder)")
        else:
            # 大于1条数据：
            # 1. 找到话术行（包含 {{#话术}} 或 {{话术}}），保存为 Tr 元素
            # 2. 保存话术行内容
            # 3. 删除从 start_row 开始的所有数据行（保留标题行和话术行）
            # 4. 在话术行之前插入 N 行数据
            # 5. 填充数据行
            # 6. 对话术行进行文本替换

            # 1. 找到话术行（保存 Tr 元素而不是索引）
            speech_row = None
            speech_row_texts = []
            for row in table.rows:
                row_text = "".join(cell.text for cell in row.cells)
                if "{{#话术}}" in row_text or "{{话术}}" in row_text:
                    speech_row = row
                    speech_row_texts = [cell.text for cell in row.cells]
                    break

            # 如果没有找到话术行，使用最后一行
            if not speech_row and len(table.rows) > 1:
                speech_row = table.rows[-1]
                speech_row_texts = [cell.text for cell in speech_row.cells]

            if not speech_row:
                logger.warning("No speech row found")
                return

            # 保存话术行的 Tr 元素
            speech_tr = speech_row._tr

            # 获取表格的列宽（从 tblGrid 获取，这是 python-docx 打开文档后的标准宽度）
            tbl = table._tbl
            tblGrid = tbl.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblGrid')
            col_widths = []
            if tblGrid is not None:
                for col in tblGrid:
                    width = col.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                    if width:
                        col_widths.append(int(width))
                    else:
                        col_widths.append(0)

            # 2. 保存模板行的边框格式（不包括 tcW，因为 python-docx 会自动调整 tcW 为 tblGrid 的值）
            template_row = table.rows[template_row_idx] if template_row_idx >= 0 else table.rows[start_row]
            template_cell_formats = []
            for cell in template_row.cells:
                tc = cell._element
                tcPr = tc.find('.//{*}tcPr')
                if tcPr is not None:
                    # 复制整个 tcPr，但会覆盖 tcW 为 tblGrid 的值
                    template_cell_formats.append(deepcopy(tcPr))
                else:
                    template_cell_formats.append(None)

            # 3. 删除从 start_row 开始到话术行之前的所有行
            rows_to_remove = []
            for idx in range(start_row, len(table.rows) - 1):
                rows_to_remove.append(table.rows[idx]._element)

            for tr in rows_to_remove:
                parent = tr.getparent()
                if parent is not None:
                    parent.remove(tr)

            # 4. 在话术行之前插入 N 行数据
            target_cols = len(table.rows[0].cells) if table.rows else 7

            # 获取话术行在表格中的位置
            tr_list = list(tbl)
            speech_position = tr_list.index(speech_tr)

            for i in range(data_count):
                # 创建新行
                new_row = table.add_row()
                # 删除多余的单元格，只保留 target_cols 个
                while len(new_row.cells) > target_cols:
                    tr = new_row._tr
                    tc_list = tr.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
                    if len(tc_list) > target_cols:
                        tr.remove(tc_list[-1])

                # 应用单元格格式
                for cell_idx in range(len(new_row.cells)):
                    # 获取列宽（从 tblGrid）
                    col_width = col_widths[cell_idx] if cell_idx < len(col_widths) else 0

                    # 复制模板行的格式（边框等）
                    if cell_idx < len(template_cell_formats) and template_cell_formats[cell_idx] is not None:
                        dst_tc = new_row.cells[cell_idx]._element
                        dst_tcPr = dst_tc.find('.//{*}tcPr')
                        if dst_tcPr is None:
                            dst_tcPr = OxmlElement('w:tcPr')
                            dst_tc.insert(0, dst_tcPr)

                        # 复制除了 tcW 之外的所有格式
                        for src_child in template_cell_formats[cell_idx]:
                            if not src_child.tag.endswith('tcW'):
                                if dst_tcPr.find(src_child.tag) is None:
                                    dst_tcPr.append(deepcopy(src_child))

                    # 设置 tcW 为 tblGrid 的列宽
                    if col_width > 0:
                        dst_tc = new_row.cells[cell_idx]._element
                        dst_tcPr = dst_tc.find('.//{*}tcPr')
                        if dst_tcPr is None:
                            dst_tcPr = OxmlElement('w:tcPr')
                            dst_tc.insert(0, dst_tcPr)
                        # 删除旧的 tcW 并添加新的
                        existing_tcW = dst_tcPr.find('.//{*}tcW')
                        if existing_tcW is not None:
                            dst_tcPr.remove(existing_tcW)
                        new_tcW = OxmlElement('w:tcW')
                        new_tcW.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w', str(col_width))
                        new_tcW.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                        dst_tcPr.append(new_tcW)

                # 在话术行之前插入
                tbl.insert(speech_position + i, new_row._tr)

            # 5. 填充数据行
            for row_idx, data in enumerate(data_list):
                if start_row + row_idx < len(table.rows) - 1:
                    row = table.rows[start_row + row_idx]
                    self._fill_row(row, data, columns, row_idx + 1)

            # 6. 对话术行进行文本替换
            if speech_row_texts:
                last_row = table.rows[-1]
                for cell_idx, text in enumerate(speech_row_texts):
                    if cell_idx < len(last_row.cells):
                        last_row.cells[cell_idx].text = text

        logger.info(f"Expanded table with {data_count} rows")

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
