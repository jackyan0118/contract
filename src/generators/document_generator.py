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
from src.fillers.data_filler import DataFiller, FilterCondition
from src.fillers.row_expander import RowExpander
from src.fillers.format_preserver import FormatPreserver
from src.fillers.speech_processor import SpeechProcessor, Speech
from src.fillers.constants import DEFAULT_SPEECH_VARIABLES, HEADER_TO_FIELD
from src.config.template_loader import TemplateLoader, TemplateMetadataModel, ColumnType
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

    def __init__(self, template_dir: str = "docs/template",
                 config_dir: str = "config/template_metadata/templates"):
        self.template_dir = Path(template_dir)
        self.config_dir = Path(config_dir)
        self.template_reader = WordTemplateReader(template_dir)
        self.template_loader = TemplateLoader(config_dir)
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
        # 尝试加载模板配置
        template_config: Optional[TemplateMetadataModel] = None
        try:
            # 优先使用 template.id
            template_config = self.template_loader.load(template.id)
        except FileNotFoundError:
            # 如果找不到，尝试从文件名提取配置名
            # 例如：template.file = "模板2：通用生化产品价格模版.docx" -> config = "模板2.yaml"
            config_name = template.file.replace(".docx", "").split("：")[0]
            try:
                template_config = self.template_loader.load(config_name)
                logger.debug(f"Loaded template config using filename: {config_name}")
            except FileNotFoundError:
                logger.debug(f"No template config found for {config_name}, using default")
            except Exception as e:
                logger.warning(f"Failed to load template config: {e}")
        except Exception as e:
            logger.warning(f"Failed to load template config: {e}")

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

            # 填充数据（带模板配置）
            self._fill_document(doc, template_config, quote_data, detail_data_list)

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
            import traceback
            logger.error(traceback.format_exc())
            return GenerationResult(
                success=False,
                template_id=template.id,
                error=str(e)
            )

    def _fill_document(
        self,
        doc: Document,
        template_config: Optional[TemplateMetadataModel],
        quote_data: Dict[str, Any],
        detail_data_list: List[Dict[str, Any]]
    ) -> None:
        """填充文档内容

        Args:
            doc: Word 文档对象
            template_config: 模板配置（可选）
            quote_data: 报价单主表数据
            detail_data_list: 明细数据列表
        """
        # 1. 填充段落占位符
        self._fill_paragraphs(doc, template_config, quote_data)

        # 2. 填充表格（支持 detail_filter）
        self._fill_tables(doc, template_config, detail_data_list, quote_data)

        # 3. 处理话术（完整集成）
        self._process_speeches(doc, template_config, quote_data)

    def _fill_paragraphs(self, doc: Document,
                         template_config: Optional[TemplateMetadataModel],
                         data: Dict[str, Any]) -> None:
        """填充段落占位符

        Args:
            doc: Word 文档对象
            template_config: 模板配置（可选）
            data: 数据字典
        """
        # 获取段落占位符配置（优先使用模板配置，否则使用默认值）
        if template_config and template_config.paragraph_placeholders:
            placeholders = template_config.paragraph_placeholders
        else:
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

    def _fill_tables(self, doc: Document,
                     template_config: Optional[TemplateMetadataModel],
                     data_list: List[Dict[str, Any]],
                     quote_data: Dict[str, Any] = None) -> None:
        """填充表格

        Args:
            doc: Word 文档对象
            template_config: 模板配置（可选）
            data_list: 明细数据列表
            quote_data: 报价单主表数据（用于话术处理）
        """
        if quote_data is None:
            quote_data = {}
        for table in doc.tables:
            # 查找明细表和话术行
            is_detail_table = False
            template_row_idx = -1
            speech_row_idx = -1
            speech_row_content = None

            # 第一遍：清除所有占位符并找到关键行
            for row_idx, row in enumerate(table.rows):
                row_text = ""
                for cell in row.cells:
                    for para in cell.paragraphs:
                        row_text += para.text

                # 检查是否是明细表模板行
                if "{{#明细表}}" in row_text:
                    is_detail_table = True
                    template_row_idx = row_idx
                    # 清除标记文本
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            para.text = para.text.replace("{{#明细表}}", "").replace("{{/明细表}}", "")

                # 检查是否是话术行
                if "{{#话术}}" in row_text or "{{话术}}" in row_text:
                    speech_row_idx = row_idx
                    # 保存话术行内容
                    speech_row_content = []
                    for cell in row.cells:
                        cell_text = ""
                        for para in cell.paragraphs:
                            cell_text += para.text
                        speech_row_content.append(cell_text)

            if not is_detail_table:
                continue

            # 应用 detail_filter 过滤数据
            filtered_data = self._apply_detail_filter(template_config, data_list)

            # 解析列配置（优先使用模板配置）
            if template_config and template_config.table:
                columns = self._parse_table_columns_from_config(template_config.table)
            else:
                columns = self._parse_table_columns(table)

            # 填充数据 - 从占位行位置开始（替换占位行）
            # 根据是否有话术行设置 has_speech_row 参数
            has_speech_row = speech_row_content is not None
            self.row_expander.expand(table, filtered_data, columns, template_row_idx, template_row_idx, True, has_speech_row)

            # 替换最后一行（话术行）中的占位符
            # 注意：expand 后原始话术行已被数据覆盖，需要使用之前保存的 speech_row_content
            if speech_row_content and len(table.rows) > 0:
                # 获取实际话术内容
                speech_contents = self._get_speech_contents(template_config, quote_data)
                full_speech = "\n".join(speech_contents)

                # 使用保存的话术行内容替换最后一行
                speech_row = table.rows[-1]
                for cell_idx, cell in enumerate(speech_row.cells):
                    if cell_idx < len(speech_row_content):
                        # 使用保存的话术行内容作为基础
                        text = speech_row_content[cell_idx]
                    else:
                        text = ""

                    if "{{#话术}}" in text or "{{话术}}" in text or "{{/话术}}" in text:
                        # Cell 0 保留原文本"其他"
                        if cell_idx == 0:
                            # 只清除话术标记
                            text = text.replace("{{#话术}}", "")
                            text = text.replace("{{/话术}}", "")
                        else:
                            # Cell 1-6 替换为话术内容
                            text = text.replace("{{#话术}}", full_speech)
                            text = text.replace("{{/话术}}", "")
                            text = text.replace("{{话术}}", full_speech)
                        # 替换变量占位符
                        for var_name, default_value in DEFAULT_SPEECH_VARIABLES.items():
                            text = text.replace(f"{{{{{var_name}}}}}", default_value)

                    # 清空单元格并设置新内容
                    cell.text = ""
                    if cell.paragraphs:
                        cell.paragraphs[0].text = text

            # 处理话术占位符（表格单元格中）
            self._process_table_speeches(table)

    def _apply_detail_filter(self,
                            template_config: Optional[TemplateMetadataModel],
                            data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用明细过滤规则

        Args:
            template_config: 模板配置
            data_list: 原始数据列表

        Returns:
            过滤后的数据列表
        """
        if not template_config or not template_config.detail_filter:
            return data_list

        filter_config = template_config.detail_filter

        if not filter_config.filter_rules:
            return data_list

        # 合并所有规则的过滤条件
        all_conditions = []
        for rule in filter_config.filter_rules:
            for cond in rule.conditions:
                all_conditions.append(FilterCondition(
                    field=cond.field,
                    operator=cond.operator,
                    value=cond.value
                ))

        if not all_conditions:
            return data_list

        # 使用 DataFiller 过滤
        filtered = self.data_filler.filter_data(data_list, all_conditions)
        logger.info(f"Filtered {len(data_list)} rows to {len(filtered)} rows")
        return filtered

    def _parse_table_columns_from_config(self, table_config) -> List[Dict[str, str]]:
        """从模板配置解析表格列

        Args:
            table_config: 表格配置模型

        Returns:
            列配置列表
        """
        columns = []
        for col in table_config.columns:
            # auto_number 类型不需要 source_field
            field = col.source_field if col.type != ColumnType.AUTO_NUMBER else ""
            columns.append({
                "name": col.name,
                "field": field,
                "type": col.type,
                "transform": col.transform,
                "params": col.params
            })
        return columns

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
        """从表头推断字段

        使用 constants.HEADER_TO_FIELD
        """
        for key, field in HEADER_TO_FIELD.items():
            if key in header_text:
                return field

        return f"col_{col_idx}"

    def _replace_variables(self, text: str, data: Dict[str, Any]) -> str:
        """替换变量占位符

        使用 constants.DEFAULT_SPEECH_VARIABLES
        """
        for var_name, default_value in DEFAULT_SPEECH_VARIABLES.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in text:
                value = data.get(var_name, default_value)
                text = text.replace(placeholder, str(value))

        return text

    def _process_speeches(self, doc: Document,
                         template_config: Optional[TemplateMetadataModel],
                         data: Dict[str, Any]) -> None:
        """处理话术占位符（完整集成）

        Args:
            doc: Word 文档对象
            template_config: 模板配置（可选）
            data: 数据字典
        """
        # 如果没有模板配置，简化处理
        if not template_config or not template_config.speeches:
            self._process_speeches_simple(doc)
            return

        # 转换为 Speech 对象
        speeches = []
        for s in template_config.speeches:
            speech = Speech(
                id=s.id,
                type=s.type,
                content=s.content,
                mutex_group=s.mutex_group,
                variables={v.name: v.default for v in s.variables},
                conditions=[FilterCondition(field=c.field, operator=c.operator, value=c.value)
                          for c in s.conditions]
            )
            speeches.append(speech)

        # 处理话术
        speech_contents = self.speech_processor.process_speeches(speeches, data)

        # 填充话术占位符
        for para in doc.paragraphs:
            text = para.text

            if "{{#话术}}" in text or "{{话术}}" in text:
                # 合并所有话术内容
                full_speech = "\n".join(speech_contents)
                text = text.replace("{{#话术}}", "")
                text = text.replace("{{/话术}}", "")
                text = text.replace("{{话术}}", full_speech)

            if text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = text

    def _process_speeches_simple(self, doc: Document) -> None:
        """简化处理话术占位符（无模板配置时）"""
        for para in doc.paragraphs:
            text = para.text

            if "{{#话术}}" in text or "{{话术}}" in text:
                # 简化：直接移除占位符
                text = text.replace("{{#话术}}", "")
                text = text.replace("{{/话术}}", "")
                # 移除话术变量占位符
                for var_name in DEFAULT_SPEECH_VARIABLES.keys():
                    placeholder = f"{{{{{var_name}}}}}"
                    text = text.replace(placeholder, DEFAULT_SPEECH_VARIABLES[var_name])

            if text != para.text:
                for run in para.runs:
                    run.text = ""
                if para.runs:
                    para.runs[0].text = text

    def _process_table_speeches(self, table) -> None:
        """处理表格中的话术占位符"""
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    text = para.text
                    if "{{#话术}}" in text or "{{话术}}" in text or "{{/话术}}" in text:
                        # 清除话术标记
                        text = text.replace("{{#话术}}", "")
                        text = text.replace("{{/话术}}", "")
                        # 替换话术变量
                        for var_name, default_value in DEFAULT_SPEECH_VARIABLES.items():
                            placeholder = f"{{{{{var_name}}}}}"
                            text = text.replace(placeholder, default_value)

                        # 更新段落文本
                        if text != para.text:
                            for run in para.runs:
                                run.text = ""
                            if para.runs:
                                para.runs[0].text = text

    def _get_speech_contents(
        self,
        template_config: Optional[TemplateMetadataModel],
        data: Dict[str, Any]
    ) -> List[str]:
        """获取话术内容列表

        Args:
            template_config: 模板配置（可选）
            data: 数据字典

        Returns:
            话术内容列表
        """
        # 如果没有模板配置，返回空列表
        if not template_config or not template_config.speeches:
            return []

        # 转换为 Speech 对象
        speeches = []
        for s in template_config.speeches:
            speech = Speech(
                id=s.id,
                type=s.type,
                content=s.content,
                mutex_group=s.mutex_group,
                variables={v.name: v.default for v in s.variables},
                conditions=[FilterCondition(field=c.field, operator=c.operator, value=c.value)
                          for c in s.conditions]
            )
            speeches.append(speech)

        # 处理话术
        speech_contents = self.speech_processor.process_speeches(speeches, data)
        return speech_contents


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
        """获取话术内容列表

        Args:
            template_config: 模板配置（可选）
            data: 数据字典

        Returns:
            话术内容列表
        """
        # 如果没有模板配置，返回空列表
        if not template_config or not template_config.speeches:
            return []

        # 转换为 Speech 对象
        speeches = []
        for s in template_config.speeches:
            speech = Speech(
                id=s.id,
                type=s.type,
                content=s.content,
                mutex_group=s.mutex_group,
                variables={v.name: v.default for v in s.variables},
                conditions=[FilterCondition(field=c.field, operator=c.operator, value=c.value)
                          for c in s.conditions]
            )
            speeches.append(speech)

        # 处理话术
        speech_contents = self.speech_processor.process_speeches(speeches, data)
        return speech_contents
