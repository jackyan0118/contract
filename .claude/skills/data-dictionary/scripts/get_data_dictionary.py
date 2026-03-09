#!/usr/bin/env python3
"""获取Oracle数据字典并生成Markdown文档.

用法:
    python get_data_dictionary.py                           # 生成所有可访问表的字典
    python get_data_dictionary.py -t UF_HTJGKST              # 指定单个表
    python get_data_dictionary.py -t UF_HTJGKST -s ECOLOGY   # 指定Schema和表
    python get_data_dictionary.py -t UF_HTJGKST,UF_HTJGKST_DT1  # 指定多个表
    python get_data_dictionary.py -o /path/to/output         # 指定输出目录
    python get_data_dictionary.py --list-tables             # 列出所有可访问的表
"""

import sys
import os
import argparse
import oracledb

# 添加项目路径
sys.path.insert(0, "/Users/yan/khb/contract")

# 初始化 Oracle Thick Mode
ORACLE_INSTANT_CLIENT_PATH = os.environ.get("ORACLE_INSTANT_CLIENT", "/opt/oracle/instantclient")
try:
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print(f"Oracle Thick Mode initialized with: {ORACLE_INSTANT_CLIENT_PATH}")
except Exception as e:
    print(f"Warning: Failed to init Thick Mode: {e}")
    print("Will try Thin Mode...")


from src.database.config import get_database_config

# 默认Schema
DEFAULT_SCHEMA = "ECOLOGY"

# 默认输出目录
DEFAULT_OUTPUT_DIR = "/Users/yan/khb/contract/docs/E9Data"

# 字段类型映射
FIELD_HTML_TYPE_MAP = {
    "1": "单行文本",
    "2": "多行文本",
    "3": "浏览按钮",
    "4": "Check框",
    "5": "选择框",
    "6": "附件上传",
    "7": "特殊字段",
}

# 标准浏览按钮类型映射
BROWSER_TYPE_MAP = {
    1: "单人力资源",
    2: "日期",
    3: "浏览按钮",
    4: "多人力资源",
    8: "部门",
    9: "部门(多选)",
    16: "流程浏览",
    17: "文档浏览",
    18: "项目浏览",
    19: "任务浏览",
    20: "CRM客户",
    21: "CRM联系人",
    22: "CRM产品",
    23: "会议浏览",
    24: "日程浏览",
    37: "自定义浏览",
    57: "知识库浏览",
    161: "自定义单选",
    162: "自定义多选",
    163: "明细表",
    164: "分部",
    165: "人员(单选)",
    166: "人员(多选)",
    167: "部门(单选)",
    168: "部门(多选)",
    169: "分部(单选)",
    170: "分部(多选)",
}


def get_browser_table(cursor, browser_code: str) -> str:
    """从 MODE_BROWSER 表获取自定义浏览框对应的实体表.

    Args:
        cursor: 数据库游标
        browser_code: 浏览框标识（如 'pp', 'cpkcpxf' 等）

    Returns:
        实体表名（如 'uf_pp', 'uf_cpxf' 等）
    """
    try:
        # 从 MODE_BROWSER 表查询
        # showname 字段存储浏览框标识
        cursor.execute("""
            SELECT name, showname, sqltext
            FROM ecology.mode_browser
            WHERE showname = :1
        """, [browser_code])
        row = cursor.fetchone()

        if row and row[2]:
            # 从 SQL 语句中提取表名
            sql = str(row[2]).upper()
            # 查找 from 后面的表名
            if "FROM UF_" in sql:
                idx = sql.find("FROM UF_")
                table_part = sql[idx + 5:].split()[0]
                return table_part
            elif "FROM UF_" in sql:
                idx = sql.find("FROM UF_")
                table_part = sql[idx + 5:].split()[0]
                return table_part

        # 如果没找到，返回原始标识
        return browser_code
    except Exception:
        return browser_code


def get_table_info(conn, schema: str, table_name: str) -> dict:
    """获取表的基本信息和字段信息."""
    cursor = conn.cursor()

    # 查询表基本信息
    cursor.execute("""
        SELECT table_name, tablespace_name
        FROM all_tables
        WHERE owner = :owner AND table_name = :table_name
    """, {"owner": schema.upper(), "table_name": table_name.upper()})
    table_info = cursor.fetchone()

    if not table_info:
        cursor.close()
        return None

    # 查询表注释
    cursor.execute("""
        SELECT comments
        FROM all_tab_comments
        WHERE owner = :owner AND table_name = :table_name
    """, {"owner": schema.upper(), "table_name": table_name.upper()})
    table_comment = cursor.fetchone()
    table_comment = table_comment[0] if table_comment and table_comment[0] else ""

    # 查询字段信息
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            data_length,
            data_precision,
            data_scale,
            nullable,
            column_id
        FROM all_tab_columns
        WHERE owner = :owner AND table_name = :table_name
        ORDER BY column_id
    """, {"owner": schema.upper(), "table_name": table_name.upper()})
    columns = cursor.fetchall()

    # 查询字段注释
    cursor.execute("""
        SELECT column_name, comments
        FROM all_col_comments
        WHERE owner = :owner AND table_name = :table_name
    """, {"owner": schema.upper(), "table_name": table_name.upper()})
    column_comments = {row[0]: row[1] for row in cursor.fetchall()}

    # 获取字段类型信息（从 workflow_billfield）
    field_types = get_field_types_from_bill(cursor, schema, table_name)

    # 尝试从 workflow_billfield 获取中文标签
    field_labels = get_field_labels_from_bill(cursor, schema, table_name)

    cursor.close()

    # 合并字段注释
    for col_name in column_comments:
        if not column_comments[col_name] and field_labels.get(col_name.upper()):
            column_comments[col_name] = field_labels[col_name.upper()]

    # 对于没有注释的字段，添加 workflow_billfield 标签
    for col_name in field_labels:
        if col_name.upper() not in column_comments or not column_comments.get(col_name.upper()):
            column_comments[col_name.upper()] = field_labels[col_name]

    return {
        "table_name": table_info[0],
        "tablespace": table_info[1] or "",
        "table_comment": table_comment,
        "columns": columns,
        "column_comments": column_comments,
        "field_types": field_types,
    }


def get_field_types_from_bill(cursor, schema: str, table_name: str) -> dict:
    """从 workflow_billfield 获取字段类型信息.

    Returns:
        dict: {字段名: {
            'fieldhtmltype': str,  # 字段表现形式
            'fieldhtmltype_name': str,  # 字段表现类型名称
            'type': int,  # 浏览按钮类型
            'type_name': str,  # 浏览按钮类型名称
            'fielddbtype': str,  # 字段数据库类型
            'browser_table': str,  # 浏览按钮对应的实体表
        }}
    """
    try:
        # 首先找到表单ID
        queries = [
            ("SELECT id, namelabel FROM ecology.workflow_bill WHERE tablename = :1", [table_name.upper()]),
            ("SELECT id, namelabel FROM ecology.workflow_bill WHERE tablename = :1", [table_name.lower()]),
        ]

        bill = None
        for sql, params in queries:
            cursor.execute(sql, params)
            bill = cursor.fetchone()
            if bill:
                break

        # 如果没找到，尝试根据表名关键词搜索
        if not bill:
            table_keyword = table_name.replace("UF_", "").replace("_DT1", "")
            cursor.execute("""
                SELECT DISTINCT b.id, b.namelabel
                FROM ecology.workflow_bill b
                WHERE b.namelabel LIKE :1
                AND ROWNUM <= 1
            """, [f"%{table_keyword}%"])
            bill = cursor.fetchone()

        if not bill:
            # 直接从 workflow_billfield 查询
            cursor.execute("""
                SELECT DISTINCT b.id, b.namelabel
                FROM ecology.workflow_bill b
                WHERE EXISTS (
                    SELECT 1 FROM ecology.workflow_billfield f
                    WHERE f.billid = b.id AND f.detailtable = :1
                )
                AND ROWNUM <= 1
            """, [table_name.lower()])
            bill = cursor.fetchone()

            if not bill:
                return {}

        bill_id = bill[0]

        # 查询字段类型信息
        cursor.execute("""
            SELECT
                fieldname,
                fieldhtmltype,
                type,
                fielddbtype,
                detailtable
            FROM ecology.workflow_billfield
            WHERE billid = :bill_id
            ORDER BY dsporder
        """, {"bill_id": bill_id})

        field_types = {}
        for row in cursor.fetchall():
            fieldname = row[0]
            fieldhtmltype = row[1]
            type_val = row[2]
            fielddbtype = row[3]
            detailtable = row[4]

            if not fieldname:
                continue

            # 判断字段属于哪个表
            detailtable_upper = detailtable.strip().upper() if detailtable and detailtable.strip() else ""
            table_name_upper = table_name.upper()

            # 明细表：detailtable 等于当前表名
            is_detail = detailtable_upper == table_name_upper
            # 主表：detailtable 为空
            is_main = detailtable_upper == ""

            # 只处理属于当前表的字段
            if not is_detail and not is_main:
                continue

            # 获取字段表现类型名称
            fieldhtmltype_str = str(fieldhtmltype) if fieldhtmltype else ""
            fieldhtmltype_name = FIELD_HTML_TYPE_MAP.get(fieldhtmltype_str, fieldhtmltype_str)

            # 获取浏览按钮类型名称和实体表
            type_name = ""
            browser_table = ""
            if fieldhtmltype_str == "3" and type_val:
                type_name = BROWSER_TYPE_MAP.get(type_val, f"type={type_val}")
                # 如果是自定义浏览按钮，从 fielddbtype 获取实体表
                if type_val in (161, 162) and fielddbtype and fielddbtype.startswith("browser."):
                    browser_code = fielddbtype.replace("browser.", "")
                    # 从 MODE_BROWSER 表获取实体表
                    browser_table = get_browser_table(cursor, browser_code)
                # 如果是标准浏览按钮，从 workflow_browserurl 获取实体表
                elif type_val:
                    try:
                        cursor.execute("""
                            SELECT tablename, columname, keycolumname
                            FROM ecology.workflow_browserurl
                            WHERE id = :1
                        """, [type_val])
                        br = cursor.fetchone()
                        if br:
                            browser_table = br[0] or ""
                    except Exception:
                        pass

            field_types[fieldname.upper()] = {
                "fieldhtmltype": fieldhtmltype_str,
                "fieldhtmltype_name": fieldhtmltype_name,
                "type": type_val,
                "type_name": type_name,
                "fielddbtype": fielddbtype,
                "browser_table": browser_table,
            }

        return field_types
    except Exception as e:
        print(f"    Warning: Could not get field types from workflow_billfield: {e}")
        return {}


def get_field_labels_from_bill(cursor, schema: str, table_name: str) -> dict:
    """从 workflow_billfield 获取字段的中文标签."""
    try:
        # 首先找到表单ID
        queries = [
            ("SELECT id, namelabel FROM ecology.workflow_bill WHERE tablename = :1", [table_name.upper()]),
            ("SELECT id, namelabel FROM ecology.workflow_bill WHERE tablename = :1", [table_name.lower()]),
        ]

        bill = None
        for sql, params in queries:
            cursor.execute(sql, params)
            bill = cursor.fetchone()
            if bill:
                break

        # 如果没找到，尝试根据表名关键词搜索
        if not bill:
            table_keyword = table_name.replace("UF_", "").replace("_DT1", "")
            cursor.execute("""
                SELECT DISTINCT b.id, b.namelabel
                FROM ecology.workflow_bill b
                WHERE b.namelabel LIKE :1
                AND ROWNUM <= 1
            """, [f"%{table_keyword}%"])
            bill = cursor.fetchone()

        if not bill:
            # 直接从 workflow_billfield 查询
            cursor.execute("""
                SELECT DISTINCT b.id, b.namelabel
                FROM ecology.workflow_bill b
                WHERE EXISTS (
                    SELECT 1 FROM ecology.workflow_billfield f
                    WHERE f.billid = b.id AND f.detailtable = :1
                )
                AND ROWNUM <= 1
            """, [table_name.lower()])
            bill = cursor.fetchone()

            if not bill:
                return {}

        bill_id = bill[0]

        # 查询字段标签 - 区分主表和明细表字段
        cursor.execute("""
            SELECT
                fieldname,
                fieldlabel,
                detailtable
            FROM ecology.workflow_billfield
            WHERE billid = :bill_id
            ORDER BY dsporder
        """, {"bill_id": bill_id})

        labels = {}
        for row in cursor.fetchall():
            fieldname = row[0]
            fieldlabel = row[1]
            detailtable = row[2]

            if not fieldname:
                continue

            # 判断字段属于哪个表
            detailtable_upper = detailtable.strip().upper() if detailtable and detailtable.strip() else ""
            table_name_upper = table_name.upper()

            # 明细表：detailtable 等于当前表名
            is_detail = detailtable_upper == table_name_upper
            # 主表：detailtable 为空
            is_main = detailtable_upper == ""

            # 只处理属于当前表的字段
            if not is_detail and not is_main:
                continue

            # 尝试获取中文标签
            label_text = None

            # 泛微E9的标签存储在 HTMLLABELINFO 表中
            if isinstance(fieldlabel, int):
                label_text = get_chinese_label_by_id(cursor, fieldlabel)

            if label_text:
                labels[fieldname.upper()] = label_text
            else:
                # 如果没有获取到中文标签，使用字段名
                labels[fieldname.upper()] = fieldname.upper()

        return labels
    except Exception as e:
        print(f"    Warning: Could not get field labels from workflow_billfield: {e}")
        return {}


def get_chinese_label_by_id(cursor, label_id: int) -> str:
    """通过标签ID获取中文标签文本."""
    try:
        # 泛微E9的标签存储在 HTMLLABELINFO 和 HTMLLABELINDEX 表中
        # languageid = 7 表示简体中文
        cursor.execute("""
            SELECT i.labelname
            FROM ecology.HTMLLABELINFO i
            WHERE i.indexid = :1 AND i.languageid = 7
        """, [label_id])
        row = cursor.fetchone()
        if row and row[0]:
            return str(row[0])
    except Exception:
        pass

    try:
        # 尝试从 HTMLLABELINDEX 直接获取
        cursor.execute("""
            SELECT i.indexdesc
            FROM ecology.HTMLLABELINDEX i
            WHERE i.id = :1
        """, [label_id])
        row = cursor.fetchone()
        if row and row[0]:
            return str(row[0])
    except Exception:
        pass

    return None


def format_data_type(col: tuple) -> str:
    """格式化数据类型."""
    data_type = col[1]
    data_length = col[2]
    data_precision = col[3]
    data_scale = col[4]

    if data_type in ("NUMBER", "FLOAT"):
        if data_precision and data_scale:
            return f"{data_type}({data_precision},{data_scale})"
        elif data_precision:
            return f"{data_type}({data_precision})"
        else:
            return data_type
    elif data_type in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR"):
        return f"{data_type}({data_length})"
    elif data_type == "DATE":
        return data_type
    elif data_type == "CLOB":
        return data_type
    elif data_type == "BLOB":
        return data_type
    else:
        if data_length:
            return f"{data_type}({data_length})"
        return data_type


# 泛微标准字段映射（仅作为fallback）
STANDARD_FIELD_DESCRIPTIONS = {
    "ID": "主键",
    "MAINID": "关联主表ID",
    "REQUESTID": "流程RequestID",
    "WORKFLOWID": "流程定义ID",
    "LASTNODEID": "最后节点ID",
    "CURRENTNODEID": "当前节点ID",
    "LASTNODETYPE": "最后节点类型",
    "CURRENTNODETYPE": "当前节点类型",
    "STATUS": "流程状态",
    "REQUESTNAME": "请求名称",
    "CREATER": "创建人",
    "CREATEDATE": "创建日期",
    "CREATETIME": "创建时间",
    "LASTOPERATOR": "最后操作人",
    "LASTOPERATEDATE": "最后操作日期",
    "LASTOPERATETIME": "最后操作时间",
    "FORMMODEID": "表单模式ID",
    "MODEDATACREATER": "创建人",
    "MODEDATACREATEDATE": "创建日期",
    "MODEDATACREATETIME": "创建时间",
    "MODEUUID": "模式UUID",
    "FORM_BIZ_ID": "表单业务ID",
    "MODEDATAMODIFIER": "修改人",
    "MODEDATAMODIFYDATETIME": "修改时间",
    "MODEDATACREATERTYPE": "创建人类型",
    "PASSEDGROUPS": "已通过节点数",
    "TOTALGROUPS": "总节点数",
}


def generate_markdown(schema: str, table_info: dict) -> str:
    """生成Markdown格式的数据字典."""
    lines = []
    table_name = table_info["table_name"]
    table_comment = table_info["table_comment"]
    columns = table_info["columns"]
    column_comments = table_info["column_comments"]
    field_types = table_info.get("field_types", {})

    # 标题
    lines.append(f"# {table_name} 数据字典")
    lines.append("")
    lines.append("## 表基本信息")
    lines.append("")
    lines.append("| 属性 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 表名 | {table_name} |")
    lines.append(f"| 描述 | {table_comment} |")
    lines.append(f"| 所属Schema | {schema.upper()} |")
    lines.append(f"| 表空间 | {table_info['tablespace']} |")
    lines.append("")

    # 字段列表
    lines.append("## 字段列表")
    lines.append("")
    lines.append("| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |")
    lines.append("|------|--------|----------|------|----------|----------|------|")

    for idx, col in enumerate(columns, 1):
        col_name = col[0]
        col_name_upper = col_name.upper()
        nullable = "YES" if col[5] == "Y" else "NO"
        data_type = format_data_type(col)
        comment = column_comments.get(col_name_upper, "")

        # 如果 comment 为空或 "None"，使用标准字段映射
        if not comment or comment == "None":
            comment = STANDARD_FIELD_DESCRIPTIONS.get(col_name_upper, "")

        # 获取字段类型信息
        ft = field_types.get(col_name_upper, {})
        field_type = ft.get("fieldhtmltype_name", "")
        browser_obj = ft.get("browser_table", "")

        # 如果字段没有从 workflow_billfield 获取到类型，使用默认推断
        if not field_type:
            # 根据字段名和类型推断字段类型
            if col_name_upper in ("ID", "MAINID", "REQUESTID", "FORMMODEID"):
                field_type = "系统字段"
            elif data_type.startswith("VARCHAR") or data_type.startswith("CHAR"):
                field_type = "单行文本"
            elif data_type.startswith("NUMBER") or data_type.startswith("INTEGER"):
                field_type = "数字"

        # 如果是浏览按钮但没有实体对象，显示类型名称
        if field_type == "浏览按钮" and not browser_obj:
            type_name = ft.get("type_name", "")
            if type_name:
                browser_obj = type_name

        lines.append(f"| {idx} | {col_name} | {data_type} | {nullable} | {field_type} | {browser_obj} | {comment} |")

    lines.append("")

    # 添加字段类型说明
    lines.append("## 字段类型说明")
    lines.append("")
    lines.append("| 类型值 | 说明 |")
    lines.append("|--------|------|")
    for k, v in FIELD_HTML_TYPE_MAP.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    return "\n".join(lines)


def parse_args():
    """解析命令行参数."""
    parser = argparse.ArgumentParser(
        description="获取Oracle数据字典并生成Markdown文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python get_data_dictionary.py                           # 生成所有可访问表的字典
  python get_data_dictionary.py -t UF_HTJGKST             # 指定单个表
  python get_data_dictionary.py -t UF_HTJGKST -s ECOLOGY  # 指定Schema和表
  python get_data_dictionary.py -t UF_HTJGKST,UF_HTJGKST_DT1  # 指定多个表
  python get_data_dictionary.py -o /path/to/output        # 指定输出目录
  python get_data_dictionary.py --list-tables             # 列出所有可访问的表
        """
    )
    parser.add_argument(
        "-t", "--tables",
        help="表名列表，逗号分隔，如: UF_HTJGKST,UF_HTJGKST_DT1"
    )
    parser.add_argument(
        "-s", "--schema",
        default=DEFAULT_SCHEMA,
        help=f"Schema名称 (默认: {DEFAULT_SCHEMA})"
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="列出所有可访问的表并退出"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="限制列出或处理的表数量 (默认: 50)"
    )
    return parser.parse_args()


def list_accessible_tables(conn, schema: str, limit: int = 50) -> list:
    """列出所有可访问的表."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT owner, table_name
        FROM all_tables
        WHERE owner = :owner
        ORDER BY table_name
    """, {"owner": schema.upper()})

    tables = []
    for row in cursor.fetchall():
        if len(tables) >= limit:
            break
        tables.append((row[0], row[1]))

    cursor.close()
    return tables


def main():
    """主函数."""
    args = parse_args()

    # 获取数据库配置
    db_config = get_database_config()
    params = db_config.to_oracledb_params()

    print(f"Connecting to database...")
    conn = oracledb.connect(
        user=params["user"],
        password=params["password"],
        dsn=params["dsn"],
    )
    print("Connected successfully!")

    # 如果指定了--list-tables，列出表并退出
    if args.list_tables:
        print(f"\nTables in schema {args.schema}:")
        print("-" * 50)
        tables = list_accessible_tables(conn, args.schema, args.limit)
        for owner, table_name in tables:
            print(f"  {owner}.{table_name}")
        print(f"\nTotal: {len(tables)} tables")
        conn.close()
        return

    # 确定要处理的表
    if args.tables:
        # 解析用户提供的表名列表
        table_names = [t.strip() for t in args.tables.split(",")]
        tables = [(args.schema, name) for name in table_names]
    else:
        # 默认处理所有可访问的表
        tables = list_accessible_tables(conn, args.schema, args.limit)

    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)

    # 处理每个表
    success_count = 0
    error_count = 0

    for schema, table_name in tables:
        print(f"\nFetching data for {schema}.{table_name}...")
        try:
            table_info = get_table_info(conn, schema, table_name)

            if table_info:
                markdown = generate_markdown(schema, table_info)

                # 保存文件
                output_file = os.path.join(args.output, f"{table_name}.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown)
                print(f"  Generated: {output_file}")
                print(f"  Table comment: {table_info['table_comment'] or '(none)'}")
                print(f"  Columns: {len(table_info['columns'])}")
                success_count += 1
            else:
                print(f"  Table {schema}.{table_name} not found!")
                error_count += 1
        except Exception as e:
            print(f"  Error: {e}")
            error_count += 1

    conn.close()
    print(f"\nDone! Success: {success_count}, Errors: {error_count}")


if __name__ == "__main__":
    main()
