#!/usr/bin/env python3
"""数据库连接验证脚本.

用于验证：
1. 数据库连接是否正常
2. Schema 配置是否正确
3. 查询功能是否正常

注意：配置从 config/settings.yaml 加载
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置工作目录为项目根目录
os.chdir(Path(__file__).parent.parent)

import oracledb

# 初始化 Thick Mode (需要 Oracle Instant Client)
ORACLE_INSTANT_CLIENT_PATH = os.environ.get("ORACLE_INSTANT_CLIENT", "/opt/oracle/instantclient")
try:
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print(f"[INFO] Thick Mode 初始化成功: {ORACLE_INSTANT_CLIENT_PATH}")
except Exception as e:
    print(f"[WARN] Thick Mode 初始化失败，将使用 Thin Mode: {e}")

from src.config import settings
from src.database.config import get_database_config


def print_section(title: str):
    """打印分隔标题."""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print('=' * 50)


def test_config():
    """测试配置加载."""
    print_section("1. 测试配置加载")

    # 显示数据库配置
    print(f"DSN: {settings.database.dsn.get_secret_value()[:50]}...")
    print(f"Schema: '{settings.database.db_schema}'")
    print(f"Min Connections: {settings.database.min_connections}")
    print(f"Max Connections: {settings.database.max_connections}")
    print(f"Connect Timeout: {settings.database.connect_timeout}s")
    print(f"Command Timeout: {settings.database.command_timeout}s")

    # 获取 DatabaseConfig
    db_config = get_database_config()
    print(f"\nDatabaseConfig Schema: '{db_config.schema}'")
    print(f"DatabaseConfig DSN: {db_config.dsn[:50]}...")

    print("\n[PASS] 配置加载成功")


def test_oracle_connection():
    """测试 Oracle 连接."""
    print_section("2. 测试 Oracle 连接")

    db_config = get_database_config()
    params = db_config.to_oracledb_params()

    print(f"User: {params.get('user')}")
    print(f"DSN: {params.get('dsn')}")

    try:
        # 直接连接测试（不使用连接池）
        conn = oracledb.connect(
            user=params.get("user"),
            password=params.get("password"),
            dsn=params.get("dsn"),
        )
        print(f"\n[PASS] Oracle 连接成功!")

        # 获取当前用户
        cursor = conn.cursor()
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        print(f"当前用户: {current_user}")

        cursor.close()
        conn.close()
        return True

    except oracledb.Error as e:
        print(f"\n[FAIL] Oracle 连接失败: {e}")
        return False


def test_schema_table():
    """测试 Schema 表查询."""
    print_section("3. 测试 Schema 表查询")

    db_config = get_database_config()
    schema = db_config.schema

    if not schema:
        print("[WARN] Schema 未配置，跳过 Schema 表查询测试")
        return True

    # 测试带 schema 的表名
    quotation_table = db_config.get_qualified_table("报价单主表")
    detail_table = db_config.get_qualified_table("uf_htjgkst_dt1")

    print(f"报价单主表: {quotation_table}")
    print(f"明细表: {detail_table}")

    params = db_config.to_oracledb_params()

    try:
        conn = oracledb.connect(
            user=params.get("user"),
            password=params.get("password"),
            dsn=params.get("dsn"),
        )
        cursor = conn.cursor()

        # 测试查询报价单主表
        print(f"\n测试查询: SELECT * FROM {quotation_table} WHERE ROWNUM <= 1")
        cursor.execute(f"SELECT * FROM {quotation_table} WHERE ROWNUM <= 1")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        print(f"列名: {columns[:5]}...")  # 只显示前5列
        print(f"行数: {len(rows)}")

        # 测试查询明细表
        print(f"\n测试查询: SELECT * FROM {detail_table} WHERE ROWNUM <= 1")
        cursor.execute(f"SELECT * FROM {detail_table} WHERE ROWNUM <= 1")
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        print(f"列名: {columns[:5]}...")
        print(f"行数: {len(rows)}")

        cursor.close()
        conn.close()

        print("\n[PASS] Schema 表查询成功")
        return True

    except oracledb.Error as e:
        print(f"\n[FAIL] Schema 表查询失败: {e}")
        return False


def test_query_quotation():
    """测试报价单查询."""
    print_section("4. 测试报价单查询（使用 _get_table_name）")

    # 导入查询模块（如果已实现）
    try:
        from src.database import get_connection_pool
        from src.queries.quotation import _get_table_name, get_quotation_by_wybs

        # 初始化连接池
        print("初始化连接池...")
        pool = get_connection_pool()
        pool.initialize()

        # 测试获取表名
        table_name = _get_table_name("quotation")
        print(f"报价单主表: {table_name}")

        print("\n[PASS] 查询模块加载成功")

        # 注意：这里不实际执行查询，因为需要有效的 wybs
        print("\n提示: 可以通过以下方式测试查询:")
        print("  from src.queries.quotation import get_quotation_by_wybs")
        print("  result = get_quotation_by_wybs('your_wybs')")

        return True

    except ImportError as e:
        print(f"[INFO] 查询模块尚未实现: {e}")
        return True
    except Exception as e:
        print(f"[WARN] 测试查询失败: {e}")
        return False


def main():
    """主函数."""
    print("\n" + "=" * 50)
    print("  数据库连接验证脚本")
    print("=" * 50)

    results = []

    # 1. 测试配置
    try:
        test_config()
        results.append(True)
    except Exception as e:
        print(f"\n[FAIL] 配置测试失败: {e}")
        results.append(False)

    # 2. 测试 Oracle 连接
    try:
        if test_oracle_connection():
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"\n[FAIL] Oracle 连接测试失败: {e}")
        results.append(False)

    # 3. 测试 Schema 表查询
    try:
        if test_schema_table():
            results.append(True)
        else:
            results.append(False)
    except Exception as e:
        print(f"\n[FAIL] Schema 表查询测试失败: {e}")
        results.append(False)

    # 4. 测试报价单查询
    try:
        test_query_quotation()
        results.append(True)
    except Exception as e:
        print(f"\n[FAIL] 报价单查询测试失败: {e}")
        results.append(False)

    # 总结
    print_section("测试结果汇总")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] 所有测试通过!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 项测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
