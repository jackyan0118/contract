# Phase 4: 模板匹配引擎

## 概述

实现智能模板匹配逻辑，支持 35+ 模板的规则匹配。

**时间估算**: 4-5 天

**复杂度**: 高

---

## 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 | 状态 |
|------|------|----------|--------|------|------|
| 4.1 | 规则文件解析器 | `config/template_rules.yaml` | YAML 规则配置文件 | Phase 3 | ✅ 已完成 |
| 4.2 | 模板规则模型 | `src/models/template_rule.py` | 规则数据模型 | 4.1 | ✅ 已完成 |
| 4.3 | 规则加载服务 | `src/services/rule_loader.py` | 规则加载服务 | 4.2 | ✅ 已完成 |
| 4.4 | 模板匹配器 | `src/matchers/template_matcher.py` | 匹配引擎核心 | 4.3 | ✅ 已完成 |
| 4.5 | 多模板匹配处理 | `src/matchers/multi_matcher.py` | 多模板处理 | 4.4 | ✅ 已完成 |
| 4.6 | 匹配结果模型 | `src/models/match_result.py` | 匹配结果模型 | 4.4 | ✅ 已完成 |
| 4.7 | 匹配引擎单元测试 | `tests/test_matcher.py` | 测试用例 | 4.4, 4.5, 4.6 | ✅ 已完成 |

---

## 设计方案

### 4.1 规则文件解析器

**状态**: ✅ 已完成

规则文件 `config/template_rules.yaml` 包含：
- 产品细分映射
- 定价组映射
- 品牌映射
- 35+ 模板规则

---

### 4.2 模板规则模型

```python
# src/models/template_rule.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class RuleCondition(BaseModel):
    """匹配条件 - 所有字段为精确匹配（AND关系）"""
    产品细分编号: Optional[str] = None
    产品细分: Optional[str] = None
    定价组编号: Optional[str] = None
    定价组名称: Optional[str] = None
    是否集采: Optional[str] = None  # "0" 或 "1"
    供货价类型: Optional[str] = None

    def match(self, data: Dict[str, Any]) -> bool:
        """检查数据是否满足此条件

        Args:
            data: 待匹配的数据字典

        Returns:
            bool: 所有条件都满足返回 True，否则返回 False
        """
        for field, expected in self.model_dump(exclude_none=True).items():
            actual = data.get(field)
            # 处理 None 值和不匹配的情况
            if actual is None:
                return False
            # 统一转为字符串比较，过滤空格
            if str(actual).strip() != str(expected).strip():
                return False
        return True


class TemplateRule(BaseModel):
    """模板规则"""
    id: str              # 模板ID，如 "模板1"
    name: str            # 模板名称
    file: str            # 模板文件路径
    条件: List[RuleCondition]  # 条件列表（AND关系）
    排序规则: Optional[str] = None   # 排序规则

    def match(self, data: Dict[str, Any]) -> bool:
        """检查数据是否匹配此模板（所有条件都满足）"""
        if not self.条件:
            return True  # 无条件则匹配所有
        return all(condition.match(data) for condition in self.条件)
```

**约束**：
- 不支持 OR 条件
- 所有条件为 AND 关系

---

### 4.3 规则加载服务

```python
# src/services/rule_loader.py
import yaml
import logging
import threading
from pathlib import Path
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.models.template_rule import TemplateRule
from src.exceptions import ConfigException

logger = logging.getLogger(__name__)


class RuleLoadError(Exception):
    """规则加载异常"""
    pass


class RuleLoader:
    """规则加载服务 - 线程安全，支持热更新"""

    def __init__(self, rule_file: str = "config/template_rules.yaml"):
        self.rule_file = Path(rule_file)
        self._rules: List[TemplateRule] = []
        self._observer: Optional[Observer] = None
        self._lock = threading.RLock()

    def load(self) -> List[TemplateRule]:
        """加载规则文件

        Raises:
            RuleLoadError: 文件不存在或格式错误
        """
        logger.info(f"Loading rules from {self.rule_file}")

        if not self.rule_file.exists():
            raise RuleLoadError(f"Rule file not found: {self.rule_file}")

        try:
            with open(self.rule_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuleLoadError(f"Invalid YAML format: {e}")

        rules_data = data.get('模板规则', [])
        self._rules = [TemplateRule(**rule) for rule in rules_data]
        logger.info(f"Loaded {len(self._rules)} template rules")
        return self._rules

    def reload(self):
        """重新加载规则（带锁保护）"""
        with self._lock:
            logger.info("Reloading template rules...")
            try:
                self.load()
                logger.info("Template rules reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload rules: {e}")
                raise

    def get_rules(self) -> List[TemplateRule]:
        """获取已加载的规则"""
        with self._lock:
            return self._rules.copy()

    def start_watching(self):
        """启动文件监听（热更新）"""
        if self._observer is not None:
            return

        event_handler = RuleFileHandler(self)
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.rule_file.parent), recursive=False)
        self._observer.start()
        logger.info(f"Started watching {self.rule_file} for changes")

    def stop_watching(self):
        """停止文件监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching rule file")


class RuleFileHandler(FileSystemEventHandler):
    """规则文件变化处理器 - 带防抖机制"""

    DEBOUNCE_SECONDS = 1.0  # 防抖延迟时间

    def __init__(self, loader: RuleLoader):
        self.loader = loader
        self._debounce_timer: Optional[threading.Timer] = None

    def on_modified(self, event: FileSystemEvent):
        if event.src_path != str(self.loader.rule_file):
            return

        # 取消之前的定时器
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # 设置新的定时器（防抖）
        self._debounce_timer = threading.Timer(
            self.DEBOUNCE_SECONDS,
            self._do_reload
        )
        self._debounce_timer.start()

    def _do_reload(self):
        """执行重载"""
        logger.warning(f"Rule file changed, reloading...")
        try:
            self.loader.reload()
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")
```

**特性**：
- 启动时预加载规则
- 支持热更新（文件变化自动重载）
- 使用 watchdog 库监听文件变化
- **带防抖机制**（1秒内多次修改只触发一次重载）
- **线程安全**（使用 RLock 保护）
- **异常处理**（文件不存在、YAML 格式错误）
- **失败回滚**（重载失败时保留旧规则）

**新增依赖**：
- `src/exceptions/ConfigException` - 配置异常类

---

### 4.4 模板匹配器

```python
# src/matchers/template_matcher.py
import logging
from typing import List, Optional, Dict, Any

from src.models.template_rule import TemplateRule, RuleCondition
from src.models.match_result import MatchResult

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """模板匹配器 - 单模板匹配"""

    def __init__(self, rules: List[TemplateRule]):
        self.rules = rules

    def match(self, data: Dict[str, Any]) -> MatchResult:
        """
        匹配模板

        Args:
            data: 报价单数据

        Returns:
            MatchResult: 匹配结果
        """
        matched_templates = []

        for rule in self.rules:
            if rule.match(data):
                matched_templates.append(rule)
                logger.debug(f"Data matched template: {rule.id} - {rule.name}")

        if not matched_templates:
            return MatchResult(
                success=False,
                templates=[],
                matched_count=0,
                reason="No matching template found"
            )

        return MatchResult(
            success=True,
            templates=matched_templates,
            matched_count=len(matched_templates),
            reason=None
        )
```

**逻辑**：
1. 遍历所有模板规则
2. 检查数据是否满足每个规则的所有条件（AND）
3. 返回所有匹配的模板（按配置顺序）

---

### 4.5 多模板匹配处理

```python
# src/matchers/multi_matcher.py
import logging
from typing import List, Dict, Any

from src.models.template_rule import TemplateRule
from src.models.match_result import MatchResult
from src.matchers.template_matcher import TemplateMatcher

logger = logging.getLogger(__name__)


class MultiMatcher:
    """多模板匹配处理器"""

    def __init__(self, rules: List[TemplateRule]):
        self.matcher = TemplateMatcher(rules)

    def match_quote(self, quote_data: Dict[str, Any]) -> MatchResult:
        """
        匹配报价单主表数据

        Args:
            quote_data: 报价单主表数据

        Returns:
            MatchResult: 包含所有匹配模板的结果
        """
        result = self.matcher.match(quote_data)

        if result.matched_count > 1:
            logger.warning(
                f"Multiple templates matched for quote. "
                f"Matched templates: {[t.id for t in result.templates]}"
            )

        return result

    def match_details(self, detail_data_list: List[Dict[str, Any]]) -> List[MatchResult]:
        """
        匹配报价单明细数据

        Args:
            detail_data_list: 报价单明细数据列表

        Returns:
            List[MatchResult]: 每个明细的匹配结果
        """
        results = []
        for detail in detail_data_list:
            result = self.matcher.match(detail)
            results.append(result)

            if result.matched_count > 1:
                logger.warning(
                    f"Multiple templates matched for detail. "
                    f"Matched templates: {[t.id for t in result.templates]}"
                )

        return results
```

**特性**：
- 匹配报价单主表数据
- 逐条匹配明细数据
- 记录 WARNING 日志（多模板匹配时）

---

### 4.6 匹配结果模型

```python
# src/models/match_result.py
from typing import Optional, List
from pydantic import BaseModel

from src.models.template_rule import TemplateRule


class MatchResult(BaseModel):
    """模板匹配结果"""
    success: bool                    # 是否匹配成功
    templates: List[TemplateRule]    # 匹配的模板列表（按优先级排序）
    matched_count: int               # 匹配数量
    reason: Optional[str] = None    # 未匹配原因

    # 兼容单个模板场景
    @property
    def template(self) -> Optional[TemplateRule]:
        """获取第一个匹配的模板（向后兼容）"""
        return self.templates[0] if self.templates else None
```

---

### 4.7 单元测试

```python
# tests/test_matcher.py
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
```

---

## 日志规范

| 级别 | 场景 |
|------|------|
| INFO | 规则加载/重载成功、匹配开始、匹配成功 |
| WARNING | 多模板匹配（记录所有匹配的模板ID） |
| ERROR | 规则加载失败、匹配异常 |

---

## 文件结构

```
src/
├── models/
│   ├── template_rule.py      # 模板规则模型
│   └── match_result.py       # 匹配结果模型
├── services/
│   └── rule_loader.py        # 规则加载服务
├── matchers/
│   ├── template_matcher.py   # 模板匹配器
│   └── multi_matcher.py      # 多模板处理
├── exceptions/
│   └── __init__.py           # 异常类定义
└── parsers/
    └── rule_parser.py        # 规则解析（可选，如果需要从Excel解析）
```

---

## 依赖关系

```
Phase 3 数据查询模块
       │
       ▼
  4.2 模板规则模型
       │
       ▼
  4.3 规则加载服务
       │
       ▼
  4.4 模板匹配器
       │
       ▼
  4.5 多模板匹配处理
       │
       ▼
  4.6 匹配结果模型
       │
       ▼
  4.7 单元测试
```

---

## 风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 规则文件格式变更 | 高 | 添加 schema 验证，版本控制 |
| 热更新失败无回滚 | 中 | 实现重载前备份旧规则，失败时回滚 |
| 规则复杂度导致性能问题 | 中 | 使用规则索引和缓存机制 |
| 并发安全问题 | 中 | 使用线程锁保护共享资源 |
| 边界条件处理不当 | 低 | 完善的单元测试覆盖 |

---

## 待确认事项

- [x] 匹配策略：精确匹配
- [x] OR 条件：不支持
- [x] 规则加载：预加载 + 热更新 + 防抖
- [x] 多模板：返回所有匹配模板
- [x] 文档生成：每个匹配模板生成一个文档
- [x] 错误处理：RuleLoader 异常处理完善
- [x] 边界条件：None 值、空数据、多余字段处理

---

## 评审跟踪

详见 `review/01-expert-panel-review.md`

**评审修复项**：
- [x] RuleCondition.match() None 值处理
- [x] RuleLoader 异常处理
- [x] 热更新防抖机制
- [x] 测试用例补充（边界条件、RuleLoader）

---

*文档版本：1.1*
*创建日期：2026-03-10*
*更新日期：2026-03-10*
