# Phase 5: Word 文档生成模块 - 设计文档

## 概述

实现 Word 模板读取和数据填充功能。

**时间估算**: 4-5 天

**复杂度**: 高

---

## 模板元数据配置

基于 `config/template_metadata/templates/` 目录下的配置文件。

### 配置结构

每个模板独立一个 YAML 文件，包含以下配置：

```yaml
# 模板基础信息
id: "模板2"
name: "通用生化产品价格模版"
file: "templates/模板2：通用生化产品价格模版.docx"
category: "通用生化"

# Phase 4: 模板匹配条件（用于确定使用哪些模板）
match_conditions:
  产品细分: "通用生化试剂"

# Phase 5: 明细表数据筛选规则
detail_filter:
  filter_rules:
    - id: "规则1"
      name: "物料生成来源2"
      conditions:
        - field: "CPXF"
          operator: "="
          value: "通用生化试剂"
        - field: "LYXH"
          operator: "="
          value: 2

# 表格配置
table:
  placeholders:
    start: "{{#明细表}}"
    end: "{{/明细表}}"
  columns:
    - name: "序号"
      type: "auto_number"
    - name: "物料编码"
      source_field: "WLDM"
      source_table: "UF_HTJGKST_DT1"

# 段落占位符
paragraph_placeholders:
  标题:
    value: "通用生化产品供货价"

# 话术配置
speeches:
  - id: "话术1.1"
    type: "conditional"  # conditional | fixed
    mutex_group: "A"     # 互斥组，同组只选一个
    conditions:
      - field: "DJZMC"
        operator: "contains"
        value: "肝功"
      - field: "SFJC"
        operator: "="
        value: "是"
    content: "话术内容..."
    variables:
      - name: "肝功扣率"
        default: "85"
```

### 模板分类

| 分类 | 数量 | 表格列数 | 示例模板 |
|------|------|----------|----------|
| 集采类 | 16 | 3 | 模板3.1, 模板3.2, 模板4.1, 模板4.2... |
| 酶免胶体金 | 2 | 6 | 模板1, 模板17 |
| 通用生化 | 5 | 7 | 模板2, 模板5, 模板8, 模板11, 模板14 |
| 外购试剂 | 20 | 8 | 模板15-模板35 |

---

## 数据字段映射

### 明细表 (UF_HTJGKST_DT1) 关键字段

| 字段名 | 说明 | 数据类型 |
|--------|------|----------|
| WLDM | 物料代码 | VARCHAR2 |
| WLMS | 物料描述 | VARCHAR2 |
| GG | 规格 | VARCHAR2 |
| LSJ | 零售价 | NUMBER |
| GHJY | 供货价_元 | NUMBER |
| DJZMC | 定价组名称 | VARCHAR2 |
| CPXF | 产品细分 | VARCHAR2 |
| LYXH | 物料生成来源 | NUMBER |
| SFJC | 是否集采 | NUMBER | 选择框，1=是，0=否 |
| BNGHJLX | 供货价类型 | VARCHAR2 | 本年供货价类型 |

### 字段映射层设计

#### 字段分类

| 字段 | ID字段 | 名称字段 | 说明 |
|------|--------|----------|------|
| 定价组 | DJZ | DJZMC | DJZ存储UF_CPZWH表ID，DJZMC存储名称 |
| 产品细分 | CPXF | - | CPXF存储UF_CPXF表ID |
| 供货价类型 | BNGHJLX | BNGHJLXZ | BNGHJLX存储UF_YXZXHTGHJLXBN表ID |
| 是否集采 | SFJC | - | NUMBER类型，1=是，0=否 |

#### 双字段匹配规则

**推荐配置方式**：同时支持ID和名称匹配，代码智能选择

```yaml
# 推荐配置格式（支持两种方式）
detail_filter:
  conditions:
    # 方式1：使用名称（可读性好，但名称修改后可能失效）
    - field: "DJZMC"
      operator: "="
      value: "通用生化试剂"

    # 方式2：使用ID（更稳定，跨环境一致）
    - field: "DJZ"
      operator: "="
      value: 123
```

**代码匹配逻辑**：
```python
# 字段名映射配置
FIELD_MAPPING = {
    # match_conditions 字段名 -> (ID字段, 名称字段)
    "产品细分": ("CPXF", None),
    "定价组": ("DJZ", "DJZMC"),
    "定价组名称": ("DJZ", "DJZMC"),
    "是否集采": ("SFJC", None),
    "供货价类型": ("BNGHJLX", "BNGHHJLXZ"),
    "物料生成来源": ("LYXH", None),
}

def build_filter_conditions(conditions):
    """构建SQL查询条件"""
    for cond in conditions:
        field = cond["field"]
        value = cond["value"]
        operator = cond["operator"]

        # 优先使用ID字段匹配（更稳定）
        if field in FIELD_MAPPING:
            id_field, name_field = FIELD_MAPPING[field]
            if isinstance(value, int) and id_field:
                # 使用ID匹配
                sql = f"{id_field} {operator} {value}"
            elif name_field:
                # 使用名称匹配
                sql = f"{name_field} {operator} '{value}'"
        else:
            # 非映射字段，直接使用
            sql = f"{field} {operator} '{value}'"
```

**匹配优先级**：
1. **数值类型value** → 优先匹配ID字段（如 DJZ, BNGHJLX）
2. **字符串类型value** → 匹配名称字段（如 DJZMC）
3. 这样既保证稳定性，又保持可读性

### 各模板字段映射

#### 模板1（酶免胶体金）- 6列

| 目标列 | 源字段 | 说明 |
|--------|--------|------|
| 产品类别 | CPXF | 产品细分 |
| 序号 | auto_number | 自动编号 |
| 物料编码 | WLDM | 物料代码 |
| 品名 | WLMS | 物料描述 |
| 规格型号 | GG | 规格 |
| 供货价 | GHJY | 供货价_元 |

#### 模板2（通用生化）- 7列

| 目标列 | 源字段 | 转换 |
|--------|--------|------|
| 序号 | auto_number | 自动编号 |
| 物料编码 | WLDM | - |
| 简称 | WLMS | substring(0,10) |
| 品名 | WLMS | - |
| 规格型号 | GG | - |
| 零售价 | LSJ | currency(2位小数) |
| 供货价 | GHJY | currency(2位小数) |

#### 模板3.1（肾功心肌酶-集采中标价）- 3列

| 目标列 | 源字段 | 说明 |
|--------|--------|------|
| 序号 | auto_number | 自动编号 |
| 产品名称 | WLMS | 物料描述 |
| 供货价 | GHJY | 供货价_元 |

#### 模板15（质谱试剂）- 8列

| 目标列 | 源字段 | 说明 |
|--------|--------|------|
| 序号 | auto_number | 自动编号 |
| SAP代码 | WLDM | 物料代码 |
| 类别 | CPXF | 产品细分 |
| 缩写 | WLMS | substring(0,8) |
| 品名 | WLMS | 物料描述 |
| 包装规格 | GG | 规格 |
| 零售价 | LSJ | 零售价 |
| 供货价 | GHJY | 供货价_元 |

---

## 条件表达式语法

### 支持的操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| `=` | 等于 | `SFJC = "是"` |
| `!=` | 不等于 | `BNGHJLX != "集采中标价"` |
| `contains` | 包含 | `DJZMC contains "肝功"` |
| `in` | 在列表中 | `DJZMC in ["肾功和心肌酶", "江西糖代谢"]` |
| `not_in` | 不在列表中 | `CPXF not_in ["酶免试剂", "胶体金试剂"]` |
| `>` | 大于 | `LSJ > 100` |
| `<` | 小于 | `LSJ < 1000` |
| `>=` | 大于等于 | `LSJ >= 100` |
| `<=` | 小于等于 | `LSJ <= 1000` |

### 条件组合

- **AND 逻辑**：多个 conditions 之间为 AND 关系
- **OR 逻辑**：使用 `in` 操作符实现

---

## 建议占位符

### 段落占位符

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{{标题}}` | 文档标题 | "通用生化产品供货价" |
| `{{金额单位}}` | 金额单位 | "元" |

### 表格占位符

| 占位符 | 说明 |
|--------|------|
| `{{#明细表}}` | 明细表数据开始 |
| `{{/明细表}}` | 明细表数据结束 |
| `{{序号}}` | 序号（自动编号） |
| `{{物料编码}}` | WLDM 字段 |
| `{{品名}}` | WLMS 字段 |
| `{{规格型号}}` | GG 字段 |
| `{{零售价}}` | LSJ 字段 |
| `{{供货价}}` | GHJY 字段 |

### 话术占位符

| 占位符 | 说明 |
|--------|------|
| `{{#话术}}` | 话术区域开始 |
| `{{/话术}}` | 话术区域结束 |
| `{{肝功扣率}}` | 话术变量 |
| `{{通用扣率}}` | 话术变量 |
| `{{北极星扣率}}` | 话术变量 |
| `{{耗材扣率}}` | 话术变量 |

---

## 话术互斥组逻辑

### 话术类型

| 类型 | 说明 |
|------|------|
| `fixed` | 固定话术，不参与互斥组判定，始终添加 |
| `conditional` | 条件话术，根据条件匹配，参与互斥组判定 |

### 互斥组选择规则

1. **同组内选择**：互斥组内按配置顺序选择**第一个**满足条件的话术
2. **无匹配时**：该互斥组输出为空（不添加任何话术）
3. **多组并行**：不同互斥组之间独立运行，最终合并所有组的话术
4. **fixed 话术**：始终添加，不参与互斥组判定

### 配置示例

```yaml
speeches:
  # 互斥组A：肝功话术（只会匹配一条）
  - id: "话术1.1"
    type: "conditional"
    mutex_group: "A"
    conditions:
      - field: "DJZMC"
        operator: "contains"
        value: "肝功"
      - field: "BNGHJLX"
        operator: "!="
        value: "集采中标价"
    content: "话术内容1..."

  - id: "话术1.2"
    type: "conditional"
    mutex_group: "A"
    conditions:
      - field: "DJZMC"
        operator: "contains"
        value: "肝功"
      - field: "BNGHJLX"
        operator: "="
        value: "集采中标价"
    content: "话术内容2..."

  # 固定话术：始终添加
  - id: "话术3"
    type: "fixed"
    content: "若产品供货价格无法按上表方法表述的，则需附详细价格表。"
```

### 执行流程

1. 按配置顺序遍历每个话术
2. 如果是 `fixed` 类型，直接添加到输出
3. 如果是 `conditional` 类型：
   - 检查是否已有同 mutex_group 的话术被选中
   - 如果没有，检查条件是否满足
   - 如果条件满足，添加到输出并标记该 mutex_group
4. 返回所有话术

---

## 默认话术变量

| 变量名 | 默认值 |
|--------|--------|
| 肝功扣率 | 85 |
| 通用扣率 | 70 |
| 北极星扣率 | 25 |
| 耗材扣率 | 50 |

---

## 已确认设计决策

| 决策项 | 选择 |
|--------|------|
| 模板读取 | 元数据配置 + 占位符 |
| 表格行超出 | 扩展行 |
| 多文档输出 | 独立文件 |
| 话术顺序 | 互斥组 |
| 话术变量 | 固定值 |
| 话术位置 | 占位符 |
| 格式复制 | 完整复制 |
| 打包格式 | ZIP压缩 |
| 测试数据 | mock数据 |

---

## 模板填写规则

详见 `template_filling_rules.md`

---

## 配置示例

### 模板2完整配置

```yaml
id: "模板2"
name: "通用生化产品价格模版"
file: "templates/模板2：通用生化产品价格模版.docx"
category: "通用生化"

# Phase 4: 模板匹配条件
match_conditions:
  产品细分: "通用生化试剂"

# Phase 5: 明细表数据筛选规则
detail_filter:
  filter_rules:
    - id: "规则1"
      name: "物料生成来源2"
      conditions:
        - field: "CPXF"
          operator: "="
          value: "通用生化试剂"
        - field: "LYXH"
          operator: "="
          value: 2
    - id: "规则2"
      name: "物料生成来源1-特殊定价组"
      conditions:
        - field: "CPXF"
          operator: "="
          value: "通用生化试剂"
        - field: "LYXH"
          operator: "="
          value: 1
        - field: "DJZMC"
          operator: "in"
          value:
            - "通用特殊生化-非集采项目"
            - "通用特殊生化-肝功"
            - "通用特殊生化-肾功和心肌酶"
        - field: "SFJC"
          operator: "!="
          value: "是"

# 表格配置
table:
  placeholders:
    start: "{{#明细表}}"
    end: "{{/明细表}}"
  columns:
    - name: "序号"
      type: "auto_number"
    - name: "物料编码"
      source_field: "WLDM"
      source_table: "UF_HTJGKST_DT1"
    - name: "简称"
      source_field: "WLMS"
      transform: "substring"
      params:
        start: 0
        length: 10

# 段落占位符
paragraph_placeholders:
  标题:
    value: "通用生化产品供货价"
  金额单位:
    value: "元"

# 话术配置
speeches:
  - id: "话术1.1"
    type: "conditional"
    mutex_group: "A"
    conditions:
      - field: "DJZMC"
        operator: "contains"
        value: "肝功"
      - field: "SFJC"
        operator: "="
        value: "是"
      - field: "BNGHJLX"
        operator: "!="
        value: "集采中标价"
    content: |
      其余肝功集采项目的通用生化试剂供货价=肝功生化类检测试剂省际联盟集中带量采购中选结果中的试剂中标价*【 {{肝功扣率}} 】%
    variables:
      - name: "肝功扣率"
        default: "85"

  - id: "话术3"
    type: "fixed"
    content: |
      若产品供货价格无法按上表方法表述的，则需附详细价格表。
```

---

## 任务列表

| 序号 | 任务 | 产出物 | 状态 |
|------|------|--------|------|
| 5.1 | Word 模板读取器 | `src/readers/word_template_reader.py` | ✅ 已完成 |
| 5.2 | 表格结构分析 | 合并到5.1 | ✅ 已完成 |
| 5.3 | 数据填充引擎 | `src/fillers/data_filler.py` | ✅ 已完成 |
| 5.4 | 表格行扩展器 | `src/fillers/row_expander.py` | ✅ 已完成 |
| 5.5 | 格式保持器 | `src/fillers/format_preserver.py` | ✅ 已完成 |
| 5.6 | 多模板生成器 | `src/generators/document_generator.py` | ✅ 已完成 |
| 5.7 | 文件打包器 | `src/utils/file_packer.py` | ✅ 已完成 |
| 5.8 | Word 生成单元测试 | `tests/unit/test_document_generator.py` | ✅ 已完成 |

---

*更新时间：2026-03-10*
