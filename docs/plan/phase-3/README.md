# Phase 3: 数据查询模块

## 概述

Phase 3 目标是实现报价单数据查询和字段映射功能，根据 wybs（报价单号）查询报价单主表和明细表数据，并转换为系统内部模型。

## 设计文档清单

| 文档编号 | 文档名称 | 说明 | 状态 |
|----------|----------|------|------|
| 01 | [01-data-query.md](./01-data-query.md) | 数据查询模块设计 | 已更新 |
| 02 | [02-field-mapping.md](./02-field-mapping.md) | 数据库字段映射 | 已完成 |
| 03 | [03-models.md](./03-models.md) | 数据模型定义（含字段对照） | 新增 |

## 任务清单

| 序号 | 任务 | 产出物 | 依赖 |
|------|------|--------|------|
| 3.1 | 数据模型定义 | `src/models/quotation.py` | Phase 2 |
| 3.2 | 字段映射配置 | `config/field_mapping.yaml` | 3.1 |
| 3.3 | 报价单主表查询 | `src/queries/quotation.py` | 3.1 |
| 3.4 | 报价单明细查询 | `src/queries/quotation_detail.py` | 3.1 |
| 3.5 | 数据转换器 | `src/transformers/data_transformer.py` | 3.2, 3.3, 3.4 |
| 3.6 | 查询模块单元测试 | 测试用例 | 3.3, 3.4, 3.5 |

## 技术选型

- **ORM**: 原生 SQL（python-oracledb）
- **字段映射**: YAML 配置文件
- **数据类型转换**: Pydantic dataclass

## 核心功能

1. **报价单主表查询**: 根据 wybs 查询报价单主表
2. **报价单明细查询**: 查询 uf_htjgkst_dt1 明细表
3. **字段映射**: Oracle 字段到系统模型的映射配置
4. **数据转换**: 类型转换（Decimal、datetime）

## 风险点

- Oracle 表结构与文档不一致 → 字段映射配置化
- 字段名称变更 → 配置化映射便于维护

## 下一步

Phase 3 完成后，进入 **Phase 4: 模板匹配引擎**

---

*Phase 3 设计文档*
