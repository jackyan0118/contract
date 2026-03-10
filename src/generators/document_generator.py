"""文档生成器 - 根据模板和数据生成 Word 文档."""

import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from docx import Document

from src.readers.word_template_reader import WordTemplateReader
from src.fillers.data_filler import DataFiller
from src.fillers.row_expander import RowExpander
from src.fillers.format_preserver import FormatPreserver
from src.fillers.speech_processor import SpeechProcessor
from src.models.template_rule import TemplateRule
from src.exceptions import DocumentGenerateException

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """生成结果"""
    success: bool
    file_path: Optional[str] = None
    template_id: Optional[str] = None
    error: Optional[str] = None


class DocumentGenerator:
    """文档生成器"""

    def __init__(self, template_dir: str = "docs/template"):
        self.template_dir = Path(template_dir)
        self.template_reader = WordTemplateReader(template_dir)
        self.data_filler = DataFiller()
        self.row_expander = RowExpander()
        self.format_preserver = FormatPreserver()
        self.speech_processor = SpeechProcessor()

    def generate(
        self,
        template: TemplateRule,
        quote_data: Dict[str, Any],
        detail_data_list: List[Dict[str, Any]],
        output_dir: str = "output"
    ) -> GenerationResult:
        """生成文档

        Args:
            template: 模板规则
            quote_data: 报价单主表数据
            detail_data_list: 报价单明细数据列表
            output_dir: 输出目录

        Returns:
            GenerationResult: 生成结果
        """
        try:
            template_path = self.template_dir / template.file

            if not template_path.exists():
                return GenerationResult(
                    success=False,
                    template_id=template.id,
                    error=f"Template file not found: {template.file}"
                )

            # 复制模板到输出目录
            output_path = Path(output_dir) / f"{template.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(template_path, output_path)

            # 打开文档
            doc = Document(output_path)

            # 填充数据
            self._fill_document(doc, quote_data, detail_data_list)

            # 保存文档
            doc.save(output_path)

            logger.info(f"Generated document: {output_path}")

            return GenerationResult(
                success=True,
                file_path=str(output_path),
                template_id=template.id
            )

        except Exception as e:
            logger.error(f"Failed to generate document: {e}")
            return GenerationResult(
                success=False,
                template_id=template.id,
                error=str(e)
            )

    def _fill_document(
        self,
        doc: Document,
        quote_data: Dict[str, Any],
        detail_data_list: List[Dict[str, Any]]
    ) -> None:
        """填充文档内容"""
        # 1. 填充段落占位符
        self._fill_paragraphs(doc, quote_data)

        # 2. 填充表格
        self._fill_tables(doc, detail_data_list)

        # 3. 处理话术
        self._process_speeches(doc, quote_data)

    def _fill_paragraphs(self, doc: Document, data: Dict[str, Any]) -> None:
        """填充段落占位符"""
        # 定义标准占位符
        placeholders = {
            "标题": data.get("标题", ""),
            "副标题": data.get("副标题", ""),
            "金额单位": data.get("金额单位", "元"),
            "报价单号": data.get("报价单号", ""),
            "客户名称": data.get("客户名称", ""),
        }

        for para in doc.paragraphs:
            text = para.text

            # 替换占位符
            for key, value in placeholders.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in text:
                    text = text.replace(placeholder, str(value))

            # 替换变量占位符（如 {{肝功扣率}}）
            text = self._replace_variables(text, data)

            # 更新段落
            if text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = text

    def _fill_tables(self, doc: Document, data_list: List[Dict[str, Any]]) -> None:
        """填充表格"""
        for table in doc.tables:
            # 查找明细表
            is_detail_table = False
            start_row = 0

            for row_idx, row in enumerate(table.rows):
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "{{#明细表}}" in para.text:
                            is_detail_table = True
                            start_row = row_idx + 1
                            # 清除标记文本
                            para.text = para.text.replace("{{#明细表}}", "").replace("{{/明细表}}", "")
                            break
                if is_detail_table:
                    break

            if not is_detail_table:
                continue

            # 解析列配置
            columns = self._parse_table_columns(table)

            # 填充数据
            self.row_expander.expand(table, data_list, columns, start_row)

    def _parse_table_columns(self, table) -> List[Dict[str, str]]:
        """解析表格列配置"""
        columns = []

        if not table.rows:
            return columns

        # 第一行是表头
        header_row = table.rows[0]

        for idx, cell in enumerate(header_row.cells):
            text = cell.text.strip()
            # 移除占位符标记
            text = re.sub(r'\{\{.*\}\}', '', text).strip()

            # 推断字段
            field = self._infer_field(text, idx)
            col_type = "auto_number" if "序号" in text else "text"

            columns.append({
                "name": text,
                "field": field,
                "type": col_type
            })

        return columns

    def _infer_field(self, header_text: str, col_idx: int) -> str:
        """从表头推断字段"""
        mapping = {
            "序号": "序号",
            "物料编码": "WLDM",
            "SAP代码": "WLDM",
            "品名": "WLMS",
            "产品名称": "WLMS",
            "简称": "WLMS",
            "规格": "GG",
            "规格型号": "GG",
            "包装规格": "GG",
            "零售价": "LSJ",
            "供货价": "GHJY",
            "产品类别": "CPXF",
            "分类": "CPXF",
        }

        for key, field in mapping.items():
            if key in header_text:
                return field

        return f"col_{col_idx}"

    def _replace_variables(self, text: str, data: Dict[str, Any]) -> str:
        """替换变量占位符"""
        # 默认变量
        variables = {
            "肝功扣率": "85",
            "通用扣率": "70",
            "北极星扣率": "25",
            "耗材扣率": "50",
        }

        for var_name, default_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in text:
                value = data.get(var_name, default_value)
                text = text.replace(placeholder, str(value))

        return text

    def _process_speeches(self, doc: Document, data: Dict[str, Any]) -> None:
        """处理话术占位符"""
        # 查找话术区域
        for para in doc.paragraphs:
            text = para.text

            # 查找话术标记
            if "{{#话术}}" in text:
                # 简化处理：查找所有条件话术占位符
                # 实际应该根据模板配置生成话术
                speech_pattern = r'\{\{(\w+)\}\}'
                matches = re.findall(speech_pattern, text)

                if matches:
                    # 简化：直接移除占位符
                    for match in matches:
                        placeholder = f"{{{{{match}}}}}"
                        text = text.replace(placeholder, "")

                # 移除标记
                text = text.replace("{{#话术}}", "").replace("{{/话术}}", "")

            if text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = text


class MultiDocumentGenerator:
    """多文档生成器 - 生成多个文档并打包"""

    def __init__(self, template_dir: str = "docs/template"):
        self.generator = DocumentGenerator(template_dir)

    def generate_batch(
        self,
        templates: List[TemplateRule],
        quote_data: Dict[str, Any],
        detail_data_list: List[Dict[str, Any]],
        output_dir: str = "output"
    ) -> List[GenerationResult]:
        """批量生成文档

        Args:
            templates: 模板列表
            quote_data: 报价单数据
            detail_data_list: 明细数据列表
            output_dir: 输出目录

        Returns:
            生成结果列表
        """
        results = []

        for template in templates:
            result = self.generator.generate(
                template, quote_data, detail_data_list, output_dir
            )
            results.append(result)

            if result.success:
                logger.info(f"Generated: {result.template_id} -> {result.file_path}")
            else:
                logger.error(f"Failed: {result.template_id} -> {result.error}")

        return results
