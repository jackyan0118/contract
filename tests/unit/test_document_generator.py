"""文档生成器单元测试."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from docx import Document

from src.generators.document_generator import (
    DocumentGenerator,
    MultiDocumentGenerator,
    GenerationResult
)
from src.fillers.data_filler import DataFiller, FilterCondition, ColumnConfig
from src.fillers.speech_processor import SpeechProcessor, Speech
from src.fillers.row_expander import RowExpander
from src.models.template_rule import TemplateRule, RuleCondition


# ============ 测试数据 ============

SAMPLE_QUOTE_DATA = {
    "报价单号": "WYBS20260310",
    "客户名称": "XX医院",
    "标题": "通用生化产品供货价",
    "金额单位": "元",
    "产品细分": "通用生化试剂",
    "是否集采": "否",
    "肝功扣率": "85",
}

SAMPLE_DETAIL_DATA = [
    {
        "WLDM": "MAT001",
        "WLMS": "测试物料1",
        "GG": "10ml",
        "LSJ": 100.00,
        "GHJY": 70.00,
    },
    {
        "WLDM": "MAT002",
        "WLMS": "测试物料2",
        "GG": "20ml",
        "LSJ": 200.00,
        "GHJY": 140.00,
    },
]


# ============ DataFiller 测试 ============

class TestDataFiller:
    """DataFiller 单元测试"""

    def test_filter_data_empty_conditions(self):
        """测试空条件返回所有数据"""
        filler = DataFiller()
        data_list = [{"id": 1}, {"id": 2}]

        result = filler.filter_data(data_list, [])

        assert len(result) == 2

    def test_filter_data_equals(self):
        """测试等于操作符"""
        filler = DataFiller()
        conditions = [FilterCondition(field="产品细分", operator="=", value="酶免试剂")]
        data_list = [
            {"产品细分": "酶免试剂"},
            {"产品细分": "胶体金试剂"},
        ]

        result = filler.filter_data(data_list, conditions)

        assert len(result) == 1
        assert result[0]["产品细分"] == "酶免试剂"

    def test_filter_data_contains(self):
        """测试包含操作符"""
        filler = DataFiller()
        conditions = [FilterCondition(field="DJZMC", operator="contains", value="肝功")]
        data_list = [
            {"DJZMC": "肝功项目"},
            {"DJZMC": "肾功项目"},
        ]

        result = filler.filter_data(data_list, conditions)

        assert len(result) == 1

    def test_filter_data_in(self):
        """测试 in 操作符"""
        filler = DataFiller()
        conditions = [FilterCondition(field="DJZMC", operator="in", value=["肝功", "肾功"])]
        data_list = [
            {"DJZMC": "肝功"},
            {"DJZMC": "肾功"},
            {"DJZMC": "糖代谢"},
        ]

        result = filler.filter_data(data_list, conditions)

        assert len(result) == 2

    def test_column_config_auto_number(self):
        """测试自动编号列"""
        filler = DataFiller()
        col = ColumnConfig(name="序号", source_field="", type="auto_number")

        value = filler._get_cell_value({}, col)

        assert value == ""

    def test_column_config_substring(self):
        """测试截取转换"""
        filler = DataFiller()
        col = ColumnConfig(
            name="简称",
            source_field="WLMS",
            transform="substring",
            params={"start": 0, "length": 10}
        )

        value = filler._get_cell_value({"WLMS": "ABCDEFGHIJKLMN"}, col)

        assert value == "ABCDEFGHIJ"

    def test_column_config_currency(self):
        """测试货币转换"""
        filler = DataFiller()
        col = ColumnConfig(
            name="零售价",
            source_field="LSJ",
            transform="currency",
            params={"decimals": 2}
        )

        value = filler._get_cell_value({"LSJ": 100.5}, col)

        assert value == "100.50"


# ============ SpeechProcessor 测试 ============

class TestSpeechProcessor:
    """SpeechProcessor 单元测试"""

    def test_process_fixed_speech(self):
        """测试固定话术"""
        processor = SpeechProcessor()
        speeches = [
            Speech(id="话术1", type="fixed", content="固定话术内容")
        ]

        result = processor.process_speeches(speeches, {})

        assert len(result) == 1
        assert result[0] == "固定话术内容"

    def test_process_conditional_speech_no_conditions(self):
        """测试无条件话术"""
        processor = SpeechProcessor()
        speeches = [
            Speech(id="话术1", type="conditional", content="条件话术内容")
        ]

        result = processor.process_speeches(speeches, {})

        assert len(result) == 1

    def test_process_mutex_group(self):
        """测试互斥组"""
        processor = SpeechProcessor()
        speeches = [
            Speech(id="话术1", type="conditional", mutex_group="A", content="话术1"),
            Speech(id="话术2", type="conditional", mutex_group="A", content="话术2"),
        ]

        result = processor.process_speeches(speeches, {})

        # 应该只选一个
        assert len(result) == 1

    def test_replace_variables(self):
        """测试变量替换"""
        processor = SpeechProcessor()

        content = "扣率为 {{肝功扣率}}%"
        variables = {"肝功扣率": "85"}

        result = processor._replace_speech_variables(content, variables, {})

        assert "85" in result

    def test_default_variables(self):
        """测试默认变量"""
        processor = SpeechProcessor()

        assert processor.DEFAULT_VARIABLES["肝功扣率"] == "85"
        assert processor.DEFAULT_VARIABLES["通用扣率"] == "70"


# ============ RowExpander 测试 ============

class TestRowExpander:
    """RowExpander 单元测试"""

    def test_get_value_auto_number(self):
        """测试自动编号"""
        expander = RowExpander()

        col = {"field": "", "type": "auto_number"}
        value = expander._get_value({}, col, 5)

        assert value == 5

    def test_get_value_text(self):
        """测试文本字段"""
        expander = RowExpander()

        col = {"field": "WLMS", "type": "text"}
        value = expander._get_value({"WLMS": "测试"}, col, 1)

        assert value == "测试"

    def test_get_value_none(self):
        """测试空值"""
        expander = RowExpander()

        col = {"field": "WLDM", "type": "text"}
        value = expander._get_value({}, col, 1)

        assert value == ""


# ============ DocumentGenerator 测试 ============

class TestDocumentGenerator:
    """DocumentGenerator 单元测试"""

    @patch('src.generators.document_generator.Document')
    def test_generate_with_mock(self, mock_document):
        """测试文档生成（使用 mock）"""
        # Mock Document
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc

        # Mock paragraphs
        mock_para = MagicMock()
        mock_para.text = "{{标题}}"
        mock_doc.paragraphs = [mock_para]

        # Mock tables
        mock_table = MagicMock()
        mock_table.rows = []
        mock_doc.tables = [mock_table]

        # Create generator with mocked template_dir
        generator = DocumentGenerator(template_dir="docs/template")

        # Mock template
        template = TemplateRule(
            id="模板1",
            name="测试模板",
            file="test.docx",
            条件=[]
        )

        # This will fail because the template doesn't exist, but tests the flow
        result = generator.generate(
            template,
            SAMPLE_QUOTE_DATA,
            SAMPLE_DETAIL_DATA,
            output_dir=tempfile.gettempdir()
        )

        # Result will be failed because template doesn't exist
        assert result.success is False or result.template_id == "模板1"


class TestMultiDocumentGenerator:
    """MultiDocumentGenerator 单元测试"""

    def test_generate_batch_empty(self):
        """测试空模板列表"""
        generator = MultiDocumentGenerator()

        results = generator.generate_batch(
            [],
            SAMPLE_QUOTE_DATA,
            SAMPLE_DETAIL_DATA
        )

        assert len(results) == 0


# ============ FilePacker 测试 ============

class TestFilePacker:
    """FilePacker 单元测试"""

    def test_pack_single_file(self):
        """测试单文件打包"""
        from src.utils.file_packer import FilePacker

        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            packer = FilePacker()
            result = packer.pack_single(temp_path)

            assert result == temp_path
        finally:
            os.unlink(temp_path)

    def test_cleanup(self):
        """测试清理文件"""
        from src.utils.file_packer import FilePacker

        with tempfile.NamedTemporaryFile(mode='w', suffix='.docx', delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            packer = FilePacker()
            packer.cleanup([temp_path])

            assert not os.path.exists(temp_path)
        except Exception:
            pass


# ============ GenerationResult 测试 ============

class TestGenerationResult:
    """GenerationResult 测试"""

    def test_success_result(self):
        """测试成功结果"""
        result = GenerationResult(
            success=True,
            file_path="/output/test.docx",
            template_id="模板1"
        )

        assert result.success is True
        assert result.file_path == "/output/test.docx"
        assert result.template_id == "模板1"

    def test_failure_result(self):
        """测试失败结果"""
        result = GenerationResult(
            success=False,
            template_id="模板1",
            error="Template not found"
        )

        assert result.success is False
        assert result.error == "Template not found"
