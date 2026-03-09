---
name: data-dictionary-generator
description: Oracle数据字典生成器。根据用户提供的表名列表，连接数据库获取表结构、字段信息、数据类型、注释等，生成Markdown格式的数据字典文档。适用于泛微E9流程建模表（workflow_bill, workflow_billfield等）或其他Oracle实体表的数据字典提取。当用户需要获取数据库表结构、字段说明、数据类型映射时自动触发。
---

# Oracle数据字典生成器

## 概述

本skill帮助用户从Oracle数据库中提取表结构信息，并生成规范的数据字典文档。支持泛微E9的浏览按钮字段类型识别和实体表映射。

## 使用场景

- 获取泛微E9流程建模表的数据字典
- 提取业务表的字段说明
- 生成数据库设计文档
- 分析表结构关系
- 识别浏览按钮对应的实体对象

## 使用方法

### 1. 命令行参数（推荐）

脚本位置：`{skill_dir}/scripts/get_data_dictionary.py`

```bash
# 激活虚拟环境
source venv/bin/activate

# 查看帮助
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py -h

# 生成指定表的字典
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py -t UF_HTJGKST

# 生成多个表
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py -t UF_HTJGKST,UF_HTJGKST_DT1

# 指定Schema
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py -t UF_HTJGKST -s ECOLOGY

# 指定输出目录
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py -t UF_HTJGKST -o ./output

# 列出所有可访问的表
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py --list-tables

# 处理所有可访问的表（默认限制50个）
python .claude/skills/data-dictionary/scripts/get_data_dictionary.py
```

### 2. 参数说明

| 参数 | 说明 |
|------|------|
| `-t, --tables` | 表名列表，逗号分隔 |
| `-s, --schema` | Schema名称（默认: ECOLOGY） |
| `-o, --output` | 输出目录（默认: docs/E9Data） |
| `--list-tables` | 列出所有可访问的表 |
| `--limit` | 限制处理表数量（默认: 50） |

### 3. 输出内容

脚本会生成包含以下信息的Markdown文档：

| 列名 | 说明 |
|------|------|
| 序号 | 字段顺序 |
| 字段名 | 数据库字段名 |
| 数据类型 | Oracle数据类型 |
| 可空 | YES/NO |
| 字段类型 | 单行文本、浏览按钮、选择框等 |
| 实体对象 | 浏览按钮对应的实体表 |
| 说明 | 字段中文说明 |

### 4. 浏览按钮实体对象映射

对于泛微E9的浏览按钮字段，脚本会自动识别实体对象：

| 浏览框标识 | 实体表 | 说明 |
|-----------|--------|------|
| cpkcpxf | uf_cpxf | 产品细分 |
| pp | uf_pp | 品牌 |
| jytc | uf_jytc | 检验套餐 |
| cpkxmjc | uf_cpkxmjc | 项目简称 |
| crmkhkp_allenable_sh | uf_crmkhkp | CRM客户卡片 |
| cpz_all | uf_cpzwh | 产品组维护 |
| sapcplb | uf_sapcplbqd | SAP产品类别清单 |

## 技术实现

### 数据来源

1. **Oracle系统表**
   - `all_tables` - 表基本信息
   - `all_tab_columns` - 字段信息
   - `all_tab_comments` - 表注释
   - `all_col_comments` - 字段注释

2. **泛微E9系统表**
   - `workflow_bill` - 表单定义
   - `workflow_billfield` - 字段定义（字段类型、浏览按钮配置）
   - `HTMLLABELINFO` - 中文标签
   - `MODE_BROWSER` - 自定义浏览框配置

### 字段类型识别

从 `workflow_billfield` 表获取：

| fieldhtmltype | 说明 |
|---------------|------|
| 1 | 单行文本 |
| 2 | 多行文本 |
| 3 | 浏览按钮 |
| 4 | Check框 |
| 5 | 选择框 |
| 6 | 附件上传 |
| 7 | 特殊字段 |

### 浏览按钮实体解析

1. 从 `workflow_billfield.type` 获取浏览按钮类型
2. 如果是自定义浏览按钮（type=161/162），从 `fielddbtype` 获取浏览框标识（如 `browser.pp`）
3. 从 `MODE_BROWSER` 表查询浏览框标识对应的SQL语句
4. 从SQL语句中解析出实体表名

## 常用表查询参考

### 泛微E9流程建模相关

| 用途 | 表名 | 说明 |
|------|------|------|
| 表单定义 | workflow_bill | 存储表单基本信息 |
| 字段定义 | workflow_billfield | 存储表单字段信息 |
| 浏览框配置 | mode_browser | 自定义浏览框定义 |
| 流程节点 | workflow_nodebase | 流程节点配置 |
| 流程主表 | workflow_requestbase | 流程请求主表 |

### Oracle系统表

| 用途 | 表名 | 说明 |
|------|------|------|
| 表列表 | all_tables | 当前用户可访问的表 |
| 列信息 | all_tab_columns | 表的列信息 |
| 表注释 | all_tab_comments | 表的注释 |
| 列注释 | all_col_comments | 列的注释 |
| 索引 | all_indexes | 表的索引 |
| 约束 | all_constraints | 约束定义 |

## 输出示例

对于 `ecology.uf_htjgkst_dt1` 表：

```markdown
# UF_HTJGKST_DT1 数据字典

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 3 | SJKHZT | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户主体 |
| 7 | DJZ | VARCHAR2(1000) | YES | 浏览按钮 | UF_CPZWH | 定价组 |
| 43 | PP | VARCHAR2(1000) | YES | 浏览按钮 | UF_PP | 品牌 |
| 44 | JYTC | VARCHAR2(1000) | YES | 浏览按钮 | UF_JYTC | 检验套餐 |
```

## 注意事项

1. **大小写处理**：Oracle表名和字段名通常大写，查询时使用大写
2. **权限问题**：确保数据库用户有访问 `all_*` 表的权限
3. **Schema前缀**：跨Schema查询需要指定owner或使用 synonym
4. **浏览按钮表**：自定义浏览框对应的实体表可能不在当前数据库中

## 依赖

- python-oracledb
- 项目数据库配置（config/settings.yaml 或 .env）
- Oracle Instant Client（用于Thick Mode）

## 相关文件

- 脚本：`{skill_dir}/scripts/get_data_dictionary.py`
- 输出目录：`docs/E9Data/`
