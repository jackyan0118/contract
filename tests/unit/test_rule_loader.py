"""规则加载服务单元测试."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.services.rule_loader import RuleLoader, RuleLoadError
from src.models.template_rule import TemplateRule, RuleCondition


@pytest.fixture
def temp_rule_file():
    """创建临时规则文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        rule_data = {
            "模板规则": [
                {
                    "id": "模板1",
                    "name": "通用生化试剂价格",
                    "file": "templates/模板1.docx",
                    "条件": [
                        {
                            "字段": "产品细分",
                            "操作符": "等于",
                            "值": "通用生化试剂"
                        }
                    ],
                    "排序规则": "按金额"
                },
                {
                    "id": "模板2",
                    "name": "酶免胶体金价格",
                    "file": "templates/模板2.docx",
                    "条件": [
                        {
                            "字段": "产品细分",
                            "操作符": "等于",
                            "值": "酶免胶体金"
                        }
                    ]
                }
            ]
        }
        yaml.dump(rule_data, f, allow_unicode=True)
        temp_path = f.name

    yield temp_path
    # 清理
    Path(temp_path).unlink(missing_ok=True)


class TestRuleLoader:
    """RuleLoader 测试"""

    def test_load_from_file(self, temp_rule_file):
        """测试从文件加载规则"""
        loader = RuleLoader(rule_file=temp_rule_file)
        rules = loader.load()

        assert len(rules) == 2
        assert rules[0].id == "模板1"
        assert rules[0].name == "通用生化试剂价格"
        assert rules[0].file == "templates/模板1.docx"

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        loader = RuleLoader(rule_file="/nonexistent/path/rules.yaml")

        with pytest.raises(RuleLoadError, match="not found"):
            loader.load()

    def test_load_invalid_yaml(self):
        """测试加载无效YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [}")
            temp_path = f.name

        try:
            loader = RuleLoader(rule_file=temp_path)
            with pytest.raises(RuleLoadError, match="Invalid YAML"):
                loader.load()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_get_rules(self, temp_rule_file):
        """测试获取规则"""
        loader = RuleLoader(rule_file=temp_rule_file)
        loader.load()

        rules = loader.get_rules()
        assert len(rules) == 2

    def test_get_rules_empty(self):
        """测试获取空规则"""
        loader = RuleLoader(rule_file="/nonexistent.yaml")
        # 不加载，_rules 为空列表
        rules = loader.get_rules()
        assert len(rules) == 0

    def test_reload_success(self, temp_rule_file):
        """测试重新加载成功"""
        loader = RuleLoader(rule_file=temp_rule_file)
        loader.load()

        # 修改文件
        with open(temp_rule_file, 'w', encoding='utf-8') as f:
            rule_data = {
                "模板规则": [
                    {
                        "id": "模板1",
                        "name": "更新后模板",
                        "file": "test.docx",
                        "条件": []
                    }
                ]
            }
            yaml.dump(rule_data, f, allow_unicode=True)

        loader.reload()
        rules = loader.get_rules()

        assert len(rules) == 1
        assert rules[0].name == "更新后模板"

    def test_reload_rollback_on_error(self, temp_rule_file):
        """测试重新加载失败回滚"""
        loader = RuleLoader(rule_file=temp_rule_file)
        loader.load()
        original_rules = loader.get_rules()

        # 备份成功后写入无效文件
        with open(temp_rule_file, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(RuleLoadError):
            loader.reload()

        # 应该回滚到旧规则
        rules = loader.get_rules()
        assert len(rules) == len(original_rules)


class TestRuleLoadError:
    """RuleLoadError 异常测试"""

    def test_exception_message(self):
        """测试异常消息"""
        error = RuleLoadError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """测试异常继承"""
        error = RuleLoadError("Test")
        assert isinstance(error, Exception)


class TestRuleLoaderExtended:
    """RuleLoader 扩展测试"""

    def test_get_cpxf_mapping(self, temp_rule_file):
        """测试获取产品细分映射"""
        loader = RuleLoader(rule_file=temp_rule_file)
        loader.load()

        mapping = loader.get_cpxf_mapping()

        # 验证返回的是字典
        assert isinstance(mapping, dict)

    def test_get_rules_empty_file(self):
        """测试加载空规则文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            rule_data = {"模板规则": []}
            yaml.dump(rule_data, f, allow_unicode=True)
            temp_path = f.name

        try:
            loader = RuleLoader(rule_file=temp_path)
            rules = loader.load()

            assert len(rules) == 0
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_with_empty_conditions(self):
        """测试加载空条件的规则"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            rule_data = {
                "模板规则": [
                    {
                        "id": "模板1",
                        "name": "测试",
                        "file": "test.docx",
                        "条件": []
                    }
                ]
            }
            yaml.dump(rule_data, f, allow_unicode=True)
            temp_path = f.name

        try:
            loader = RuleLoader(rule_file=temp_path)
            rules = loader.load()

            assert len(rules) == 1
            assert rules[0].条件 == []
        finally:
            Path(temp_path).unlink(missing_ok=True)
