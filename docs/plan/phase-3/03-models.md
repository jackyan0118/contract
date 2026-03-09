# Phase 3: 数据模型定义

## 概述

本文件定义报价单查询模块的数据模型，基于实际数据库表结构（uf_htjgkst / uf_htjgkst_dt1）。

> **数据字典**: 完整字段信息请参考 [数据字典文档](../../E9Data/)：
> - [UF_HTJGKST 数据字典](../../E9Data/UF_HTJGKST.md)
> - [UF_HTJGKST_DT1 数据字典](../../E9Data/UF_HTJGKST_DT1.md)

## 实体对象表

价格附件系统涉及以下浏览按钮对应的实体表：

| 表名 | 用途 | 实体对象 |
|------|------|----------|
| UF_CRMKHKP | CRM客户卡片 | 客户主体、客户终端 |
| UF_CPZWH | 产品组维护 | 定价组 |
| UF_SAPCPLBQD | SAP产品类别清单 | 特殊价格说明 |
| UF_CPXF | 产品细分 | 产品细分 |
| UF_PP | 品牌 | 品牌 |
| UF_JYTC | 检验套餐 | 检验套餐 |
| UF_CPKXMJC | 项目简称 | 项目简称 |
| WORKFLOW_REQUESTBASE | 流程请求表 | 相关流程 |

> 详见 [实体对象汇总](../../E9Data/entity-summary.md)

## 数据模型与数据库字段对照

### 报价单主表 (Quotation) ↔ uf_htjgkst

| 模型字段 | Oracle字段 | 数据类型 | 说明 | 必填 |
|----------|------------|----------|------|------|
| id | ID | NUMBER(22) | 主键 | 是 |
| requestid | REQUESTID | NUMBER(22) | 流程RequestID | 否 |
| formmodeid | FORMMODEID | NUMBER(22) | 表单模式ID | 否 |
| creater | MODEDATACREATER | NUMBER(22) | 创建人 | 否 |
| createdate | MODEDATACREATEDATE | VARCHAR2(10) | 创建日期 | 否 |
| createtime | MODEDATACREATETIME | VARCHAR2(8) | 创建时间 | 否 |
| modeuuid | MODEUUID | VARCHAR2(100) | 流程UUID | 否 |
| form_biz_id | FORM_BIZ_ID | VARCHAR2(100) | 业务ID | 否 |
| lcbh | LCBH | VARCHAR2(999) | 流程编号 | 否 |
| htbh | HTBH | VARCHAR2(999) | 合同编号 | 否 |
| xglc | XGLC | NUMBER(22) | 相关流程 | 否 |
| wybs | WYBS | VARCHAR2(999) | **唯一标识（查询主键）** | 是 |

**查询主键**：使用 `WYBS`（唯一标识）作为查询条件

---

### 报价单明细表 (QuotationDetail) ↔ uf_htjgkst_dt1

| 模型字段 | Oracle字段 | 数据类型 | 说明 | 必填 |
|----------|------------|----------|------|------|
| id | ID | NUMBER(22) | 主键 | 是 |
| mainid | MAINID | NUMBER(22) | 主表ID（关联主表.ID） | 是 |
| wybs | WYBS | VARCHAR2(999) | 唯一标识 | 是 |
| lyxh | LYXH | NUMBER(22) | 序号 | 是 |
| wldm | WLDM | VARCHAR2(999) | 物料代码 | 否 |
| wlms | WLMS | VARCHAR2(999) | 物料描述 | 否 |
| gg | GG | VARCHAR2(999) | 规格 | 否 |
| dw | DW | VARCHAR2(999) | 单位 | 否 |
| jgms | JGMS | VARCHAR2(999) | 价格描述 | 否 |

#### 价格相关字段

| 模型字段 | Oracle字段 | 数据类型 | 说明 |
|----------|------------|----------|------|
| lsj | LSJ | NUMBER(22) | 零售价 |
| bzjxj | BZJXJ | NUMBER(22) | 标准价(升级价) |
| ghjy | GHJY | NUMBER(22) | 供货价 |
| zxkhkpdjy | ZXKHKPDJY | NUMBER(22) | 执行客户开单价(代理价) |
| jsj | JSJ | NUMBER(22) | 结算价 |
| klbfb | KLBFB | NUMBER(22) | 扣率百分比 |
| yhfdbfb | YHFDBFB | NUMBER(22) | 优惠幅度百分比 |

#### 状态标记字段

| 模型字段 | Oracle字段 | 数据类型 | 说明 |
|----------|------------|----------|------|
| sfwc | SFWC | NUMBER(22) | 是否完成 |
| sfjl | SFJL | NUMBER(22) | 是否记录 |
| sfjj | SFJJ | NUMBER(22) | 是否计价 |

#### 扩展字段（浏览按钮类型）

> **注意**: 以下字段在数据库中存储的是实体ID，显示值需要通过关联查询获取。
> 详见 [UF_HTJGKST_DT1 数据字典](../../E9Data/UF_HTJGKST_DT1.md)

| 模型字段 | Oracle字段 | 数据类型 | 字段类型 | 实体对象 | 说明 |
|----------|------------|----------|----------|----------|------|
| sjkht | SJKHZT | VARCHAR2(1000) | 浏览按钮 | UF_CRMKHKP | 设价客户主体 |
| djz | DJZ | VARCHAR2(1000) | 浏览按钮 | UF_CPZWH | 定价组 |
| djzmc | DJZMC | VARCHAR2(999) | 单行文本 | | 定价组名称 |
| sjkhan | SJKH | VARCHAR2(1000) | 浏览按钮 | UF_CRMKHKP | 设价客户 |
| sjkhan_zd | SJKHZD | VARCHAR2(1000) | 浏览按钮 | UF_CRMKHKP | 设价客户终端 |
| cpxf | CPXF | VARCHAR2(1000) | 浏览按钮 | UF_CPXF | 产品细分 |
| pp | PP | VARCHAR2(1000) | 浏览按钮 | UF_PP | 品牌 |
| jytc | JYTC | VARCHAR2(1000) | 浏览按钮 | UF_JYTC | 检验套餐 |
| xmjc | XMJC | VARCHAR2(1000) | 浏览按钮 | UF_CPKXMJC | 项目简称 |
| tsjgsm | TSJGSM | VARCHAR2(1000) | 浏览按钮 | UF_SAPCPLBQD | 特殊价格说明 |
| sjsj | SJSJ | CHAR(10) | 浏览按钮 | 日期 | 设价时间 |

#### 状态标记字段

| 模型字段 | Oracle字段 | 数据类型 | 字段类型 | 说明 |
|----------|------------|----------|----------|------|
| sfwc | SFWC | NUMBER | 选择框 | 是否外采 |
| sfjl | SFJL | NUMBER | 选择框 | 是否计量 |
| sfjj | SFJJ | NUMBER | 选择框 | 是否计奖 |
| jggxbj | JGGXBJ | NUMBER | 选择框 | 价格更新标记 |
| sjjd | SJJD | NUMBER | 选择框 | 设价节点 |
| sftqsj | SFTQSJ | NUMBER | 选择框 | 是否提前设价 |
| sftpsybjg | SFTPSYBJG | NUMBER | 选择框 | 是否突破事业部价格 |
| sjlx | SJLX | NUMBER | 选择框 | 设价类型 |

#### 价格相关字段（新增）

| 模型字段 | Oracle字段 | 数据类型 | 字段类型 | 说明 |
|----------|------------|----------|----------|------|
| xzxcjg | XZXJG | NUMBER(38,2) | 单行文本 | 现执行价格 |
| tpj | TPJ | NUMBER(38,2) | 单行文本 | 突破价 |
| sczdjjc | SCZDJJC | NUMBER(38,2) | 单行文本 | 市场指导价_集采 |
| sczdjfjc | SCZDJFJC | NUMBER(38,2) | 单行文本 | 市场指导价_非集采 |
| bzjxjjc | BZJXJJC | NUMBER(38,2) | 单行文本 | 标准经销价_集采 |
| bzjxjfjc | BZJXJFJC | NUMBER(38,2) | 单行文本 | 标准经销价_非集采 |
| jcZbj | JCZBJ | NUMBER(38,2) | 单行文本 | 集采中标价 |
| jcjxj | JCJXJ | NUMBER(38,2) | 单行文本 | 集采经销价 |
| jgjcy | JGJCY | NUMBER(38,2) | 单行文本 | 价格间差异 |

---

## Pydantic 模型定义

### src/models/__init__.py

```python
"""数据模型模块."""

from .quotation import Quotation, QuotationDetail, QuotationItem

__all__ = [
    "Quotation",
    "QuotationDetail",
    "QuotationItem",
]
```

### src/models/quotation.py

```python
"""报价单数据模型."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Quotation:
    """报价单主表模型.

    对应数据库表: uf_htjgkst
    查询主键: WYBS (唯一标识)
    """

    # 主键
    id: int
    wybs: str  # 唯一标识（查询主键）

    # 流程相关
    requestid: Optional[int] = None
    formmodeid: Optional[int] = None
    modeuuid: Optional[str] = None
    form_biz_id: Optional[str] = None

    # 业务字段
    lcbh: Optional[str] = None  # 流程编号
    htbh: Optional[str] = None  # 合同编号
    xglc: Optional[int] = None  # 相关流程

    # 创建信息
    creater: Optional[int] = None
    createdate: Optional[str] = None
    createtime: Optional[str] = None


@dataclass
class QuotationDetail:
    """报价单明细模型.

    对应数据库表: uf_htjgkst_dt1
    关联主表: MAINID -> uf_htjgkst.ID
    """

    # 主键
    id: int
    mainid: int  # 关联主表.ID
    wybs: str  # 唯一标识

    # 序号
    lyxh: int

    # 物料信息
    wldm: Optional[str] = None  # 物料代码
    wlms: Optional[str] = None  # 物料描述
    gg: Optional[str] = None  # 规格
    dw: Optional[str] = None  # 单位

    # 价格字段
    lsj: Optional[Decimal] = None  # 零售价
    bzjxj: Optional[Decimal] = None  # 标准价(升级价)
    ghjy: Optional[Decimal] = None  # 供货价
    zxkhkpdjy: Optional[Decimal] = None  # 执行客户开单价
    jsj: Optional[Decimal] = None  # 结算价
    klbfb: Optional[Decimal] = None  # 扣率百分比
    yhfdbfb: Optional[Decimal] = None  # 优惠幅度百分比

    # 价格描述
    jgms: Optional[str] = None

    # 状态标记
    sfwc: Optional[int] = None  # 是否外采
    sfjl: Optional[int] = None  # 是否计量
    sfjj: Optional[int] = None  # 是否计奖
    bz: Optional[str] = None  # 备注

    # 价格标记
    jggxbj: Optional[int] = None  # 价格更新标记
    sjjd: Optional[int] = None  # 设价节点
    sftqsj: Optional[int] = None  # 是否提前设价
    sftpsybjg: Optional[int] = None  # 是否突破事业部价格
    sjlx: Optional[int] = None  # 设价类型

    # 浏览按钮字段（存储实体ID）
    sjkht: Optional[str] = None  # 设价客户主体
    sjkhan: Optional[str] = None  # 设价客户
    sjkhan_zd: Optional[str] = None  # 设价客户终端
    djz: Optional[str] = None  # 定价组
    tsjgsm: Optional[str] = None  # 特殊价格说明
    cpxf: Optional[str] = None  # 产品细分
    pp: Optional[str] = None  # 品牌
    jytc: Optional[str] = None  # 检验套餐
    xmjc: Optional[str] = None  # 项目简称
    sjsj: Optional[str] = None  # 设价时间

    # 扩展价格字段
    xzxcjg: Optional[Decimal] = None  # 现执行价格
    tpj: Optional[Decimal] = None  # 突破价
    sczdjjc: Optional[Decimal] = None  # 市场指导价_集采
    sczdjfjc: Optional[Decimal] = None  # 市场指导价_非集采
    bzjxjjc: Optional[Decimal] = None  # 标准经销价_集采
    bzjxjfjc: Optional[Decimal] = None  # 标准经销价_非集采
    jczbj: Optional[Decimal] = None  # 集采中标价
    jcjxj: Optional[Decimal] = None  # 集采经销价
    jgjcy: Optional[Decimal] = None  # 价格间差异


@dataclass
class QuotationItem:
    """报价单项（合并主表和明细的完整数据）.

    这是系统内部使用的完整报价单模型，
    包含主表信息和明细列表。
    """

    # 主表核心字段
    wybs: str  # 唯一标识（查询主键）
    id: int = 0  # 主表主键

    # 扩展字段
    lcbh: Optional[str] = None  # 流程编号
    htbh: Optional[str] = None  # 合同编号
    xglc: Optional[int] = None  # 相关流程

    # 明细列表
    items: list[QuotationDetail] = field(default_factory=list)

    def __post_init__(self):
        if self.items is None:
            self.items = []

    @property
    def item_count(self) -> int:
        """明细行数."""
        return len(self.items)
```

---

## 字段类型映射

### Oracle → Python 类型对照表

| Oracle 数据类型 | Python 类型 | 转换说明 |
|----------------|-------------|----------|
| NUMBER(22) | int | 直接转换 |
| NUMBER(p,s) | Decimal | 使用 Decimal 保留精度 |
| VARCHAR2(n) | str | 直接转换 |
| CHAR(n) | str | 直接转换 |
| DATE | datetime | 转换为 datetime |
| CLOB | str | 转换为文本 |

### 特殊字段处理

| 字段 | 处理方式 |
|------|----------|
| 价格字段 (LSJ, BZJXJ, GHJY等) | 使用 Decimal，保留2位小数 |
| 日期字段 | 转换为 datetime 或 date |
| 空值 | 转换为 Python None |

---

## 使用示例

```python
from src.models import Quotation, QuotationDetail, QuotationItem

# 主表模型
quotation = Quotation(
    id=12345,
    wybs="20240301001",
    lcbh="LC202403001",
    htbb="HT202403001",
)

# 明细模型
detail = QuotationDetail(
    id=1,
    mainid=12345,
    wybs="20240301001",
    lyxh=1,
    wldm="M001",
    wlms="产品A",
    gg="规格A",
    dw="个",
    lsj=Decimal("100.00"),
    jsj=Decimal("80.00"),
)

# 完整报价单
item = QuotationItem(
    wybs="20240301001",
    id=12345,
    lcbh="LC202403001",
    items=[detail],
)
```

---

## 更新日志

| 日期 | 修改内容 |
|------|----------|
| 2026-03-09 | 初始版本，基于实际数据库表结构 |
| 2026-03-09 | 更新：添加浏览按钮字段、状态字段、扩展价格字段，引用数据字典文档 |
