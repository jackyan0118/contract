"""报价单明细查询模块.

根据 wybs（报价单号）查询报价单明细数据。
"""

from __future__ import annotations

from src.database import get_connection_pool
from src.database.config import get_database_config
from src.exceptions import QueryException
from src.utils.logger import get_logger

logger = get_logger("queries.quotation_detail")

# 明细表名
_DETAIL_TABLE = "uf_htjgkst_dt1"

# 查询字段
_DETAIL_COLUMNS = [
    "ID",
    "MAINID",
    "WYBS",
    "LYXH",
    "WLDM",
    "WLMS",
    "GG",
    "DW",
    "JGMS",
    "LSJ",
    "BZJXJ",
    "GHJY",
    "ZXKHKPDJY",
    "JSJ",
    "KLBFB",
    "YHFDBFB",
    "BZ",
    "SFWC",
    "SFJL",
    "SFJJ",
    # 价格更新相关字段
    "JGGXBJ",
    "SJJD",
    "SFTQSJ",
    "SFTPSYBJG",
    "SJLX",
    "SJSJ",
    # 扩展价格字段
    "XZXJG",
    "TPJ",
    "SCZDJJC",
    "SCZDJFJC",
    "BZJXJJC",
    "BZJXJFJC",
    "JCZBJ",
    "JCJXJ",
    "JGJCY",
    # 其他扩展字段
    "TSJGSM",
    # 新增字段（本年供货价类型、是否集采）
    "BNGHJLX",
    "BNGHJLXZ",
    "SFJC",
]

# 明细查询 SQL 模板
_QUERY_DETAIL_SQL = f"""
SELECT {', '.join(_DETAIL_COLUMNS)}
FROM {{schema}}.{_DETAIL_TABLE}
WHERE WYBS = :wybs
ORDER BY LYXH
"""

# 计数 SQL 模板
_COUNT_DETAIL_SQL = f"""
SELECT COUNT(*) as CNT
FROM {{schema}}.{_DETAIL_TABLE}
WHERE WYBS = :wybs
"""


def _validate_wybs(wybs: str | None) -> str:
    """验证 wybs 参数.

    Args:
        wybs: 报价单号

    Returns:
        验证后的报价单号

    Raises:
        QueryException: wybs 为空或无效
    """
    if not wybs or not wybs.strip():
        raise QueryException(
            query="WYBS validation",
            reason="报价单号（wybs）不能为空",
        )
    return wybs.strip()


def _row_to_dict(row: tuple, columns: list[str]) -> dict:
    """将数据库行转换为字典.

    Args:
        row: 数据库行元组
        columns: 字段名列表

    Returns:
        字段名和值组成的字典
    """
    return dict(zip(columns, row))


def get_quotation_details(wybs: str) -> list[dict]:
    """根据 wybs 查询报价单明细数据.

    Args:
        wybs: 报价单号

    Returns:
        明细数据字典列表，按 LYXH 排序

    Raises:
        QueryException: 查询失败或 wybs 无效
    """
    wybs = _validate_wybs(wybs)

    db_config = get_database_config()
    table_name = db_config.get_qualified_table(_DETAIL_TABLE)
    sql = _QUERY_DETAIL_SQL.format(schema=db_config.schema or "")

    logger.info(
        "开始查询报价单明细",
        extra={"wybs": wybs, "table": table_name},
    )

    pool = get_connection_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, {"wybs": wybs})
                rows = cursor.fetchall()

                # 将行数据转换为字典列表
                details = [_row_to_dict(row, _DETAIL_COLUMNS) for row in rows]

                logger.info(
                    "报价单明细查询成功",
                    extra={
                        "wybs": wybs,
                        "count": len(details),
                    },
                )

                return details

            except QueryException:
                # 重新抛出 QueryException，不包装
                raise
            except Exception as e:
                logger.error(
                    "报价单明细查询失败",
                    extra={"wybs": wybs, "error": str(e)},
                )
                raise QueryException(query=sql, reason=str(e)) from e


def get_quotation_detail_count(wybs: str) -> int:
    """获取报价单明细行数.

    Args:
        wybs: 报价单号

    Returns:
        明细行数

    Raises:
        QueryException: 查询失败或 wybs 无效
    """
    wybs = _validate_wybs(wybs)

    db_config = get_database_config()
    sql = _COUNT_DETAIL_SQL.format(schema=db_config.schema or "")

    logger.info(
        "开始查询报价单明细数量",
        extra={"wybs": wybs},
    )

    pool = get_connection_pool()

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, {"wybs": wybs})
                row = cursor.fetchone()

                count = row[0] if row else 0

                logger.info(
                    "报价单明细数量查询成功",
                    extra={"wybs": wybs, "count": count},
                )

                return count

            except QueryException:
                # 重新抛出 QueryException，不包装
                raise
            except Exception as e:
                logger.error(
                    "报价单明细数量查询失败",
                    extra={"wybs": wybs, "error": str(e)},
                )
                raise QueryException(query=sql, reason=str(e)) from e
