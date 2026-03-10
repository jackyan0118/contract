# Phase-5 设计文档专家评审报告

**评审日期**: 2026-03-10

**评审文件**: docs/plan/phase-5/README.md

**评审专家**:
- 数据库专家 (database-reviewer)
- Python 代码专家 (python-reviewer)

**修复日期**: 2026-03-10

---

## 一、评审结论

| 评审项 | 状态 | 说明 |
|--------|------|------|
| 数据逻辑与数据库匹配 | ✅ 已修复 | SFJC 字段值已改为数值 1/0 |
| 配置结构一致性 | ⚠️ 待统一 | detail_filter 结构不一致 |
| 代码实现复杂度 | ⚠️ 需明确 | 话术互斥组逻辑需明确 |

---

## 二、已修复的问题

### 修复 1: SFJC 字段类型不匹配 [严重] ✅

| 项目 | 内容 |
|------|------|
| **状态** | ✅ 已修复 |
| **修复内容** | 将所有 `value: "是"` 改为 `value: 1`，`value: "!="是""` 改为 `value: 0` |
| **修复文件** | 16个模板文件 |

**修复明细**:
- 模板3.1, 3.2, 4.1, 4.2: `value: "是"` → `value: 1`
- 模板6.1, 6.2, 7.1, 7.2: `value: "是"` → `value: 1`
- 模板9.1, 9.2, 10.1, 10.2: `value: "是"` → `value: 1`
- 模板12.1, 12.2, 13.1, 13.2: `value: "是"` → `value: 1`
- 模板2.yaml: 话术条件中的 SFJC 全部修复

---

### 修复 2: 模板1 YAML 语法错误 [低] ✅

| 项目 | 内容 |
|------|------|
| **状态** | ✅ 已修复 |
| **修复内容** | 删除重复的 `table:` 键 |

---

## 三、待处理问题

### 问题 1: detail_filter 配置结构不一致 [中等]

| 模板 | 配置结构 |
|------|----------|
| 模板1, 模板3.1 | `detail_filter.conditions` (数组) |
| 模板2 | `detail_filter.filter_rules` (带id的规则组) |

**建议**: 统一使用 `detail_filter.conditions` 数组结构

---

### 问题 2: match_conditions 与 detail_filter 字段名不一致 [中等]

**示例** (模板3.1):
```yaml
# match_conditions 使用中文别名
match_conditions:
  产品细分: "通用生化试剂"
  定价组: [...]
  是否集采: "是"
  供货价类型: "集采中标价"

# detail_filter 使用数据库字段名
detail_filter:
  conditions:
    - field: "CPXF"       # 产品细分
    - field: "DJZMC"       # 定价组
    - field: "SFJC"        # 是否集采
    - field: "BNGHJLX"     # 供货价类型
```

**建议**: 在代码中添加字段映射层

---

### 问题 3: 话术互斥组逻辑需明确 [中等]

| 问题 | 建议 |
|------|------|
| 多条件同时满足时如何选择 | 按配置顺序选择第一个匹配的 |
| 无匹配话术时如何处理 | 输出为空 |
| fixed 话术与互斥组关系 | fixed 不参与互斥组判定，始终添加 |

---

### 问题 4: 操作符设计需补充 [中等]

| 问题 | 建议 |
|------|------|
| `contains` 大小写敏感 | 增加 `case_sensitive` 配置 |
| 空值处理 | 明确 `field is None` 时的行为 |
| 数值类型转换 | 数值比较时统一转换为 float |

---

## 四、字段存在性检查

| 字段名 | 数据库存在 | 数据类型 | 配置中使用方式 | 状态 |
|--------|------------|----------|----------------|------|
| CPXF | 是 | VARCHAR2 | 字符串 | OK |
| LYXH | 是 | NUMBER | 数值 (1, 2) | OK |
| DJZMC | 是 | VARCHAR2 | 字符串 | OK |
| SFJC | 是 | NUMBER | 数值 (1, 0) | ✅ 已修复 |
| WLDM | 是 | VARCHAR2 | 字符串 | OK |
| WLMS | 是 | VARCHAR2 | 字符串 | OK |
| GG | 是 | VARCHAR2 | 字符串 | OK |
| LSJ | 是 | NUMBER | 数值 | OK |
| GHJY | 是 | NUMBER | 数值 | OK |
| BNGHJLX | 是 | VARCHAR2 | 字符串 | OK |

---

## 五、风险评估

| 问题 | 严重程度 | 影响范围 | 风险等级 | 状态 |
|------|----------|----------|----------|------|
| SFJC 类型不匹配 | 严重 | 16个模板 | **高** | ✅ 已修复 |
| 配置结构不一致 | 中等 | 全部模板 | **中 |
| 字段映射缺失 | 中等 | ** | 待处理集采类16个模板 | **中** | 待处理 |
| 话术互斥组逻辑不明确 | 中等 | 有话术的模板 | **中** | 待处理 |
| YAML 语法错误 | 低 | 模板1 | **低** | ✅ 已修复 |

---

## 六、建议的 Pydantic 模型

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Any, List
from enum import Enum

class Operator(str, Enum):
    EQ = "="
    NE = "!="
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="

class Condition(BaseModel):
    field: str
    operator: Operator
    value: Any

class SpeechVariable(BaseModel):
    name: str
    default: str

class SpeechConfig(BaseModel):
    id: str
    name: Optional[str] = None
    type: Literal["conditional", "fixed"]
    mutex_group: Optional[str] = None
    conditions: Optional[List[Condition]] = None
    content: str
    variables: List[SpeechVariable] = []
```

---

*评审完成时间: 2026-03-10*
