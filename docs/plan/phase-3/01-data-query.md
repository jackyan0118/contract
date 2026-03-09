# Phase 3: 数据查询模块

## 概述

Phase 3 目标是实现报价单数据查询和字段映射功能，根据 wybs（报价单号）查询报价单主表和明细表数据，并转换为系统内部模型。

## 任务清单

| 序号 | 任务 | 产出物 | 依赖 |
|------|------|--------|------|
| 3.1 | 数据模型定义 | `src/models/quotation.py` | Phase 2 |
| 3.2 | 字段映射配置 | `config/field_mapping.yaml` | 3.1 |
| 3.3 | 报价单主表查询 | `src/queries/quotation.py` | 3.1 |
| 3.4 | 报价单明细查询 | `src/queries/quotation_detail.py` | 3.1 |
| 3.5 | 数据转换器 | `src/transformers/data_transformer.py` | 3.2, 3.3, 3.4 |
| 3.6 | 查询模块单元测试 | 测试用例 | 3.3, 3.4, 3.5 |

## 架构设计

```
src/
├── models/
│   └── quotation.py          # 报价单数据模型
├── queries/
│   ├── quotation.py          # 报价单主表查询
│   └── quotation_detail.py  # 报价单明细查询
├── transformers/
│   └── data_transformer.py  # 数据转换器
└── __init__.py
```

## 数据库表信息

根据实际数据库查询结果：

| 表类型 | 表名 | Schema | 说明 |
|--------|------|--------|------|
| 主表 | uf_htjgkst | ecology | 报价单主表（15个字段） |
| 明细表 | uf_htjgkst_dt1 | ecology | 报价单明细表（46个字段） |

### 主表字段 (uf_htjgkst)

| 序号 | 字段名 | 数据类型 | 说明 |
|------|--------|----------|------|
| 1 | ID | NUMBER(22) | 主键 |
| 2 | REQUESTID | NUMBER(22) | 流程RequestID |
| 3 | FORMMODEID | NUMBER(22) | 表单模式ID |
| 4 | MODEDATACREATER | NUMBER(22) | 创建人 |
| 5 | MODEDATACREATERTYPE | NUMBER(22) | 创建人类型 |
| 6 | MODEDATACREATEDATE | VARCHAR2(10) | 创建日期 |
| 7 | MODEDATACREATETIME | VARCHAR2(8) | 创建时间 |
| 8 | MODEUUID | VARCHAR2(100) | 流程UUID |
| 9 | FORM_BIZ_ID | VARCHAR2(100) | 业务ID |
| 10 | LCBH | VARCHAR2(999) | 流程编号 |
| 11 | HTBH | VARCHAR2(999) | 合同编号 |
| 12 | XGLC | NUMBER(22) | 相关流程 |
| 13 | WYBS | VARCHAR2(999) | 唯一标识（查询主键） |
| 14 | MODEDATAMODIFIER | NUMBER(22) | 修改人 |
| 15 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | 修改时间 |

### 明细表字段 (uf_htjgkst_dt1)

关键字段：

| 序号 | 字段名 | 数据类型 | 说明 |
|------|--------|----------|------|
| 1 | ID | NUMBER(22) | 主键 |
| 2 | MAINID | NUMBER(22) | 主表ID（关联主表.ID） |
| 3 | SJKHZT | VARCHAR2(1000) | 客户主体 |
| 4 | LSH | VARCHAR2(999) | 流水号 |
| 5 | WYBS | VARCHAR2(999) | 唯一标识 |
| 6 | LYXH | NUMBER(22) | 序号 |
| 7 | DJZ | VARCHAR2(1000) | 等级 |
| 8 | DJZMC | VARCHAR2(999) | 等级名称 |
| 9 | WLDM | VARCHAR2(999) | 物料代码 |
| 10 | WLMS | VARCHAR2(999) | 物料描述 |
| 11 | SFWC | NUMBER(22) | 是否完成 |
| 12 | GG | VARCHAR2(999) | 规格 |
| 13 | DW | VARCHAR2(999) | 单位 |
| 14 | JGMS | VARCHAR2(999) | 价格描述 |
| 15 | LSJ | NUMBER(22) | 零售价 |
| 16 | BZJXJ | NUMBER(22) | 标准价(升级价) |
| 17 | GHJY | NUMBER(22) | 供货价 |
| 18 | ZXKHKPDJY | NUMBER(22) | 执行客户开单价 |
| 19 | JSJ | NUMBER(22) | 结算价 |
| 20-46 | ... | ... | 其他价格字段 |

## 技术选型

- **ORM**: SQLAlchemy 2.0 (可选) 或原生 SQL
- **字段映射**: YAML 配置文件
- **数据类型转换**: Pydantic 模型验证

## 代码实现

> **注意**: 数据模型定义已拆分到独立文档，详见 [03-models.md](./03-models.md)

### 3.2 字段映射配置

#### config/field_mapping.yaml

基于实际数据库结构（uf_htjgkst / uf_htjgkst_dt1）：

```yaml
# 字段映射配置
# Oracle 字段名 -> 系统内部字段名

quotation:
  # 报价单主表字段映射 (表: uf_htjgkst)
  mapping:
    WYBS: "wybs"           # 唯一标识（查询主键）
    LCBH: "lcbh"           # 流程编号
    HTBH: "htbh"           # 合同编号
    XGLC: "xglc"           # 相关流程
    ID: "id"               # 主键
    REQUESTID: "requestid" # 流程RequestID
    FORMMODEID: "formmodeid" # 表单模式ID
    MODEDATACREATER: "creater" # 创建人
    MODEDATACREATEDATE: "createdate" # 创建日期
    MODEDATACREATETIME: "createtime" # 创建时间

  # 数据类型转换
  types:
    wybs: "str"
    lcbh: "str"
    htbh: "str"
    xglc: "int"
    id: "int"
    requestid: "int"
    formmodeid: "int"
    creater: "int"
    createdate: "str"
    createtime: "str"

quotation_detail:
  # 报价单明细表字段映射 (表: uf_htjgkst_dt1)
  mapping:
    MAINID: "mainid"       # 主表ID
    WYBS: "wybs"           # 唯一标识
    LYXH: "lyxh"           # 序号
    WLDM: "wldm"           # 物料代码
    WLMS: "wlms"           # 物料描述
    GG: "gg"               # 规格
    DW: "dw"               # 单位
    JGMS: "jgms"           # 价格描述
    LSJ: "lsj"             # 零售价
    BZJXJ: "bzjxj"         # 标准价(升级价)
    GHJY: "ghjy"           # 供货价
    ZXKHKPDJY: "zxkhkpdjy" # 执行客户开单价
    JSJ: "jsj"             # 结算价
    KLBFB: "klbfb"         # 扣率百分比
    YHFDBFB: "yhfdbfb"     # 优惠幅度百分比
    BZ: "bz"               # 备注
    SFWC: "sfwc"           # 是否完成
    SFJL: "sfjl"           # 是否记录
    SFJJ: "sfjj"           # 是否计价

  types:
    mainid: "int"
    wybs: "str"
    lyxh: "int"
    wldm: "str"
    wlms: "str"
    gg: "str"
    dw: "str"
    jgms: "str"
    lsj: "decimal"
    bzjxj: "decimal"
    ghjy: "decimal"
    zxkhkpdjy: "decimal"
    jsj: "decimal"
    klbfb: "decimal"
    yhfdbfb: "decimal"
    bz: "str"
    sfwc: "int"
    sfjl: "int"
    sfjj: "int"
```

### 3.3 报价单主表查询

#### src/queries/__init__.py

```python
"""查询模块."""

from .quotation import get_quotation_by_wybs
from .quotation_detail import get_quotation_details

__all__ = [
    "get_quotation_by_wybs",
    "get_quotation_details",
]
```

#### src/queries/quotation.py

```python
"""报价单主表查询."""

from __future__ import annotations

from typing import Optional

from src.database import get_connection_pool
from src.exceptions import QueryException
from src.utils.logger import get_logger

logger = get_logger("queries.quotation")

# 报价单主表查询 SQL (表: uf_htjgkst)
QUERY_QUOTATION_SQL = """
    SELECT
        ID,                    -- 主键
        REQUESTID,             -- 流程RequestID
        FORMMODEID,            -- 表单模式ID
        MODEDATACREATER,       -- 创建人
        MODEDATACREATEDATE,    -- 创建日期
        MODEDATACREATETIME,     -- 创建时间
        MODEUUID,               -- 流程UUID
        FORM_BIZ_ID,           -- 业务ID
        LCBH,                  -- 流程编号
        HTBH,                  -- 合同编号
        XGLC,                  -- 相关流程
        WYBS                   -- 唯一标识(查询主键)
    FROM {table_name}
    WHERE WYBS = :wybs
"""

# 报价单明细表 SQL 模板 (表: uf_htjgkst_dt1)
QUERY_DETAIL_SQL_TEMPLATE = """
    SELECT
        ID,                 -- 主键
        MAINID,             -- 主表ID
        WYBS,               -- 唯一标识
        LYXH,               -- 序号
        WLDM,               -- 物料代码
        WLMS,               -- 物料描述
        GG,                 -- 规格
        DW,                 -- 单位
        JGMS,               -- 价格描述
        LSJ,                -- 零售价
        BZJXJ,              -- 标准价(升级价)
        GHJY,               -- 供货价
        ZXKHKPDJY,          -- 执行客户开单价
        JSJ,                -- 结算价
        KLBFB,              -- 扣率百分比
        YHFDBFB,            -- 优惠幅度百分比
        BZ,                 -- 备注
        SFWC,               -- 是否完成
        SFJL,               -- 是否记录
        SFJJ                -- 是否计价
    FROM {table_name}
    WHERE WYBS = :wybs
    ORDER BY LYXH
"""


def _get_table_name(table_key: str) -> str:
    """获取带 schema 的表名.

    Args:
        table_key: 表标识，如 "quotation" 或 "quotation_detail"

    Returns:
        带 schema 的表名
    """
    from src.database.config import get_database_config

    db_config = get_database_config()
    table_map = {
        "quotation": "uf_htjgkst",
        "quotation_detail": "uf_htjgkst_dt1",
    }
    table_name = table_map.get(table_key, table_key)
    return db_config.get_qualified_table(table_name)


def get_quotation_by_wybs(wybs: str) -> Optional[dict]:
    """根据报价单号查询报价单主表数据.

    Args:
        wybs: 报价单编号

    Returns:
        报价单主表数据字典，无数据返回 None

    Raises:
        QueryException: 查询失败时抛出
    """
    if not wybs or not wybs.strip():
        raise QueryException(reason="报价单号不能为空")

    wybs = wybs.strip()
    logger.info("查询报价单主表", context={"wybs": wybs})

    # 获取带 schema 的表名
    table_name = _get_table_name("quotation")
    sql = QUERY_QUOTATION_SQL.format(table_name=table_name)

    pool = get_connection_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"wybs": wybs})
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()

                if row is None:
                    logger.warning("报价单不存在", context={"wybs": wybs})
                    return None

                # 将 Oracle 列名转换为字典
                result = dict(zip(columns, row, strict=False))
                logger.info(
                    "查询报价单成功",
                    context={"wybs": wybs, "has_data": True},
                )
                return result

    except Exception as e:
        logger.error("查询报价单失败", context={"wybs": wybs})
        raise QueryException(reason="查询报价单失败") from e


# 报价单列表查询 SQL（模板）
LIST_QUOTATIONS_SQL = """
    SELECT
        WYBS, WLDW, ZDSJ, DJZT, JE, SL
    FROM {table_name}
    ORDER BY ZDSJ DESC
    OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
"""

# 最大分页限制
MAX_LIMIT = 1000


def list_quotations(limit: int = 100, offset: int = 0) -> list[dict]:
    """查询报价单列表（分页）.

    Args:
        limit: 返回数量限制，最大 1000
        offset: 偏移量，不能为负数

    Returns:
        报价单列表

    Raises:
        QueryException: 参数校验失败或查询失败
    """
    # 参数校验
    if limit <= 0:
        raise QueryException(reason="limit 必须大于 0")
    if limit > MAX_LIMIT:
        raise QueryException(reason=f"limit 不能超过 {MAX_LIMIT}")
    if offset < 0:
        raise QueryException(reason="offset 不能为负数")

    logger.info("查询报价单列表", context={"limit": limit, "offset": offset})

    # 获取带 schema 的表名
    table_name = _get_table_name("quotation")
    sql = LIST_QUOTATIONS_SQL.format(table_name=table_name)

    pool = get_connection_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    {"limit": limit, "offset": offset},
                )
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
                logger.info(
                    "查询报价单列表成功",
                    context={"count": len(results)},
                )
                return results
    except Exception as e:
        logger.error("查询报价单列表失败")
        raise QueryException(reason="查询报价单列表失败") from e
```

### 3.4 报价单明细查询

#### src/queries/quotation_detail.py

```python
"""报价单明细查询."""

from __future__ import annotations

from typing import Optional

from src.database import get_connection_pool
from src.exceptions import QueryException
from src.utils.logger import get_logger

logger = get_logger("queries.quotation_detail")


def get_quotation_details(wybs: str) -> list[dict]:
    """根据报价单号查询报价单明细数据.

    Args:
        wybs: 报价单编号

    Returns:
        报价单明细列表

    Raises:
        QueryException: 查询失败时抛出
    """
    if not wybs or not wybs.strip():
        raise QueryException(reason="报价单号不能为空")

    wybs = wybs.strip()
    logger.info("查询报价单明细", context={"wybs": wybs})

    # 获取带 schema 的表名
    table_name = _get_table_name("quotation_detail")
    sql = QUERY_DETAIL_SQL_TEMPLATE.format(table_name=table_name)

    pool = get_connection_pool()
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, {"wybs": wybs})
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                results = [dict(zip(columns, row, strict=False)) for row in rows]
                logger.info(
                    "查询报价单明细成功",
                    context={"wybs": wybs, "count": len(results)},
                )
                return results

    except Exception as e:
        logger.error("查询报价单明细失败", context={"wybs": wybs})
        raise QueryException(reason="查询报价单明细失败") from e


def get_quotation_detail_count(wybs: str) -> int:
    """获取报价单明细数量.

    Args:
        wybs: 报价单编号

    Returns:
        明细行数
    """
    table_name = _get_table_name("quotation_detail")
    sql = f"SELECT COUNT(*) FROM {table_name} WHERE WYBS = :wybs"

    pool = get_connection_pool()
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, {"wybs": wybs})
            result = cursor.fetchone()
            return result[0] if result else 0
```

### 3.5 数据转换器

#### src/transformers/__init__.py

```python
"""数据转换模块."""

from .data_transformer import DataTransformer, transform_quotation

__all__ = [
    "DataTransformer",
    "transform_quotation",
]
```

#### src/transformers/data_transformer.py

```python
"""数据转换器."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

import yaml

from src.models.quotation import Quotation, QuotationDetail, QuotationItem
from src.queries import get_quotation_by_wybs, get_quotation_details
from src.utils.logger import get_logger

logger = get_logger("transformers.data_transformer")

# 全局配置缓存
_mapping_cache: Optional[dict] = None


def _get_mapping_config() -> dict:
    """获取字段映射配置（带缓存）."""
    global _mapping_cache
    if _mapping_cache is None:
        try:
            config_path = "config/field_mapping.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                _mapping_cache = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("字段映射配置文件不存在，使用默认映射")
            _mapping_cache = {
                "quotation": {
                    "mapping": {
                        "WYBS": "wybs", "WLDW": "wldw", "BZ": "bz", "ZDR": "zdr",
                        "ZDSJ": "zdsj", "SHR": "shr", "SHSJ": "shsj", "DJZT": "djzt",
                        "JE": "je", "SL": "sl", "CPXFL": "cpxfl", "DJJZ": "djjz",
                        "SFJC": "sfjc", "GHLX": "ghlx",
                    }
                },
                "quotation_detail": {
                    "mapping": {
                        "WYBS": "wybs", "MXH": "mxh", "CPBM": "cpbm", "CPMC": "cpmc",
                        "GG": "gg", "DW": "dw", "DJ": "dj", "JE": "je", "SL": "sl",
                        "SCSXRQ": "scsxrq", "PH": "ph",
                    }
                },
            }
        except yaml.YAMLError as e:
            logger.error("字段映射配置文件解析失败", context={"error": str(e)})
            _mapping_cache = {}
    return _mapping_cache


class DataTransformer:
    """数据转换器 - 将 Oracle 查询结果转换为系统模型."""

    def __init__(self, mapping_config: Optional[dict] = None):
        """初始化数据转换器.

        Args:
            mapping_config: 字段映射配置，默认从缓存加载
        """
        if mapping_config is None:
            mapping_config = _get_mapping_config()
        self._mapping = mapping_config

    def transform_quotation(self, raw_data: dict) -> Quotation:
        """转换报价单主表数据.

        Args:
            raw_data: Oracle 查询结果字典

        Returns:
            Quotation 模型实例
        """
        mapping = self._mapping.get("quotation", {}).get("mapping", {})

        # 构建转换后的字典
        transformed = {}
        for oracle_field, model_field in mapping.items():
            value = raw_data.get(oracle_field)
            transformed[model_field] = self._convert_value(value, model_field)

        return Quotation(**transformed)

    def transform_quotation_detail(self, raw_data: dict) -> QuotationDetail:
        """转换报价单明细数据.

        Args:
            raw_data: Oracle 查询结果字典

        Returns:
            QuotationDetail 模型实例
        """
        mapping = self._mapping.get("quotation_detail", {}).get("mapping", {})

        transformed = {}
        for oracle_field, model_field in mapping.items():
            value = raw_data.get(oracle_field)
            transformed[model_field] = self._convert_value(value, model_field)

        return QuotationDetail(**transformed)

    def _convert_value(self, value: Any, field_name: str) -> Any:
        """类型转换.

        Args:
            value: 原始值
            field_name: 字段名

        Returns:
            转换后的值
        """
        if value is None:
            return None

        # 金额字段 - 转换为 Decimal
        if field_name in ("je", "dj"):
            if isinstance(value, (int, float)):
                return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return value

        # 数量字段 - 转换为 int
        if field_name in ("sl", "mxh"):
            if isinstance(value, (int, float)):
                return int(value)
            return value

        # 时间字段 - 转换为 datetime
        if field_name in ("zdsj", "shsj", "scsxrq"):
            if isinstance(value, datetime):
                return value
            if isinstance(value, str):
                try:
                    # 尝试解析 Oracle 日期格式
                    return datetime.fromisoformat(value.replace(" ", "T"))
                except ValueError:
                    return None
            return value

        return value


def transform_quotation(wybs: str) -> Optional[QuotationItem]:
    """转换报价单数据（主表 + 明细）.

    这是主要入口函数，将 Oracle 查询结果转换为完整的报价单模型。

    Args:
        wybs: 报价单编号

    Returns:
        QuotationItem 实例，无数据返回 None

    Raises:
        QueryException: 查询或转换失败时抛出
    """
    logger.info("开始转换报价单数据", context={"wybs": wybs})

    # 查询主表数据
    raw_quotation = get_quotation_by_wybs(wybs)
    if raw_quotation is None:
        return None

    # 查询明细数据
    raw_details = get_quotation_details(wybs)

    # 创建转换器
    transformer = DataTransformer()

    # 转换主表
    quotation = transformer.transform_quotation(raw_quotation)

    # 转换明细
    details = [transformer.transform_quotation_detail(d) for d in raw_details]

    # 构建完整报价单项
    item = QuotationItem(
        wybs=quotation.wybs,
        wldw=quotation.wldw,
        bz=quotation.bz,
        zdr=quotation.zdr,
        zdsj=quotation.zdsj,
        djzt=quotation.djzt,
        je=quotation.je,
        sl=quotation.sl,
        cpxfl=quotation.cpxfl,
        djjz=quotation.djjz,
        sfjc=quotation.sfjc,
        ghlx=quotation.ghlx,
        items=details,
    )

    logger.info(
        "报价单数据转换完成",
        context={
            "wybs": wybs,
            "item_count": len(details),
        },
    )

    return item
```

## 异常定义

### src/exceptions/query.py

```python
"""查询异常."""


class QueryException(Exception):
    """查询异常基类."""

    def __init__(self, reason: str = "", detail: dict = None):
        self.reason = reason
        self.detail = detail or {}
        super().__init__(reason)
```

## 验收标准

- [ ] 可根据 wybs 查询报价单主表数据
- [ ] 可查询报价单明细数据（uf_htjgkst_dt1）
- [ ] 数据字段映射可配置
- [ ] 支持数据类型转换（Decimal、datetime）
- [ ] 返回完整的 QuotationItem（包含明细列表）
- [ ] 错误处理完善，无数据时返回 None
- [ ] 日志记录完整
- [ ] 支持配置化的 Schema 前缀（通过 `DB_SCHEMA` 环境变量或配置文件）

## Schema 配置说明

### 配置方式

通过配置文件 `config/settings.yaml` 指定 Schema：

```yaml
database:
  dsn: "oracle://user:pass@host:1521/service"
  db_schema: "ecology"    # Oracle Schema/用户
```

**注意**: 使用 `db_schema` 字段名，避免与 Pydantic BaseSettings 冲突。

### 表名自动处理

系统会自动为表名添加 Schema 前缀：

| 配置 | 查询实际使用 |
|------|-------------|
| `db_schema=` (空) | `FROM uf_htjgkst` |
| `db_schema=ecology` | `FROM ecology.uf_htjgkst` |

### 当前配置

- **Schema**: ecology
- **主表**: ecology.uf_htjgkst
- **明细表**: ecology.uf_htjgkst_dt1

## 风险点

| 风险项 | 风险等级 | 缓解措施 |
|--------|----------|----------|
| Oracle 表结构与文档不一致 | 中 | 创建字段映射配置，配置化处理 |
| 字段名称变更风险 | 低 | 使用配置化字段映射，便于维护 |
| 数据类型转换异常 | 中 | 使用 Pydantic 验证，异常捕获 |

## 下一步

Phase 3 完成后，进入 **Phase 4: 模板匹配引擎**

---

*文档版本：1.0*
*创建日期：2026-03-09*
