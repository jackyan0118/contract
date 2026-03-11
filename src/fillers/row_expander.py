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
            # 1. 首先保存话术行内容（重要！）
            # 2. 删除所有数据行（保留标题行）
            # 3. 添加 N+1 行（N条数据 + 1条话术）
            # 4. 填充数据，跳过最后一行（话术行）

            # 1. 保存话术行（表格最后一行）
            speech_row = table.rows[-1] if len(table.rows) > 1 else None
            speech_row_texts = []
            if speech_row:
                for cell in speech_row.cells:
                    speech_row_texts.append(cell.text)

            # 2. 删除占位行之后的所有行
            while len(table.rows) > start_row:
                if len(table.rows) > 1:
                    last_row = table.rows[-1]
                    last_row._element.getparent().remove(last_row._element)
                else:
                    break

            # 3. 添加 N+1 行（N条数据 + 1条话术）
            for i in range(data_count + 1):
                table.add_row()

            # 4. 填充数据（从 start_row 开始，填充 N 条）
            for row_idx, data in enumerate(data_list):
                table_row_idx = start_row + row_idx
                if table_row_idx >= len(table.rows) - 1:
                    break
                row = table.rows[table_row_idx]
                self._fill_row(row, data, columns, row_idx + 1)

            # 5. 最后一行是话术行，填充保存的话术内容
            if speech_row_texts:
                last_row = table.rows[-1]
                for cell_idx, text in enumerate(speech_row_texts):
                    if cell_idx < len(last_row.cells):
                        last_row.cells[cell_idx].text = text

        logger.info(f"Expanded table with {data_count} rows")

    def _ensure_rows(self, table: Table, required_rows: int, start_row: int, template_row_idx: int = -1, placeholder_deleted: bool = False) -> None:
        """确保表格有足够的行

        Args:
            table: 表格对象
            required_rows: 需要的数据行数
            start_row: 起始行索引
            template_row_idx: 模板行索引（用于复制格式）
            placeholder_deleted: 占位行是否已被删除
        """
        # 计算当前从 start_row 开始有多少行
        current_rows_from_start = max(0, len(table.rows) - start_row)
        rows_to_add = required_rows - current_rows_from_start

        if rows_to_add <= 0:
            # 如果不需要添加新行，清空模板行的内容
            if template_row_idx >= 0 and template_row_idx < len(table.rows):
                self._clear_template_row(table.rows[template_row_idx])
            return

        # 确定模板行
        if template_row_idx < 0:
            template_row_idx = start_row

        # 如果模板行索引超出范围，尝试使用最后一个有效行
        if template_row_idx >= len(table.rows):
            template_row_idx = len(table.rows) - 1

        # 复制模板行
        if template_row_idx >= 0:
            template_row = table.rows[template_row_idx]

            # 首先清空模板行的内容
            self._clear_template_row(template_row)

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

    def _clear_template_row(self, row) -> None:
        """清空模板行的内容（保留格式），但保留话术行"""
        for cell in row.cells:
            for para in cell.paragraphs:
                text = para.text
                # 如果这一行包含话术占位符，不清空，只替换占位符
                if "{{#话术}}" in text or "{{话术}}" in text or "{{/话术}}" in text:
                    # 替换话术占位符
                    from src.fillers.constants import DEFAULT_SPEECH_VARIABLES
                    text = text.replace("{{#话术}}", "").replace("{{/话术}}", "")
                    for var_name, default_value in DEFAULT_SPEECH_VARIABLES.items():
                        text = text.replace(f"{{{{{var_name}}}}}", default_value)
                    # 更新段落文本
                    if para.runs:
                        for run in para.runs:
                            run.text = ""
                        para.runs[0].text = text
                else:
                    # 清空其他行的内容
                    for run in para.runs:
                        run.text = ""

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

    def _insert_row_at(self, table: Table, new_row, position: int) -> None:
        """在指定位置插入行

        Args:
            table: 表格对象
            new_row: 新行
            position: 插入位置索引
        """
        # 获取表格的 tbl 元素
        tbl = table._tbl
        # 获取 tr 元素
        new_tr = new_row._tr
        # 找到插入位置的目标 tr
        tr_list = tbl.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')

        if position < len(tr_list):
            target_tr = tr_list[position]
            tbl.insert(list(tbl).index(target_tr), new_tr)
