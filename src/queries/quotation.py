"""报价单主表查询."""

from __future__ import annotations

from typing import Optional

from src.database import get_connection_pool
from src.database.config import get_database_config
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

# 报价单列表查询 SQL（模板）
LIST_QUOTATIONS_SQL = """
    SELECT
        WYBS, LCBH, HTBH, XGLC, MODEDATACREATEDATE
    FROM {table_name}
    ORDER BY MODEDATACREATEDATE DESC
    OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
"""

# 最大分页限制
MAX_LIMIT = 1000


def _get_table_name(table_key: str) -> str:
    """获取带 schema 的表名.

    Args:
        table_key: 表标识，如 "quotation" 或 "quotation_detail"

    Returns:
        带 schema 的表名
    """
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
        raise QueryException(
            query="",
            reason="报价单号不能为空",
        )

    wybs = wybs.strip()
    logger.info("查询报价单主表", extra={"wybs": wybs})

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
                    logger.warning("报价单不存在", extra={"wybs": wybs})
                    return None

                # 将 Oracle 列名转换为字典
                result = dict(zip(columns, row, strict=False))
                logger.info(
                    "查询报价单成功",
                    extra={"wybs": wybs, "has_data": True},
                )
                return result

    except QueryException:
        # 重新抛出 QueryException
        raise
    except Exception as e:
        logger.error("查询报价单失败", extra={"wybs": wybs})
        raise QueryException(
            query=sql,
            reason="查询报价单失败",
        ) from e


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
        raise QueryException(
            query="",
            reason="limit 必须大于 0",
        )
    if limit > MAX_LIMIT:
        raise QueryException(
            query="",
            reason=f"limit 不能超过 {MAX_LIMIT}",
        )
    if offset < 0:
        raise QueryException(
            query="",
            reason="offset 不能为负数",
        )

    logger.info("查询报价单列表", extra={"limit": limit, "offset": offset})

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
                    extra={"count": len(results)},
                )
                return results
    except QueryException:
        raise
    except Exception as e:
        logger.error("查询报价单列表失败")
        raise QueryException(
            query=sql,
            reason="查询报价单列表失败",
        ) from e
