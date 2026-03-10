"""模板匹配器单元测试."""

import pytest
import tempfile
import os
from pathlib import Path

from src.models.template_rule import TemplateRule, RuleCondition
from src.models.match_result import MatchResult
from src.matchers.template_matcher import TemplateMatcher
from src.matchers.multi_matcher import MultiMatcher
from src.services.rule_loader import RuleLoader, RuleLoadError


# ============ 测试数据 ============

SAMPLE_QUOTE_DATA = {
    "产品细分编号": "11",
    "产品细分": "酶免试剂",
    "定价组编号": "12",
    "定价组名称": "通用生化-非集采项目",
    "是否集采": "1",
    "供货价类型": "集采中标价"
}

SAMPLE_DETAIL_DATA = [
    {"产品细分编号": "11", "定价组编号": "12", "是否集采": "1"},
    {"产品细分编号": "21", "定价组编号": "44", "是否集采": "0"},
]


# ============ RuleCondition 测试 ============

class TestRuleCondition:
    """RuleCondition 单元测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        condition = RuleCondition(产品细分编号="11", 是否集采="1")
        assert condition.match({"产品细分编号": "11", "是否集采": "1"}) is True

    def test_no_match(self):
        """测试不匹配"""
        condition = RuleCondition(产品细分编号="11")
        assert condition.match({"产品细分编号": "21"}) is False

    def test_partial_match(self):
        """测试部分条件不匹配"""
        condition = RuleCondition(产品细分编号="11", 是否集采="1")
        assert condition.match({"产品细分编号": "11", "是否集采": "0"}) is False

    def test_condition_with_none_value(self):
        """测试数据中字段为 None"""
        condition = RuleCondition(产品细分编号="11")
        assert condition.match({"产品细分编号": None}) is False

    def test_condition_missing_field(self):
        """测试数据中缺少字段"""
        condition = RuleCondition(产品细分编号="11", 是否集采="1")
        assert condition.match({"产品细分编号": "11"}) is False

    def test_condition_type_mismatch(self):
        """测试数据类型不匹配（数字 vs 字符串）"""
        condition = RuleCondition(是否集采="1")
        assert condition.match({"是否集采": 1}) is True  # str(1) == "1"

    def test_condition_with_extra_fields(self):
        """测试数据中有多余字段"""
        condition = RuleCondition(产品细分编号="11")
        data = {"产品细分编号": "11", "其他字段": "值"}
        assert condition.match(data) is True

    def test_condition_whitespace_handling(self):
        """测试空格处理"""
        condition = RuleCondition(产品细分编号="11")
        assert condition.match({"产品细分编号": " 11 "}) is True


# ============ TemplateRule 测试 ============

class TestTemplateRule:
    """TemplateRule 单元测试"""

    def test_match_all_conditions(self):
        """测试所有条件都满足"""
        rule = TemplateRule(
            id="模板1",
            name="测试模板",
            file="test.docx",
            条件=[
                RuleCondition(产品细分编号="11"),
                RuleCondition(是否集采="1")
            ]
        )
        assert rule.match({"产品细分编号": "11", "是否集采": "1"}) is True

    def test_no_condition_matches_all(self):
        """测试无条件匹配所有"""
        rule = TemplateRule(
            id="模板1",
            name="测试模板",
            file="test.docx",
            条件=[]
        )
        assert rule.match({"产品细分编号": "11"}) is True

    def test_single_empty_condition(self):
        """测试单个空条件"""
        rule = TemplateRule(
            id="模板1",
            name="测试模板",
            file="test.docx",
            条件=[RuleCondition()]
        )
        assert rule.match({"产品细分编号": "11"}) is True


# ============ TemplateMatcher 测试 ============

class TestTemplateMatcher:
    """TemplateMatcher 单元测试"""

    def test_single_match(self):
        """测试单模板匹配"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = TemplateMatcher(rules)
        result = matcher.match({"产品细分编号": "11"})

        assert result.success is True
        assert result.matched_count == 1
        assert result.templates[0].id == "模板1"

    def test_no_match(self):
        """测试无匹配"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = TemplateMatcher(rules)
        result = matcher.match({"产品细分编号": "21"})

        assert result.success is False
        assert result.matched_count == 0
        assert result.reason == "No matching template found"

    def test_multiple_match(self):
        """测试多模板匹配"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")]),
            TemplateRule(id="模板2", name="模板2", file="2.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = TemplateMatcher(rules)
        result = matcher.match({"产品细分编号": "11"})

        assert result.success is True
        assert result.matched_count == 2

    def test_empty_rules(self):
        """测试空规则列表"""
        matcher = TemplateMatcher([])
        result = matcher.match({"产品细分编号": "11"})

        assert result.success is False

    def test_empty_data(self):
        """测试空数据"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = TemplateMatcher(rules)
        result = matcher.match({})

        assert result.success is False


# ============ MultiMatcher 测试 ============

class TestMultiMatcher:
    """MultiMatcher 单元测试"""

    def test_match_quote_single_result(self):
        """测试主表单模板匹配-单结果"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = MultiMatcher(rules)
        result = matcher.match_quote({"产品细分编号": "11"})

        assert result.success is True
        assert result.matched_count == 1

    def test_match_quote_multiple_results(self):
        """测试主表多模板匹配"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")]),
            TemplateRule(id="模板2", name="模板2", file="2.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = MultiMatcher(rules)
        result = matcher.match_quote({"产品细分编号": "11"})

        assert result.success is True
        assert result.matched_count == 2

    def test_match_details_multiple(self):
        """测试明细多行数据匹配"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = MultiMatcher(rules)
        results = matcher.match_details(SAMPLE_DETAIL_DATA)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    def test_template_property_compatibility(self):
        """测试向后兼容属性"""
        rules = [
            TemplateRule(id="模板1", name="模板1", file="1.docx",
                       条件=[RuleCondition(产品细分编号="11")])
        ]
        matcher = MultiMatcher(rules)
        result = matcher.match_quote({"产品细分编号": "11"})

        assert result.template is not None
        assert result.template.id == "模板1"


# ============ RuleLoader 测试 ============

class TestRuleLoader:
    """RuleLoader 服务测试"""

    @pytest.fixture
    def temp_rule_file(self):
        """创建临时规则文件"""
        content = """
模板规则:
- id: 测试模板1
  name: 测试1
  file: test1.docx
  条件:
    - 产品细分编号: "11"
- id: 测试模板2
  name: 测试2
  file: test2.docx
  条件:
    - 产品细分编号: "21"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # 清理
        os.unlink(temp_path)

    def test_load_success(self, temp_rule_file):
        """测试正常加载"""
        loader = RuleLoader(temp_rule_file)
        rules = loader.load()

        assert len(rules) == 2
        assert rules[0].id == "测试模板1"

    def test_load_file_not_found(self):
        """测试文件不存在"""
        loader = RuleLoader("nonexistent.yaml")

        with pytest.raises(RuleLoadError) as exc_info:
            loader.load()

        assert "not found" in str(exc_info.value)

    def test_load_invalid_yaml(self):
        """测试无效 YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name

        try:
            loader = RuleLoader(temp_path)
            with pytest.raises(RuleLoadError) as exc_info:
                loader.load()
            assert "Invalid YAML" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_get_rules_returns_copy(self, temp_rule_file):
        """测试 get_rules 返回副本"""
        loader = RuleLoader(temp_rule_file)
        loader.load()

        rules1 = loader.get_rules()
        rules2 = loader.get_rules()

        assert rules1 is not rules2  # 不同的对象
        assert rules1 == rules2  # 相同的内容
