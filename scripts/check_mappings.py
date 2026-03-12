#!/usr/bin/env python3
"""检查 YAML 映射与数据库一致性 - 以 YAML 为基础."""

import os
import sys
from datetime import datetime
from pathlib import Path

import oracledb
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def load_db_data():
    """从数据库加载产品细分和定价组数据."""
    oracledb.init_oracle_client(lib_dir='/opt/oracle/instantclient')

    from src.database.config import get_database_config

    db_config = get_database_config()
    params = db_config.to_oracledb_params()

    conn = oracledb.connect(
        user=params.get("user"),
        password=params.get("password"),
        dsn=params.get("dsn"),
    )

    cursor = conn.cursor()

    # 产品细分: BM(编码) -> CPXF(名称)
    cursor.execute("SELECT BM, CPXF FROM ECOLOGY.UF_CPXF WHERE BM IS NOT NULL AND CPXF IS NOT NULL")
    product_categories = {}
    for row in cursor.fetchall():
        code, name = row
        if code and name:
            try:
                product_categories[int(code)] = name
            except (ValueError, TypeError):
                pass

    # 定价组: DJZBM(编号) -> DJZMC(名称)，从UF_HTDJZPPB表获取
    cursor.execute("SELECT ID, DJZBM, DJZMC FROM ECOLOGY.UF_HTDJZPPB WHERE DJZBM IS NOT NULL AND DJZMC IS NOT NULL")
    pricing_groups = {}
    pricing_group_id_map = {}  # 编号 -> ID
    for row in cursor.fetchall():
        pg_id, code, name = row
        if code and name:
            try:
                pricing_groups[int(code)] = name.strip()
                pricing_group_id_map[int(code)] = pg_id
            except (ValueError, TypeError):
                pricing_groups[str(code)] = name.strip()
                pricing_group_id_map[str(code)] = pg_id

    # 供货价类型: 定价组编号(CPZBH) -> [供货价类型名称列表]
    # 注意：UF_YXZXHTGHJLXBN表的CPZAN字段存储的是UF_CPZWH.ID，需要转换为CPZBH
    # 包含SFQY=0和SFQY=1的记录
    # 使用GHJLX（名称）进行匹配
    # 先建立ID(字符串)到CPZBH的映射
    cursor.execute("SELECT ID, CPZBH FROM ECOLOGY.UF_CPZWH WHERE ID IS NOT NULL")
    id_to_bh = {}
    for row in cursor.fetchall():
        pg_id, pg_bh = row
        id_to_bh[str(pg_id)] = pg_bh

    # 查询供货价类型（包含SFQY=0和SFQY=1），使用名称匹配
    cursor.execute("""
        SELECT DISTINCT CPZAN, GHJLX
        FROM ECOLOGY.UF_YXZXHTGHJLXBN
        WHERE CPZAN IS NOT NULL AND GHJLX IS NOT NULL AND SFQY IN (0, 1)
    """)
    pricing_type_map = {}  # 定价组编号(CPZBH) -> 供货价类型名称集合
    for row in cursor.fetchall():
        cpz_id, ghlx_name = row
        # 将CPZAN(ID)转换为CPZBH
        pg_bh = id_to_bh.get(str(cpz_id))
        if pg_bh is None:
            continue

        try:
            pg_bh = int(pg_bh)
        except (ValueError, TypeError):
            pg_bh = str(pg_bh)

        if pg_bh not in pricing_type_map:
            pricing_type_map[pg_bh] = set()
        pricing_type_map[pg_bh].add(ghlx_name)

    # 品牌: DM(代码) -> MS(名称)
    cursor.execute("SELECT DM, MS FROM ECOLOGY.UF_PP WHERE SFQY = 0")
    brand_mapping = {}
    for row in cursor.fetchall():
        code, name = row
        if code and name:
            try:
                brand_mapping[int(code)] = name
            except (ValueError, TypeError):
                pass

    cursor.close()
    conn.close()

    return product_categories, pricing_groups, pricing_group_id_map, pricing_type_map, brand_mapping


def check_mappings(yaml_data: dict, db_products: dict, db_pricing: dict, db_pricing_types: dict, db_brands: dict):
    """检查映射一致性 - 以 YAML 为基础."""
    results = []
    results.append("# 映射检查结果")
    results.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("")
    results.append("## 产品细分映射检查 (以 YAML 为基础)")
    results.append("")

    yaml_products = yaml_data.get("产品细分映射", {})

    product_issues = []
    for code, name in sorted(yaml_products.items()):
        db_name = db_products.get(code)
        if db_name is None:
            product_issues.append(f"- 编号 {code}: YAML=\"{name}\" [数据库中不存在]")
        elif db_name != name:
            product_issues.append(f"- 编号 {code}: YAML=\"{name}\" vs 数据库=\"{db_name}\" [不一致]")

    if product_issues:
        for item in product_issues:
            results.append(item)
    else:
        results.append("✓ 全部一致")
    results.append("")

    results.append("## 定价组映射检查 (以 YAML 为基础)")
    results.append("")

    yaml_pricing = yaml_data.get("定价组映射", {})

    pricing_issues = []
    for code, name in sorted(yaml_pricing.items(), key=lambda x: str(x[0])):
        db_name = db_pricing.get(code)
        if db_name is None:
            pricing_issues.append(f"- 编号 {code}: YAML=\"{name}\" [数据库中不存在]")
        elif db_name != name:
            pricing_issues.append(f"- 编号 {code}: YAML=\"{name}\" vs 数据库=\"{db_name}\" [不一致]")

    if pricing_issues:
        for item in pricing_issues:
            results.append(item)
    else:
        results.append("✓ 全部一致")
    results.append("")

    # 供货价类型检查
    results.append("## 供货价类型检查 (以 YAML 为基础)")
    results.append("")

    type_issues = []
    templates = yaml_data.get("模板规则", [])

    for template in templates:
        conditions = template.get("条件", [])
        for cond in conditions:
            pg_code = cond.get("定价组编号")
            ghlx_name = cond.get("供货价类型")

            if pg_code and ghlx_name:
                # 将YAML中的字符串编号转换为int，以便与数据库映射表匹配
                try:
                    pg_code_int = int(pg_code)
                except (ValueError, TypeError):
                    pg_code_int = pg_code

                # 直接使用名称匹配
                db_types = db_pricing_types.get(pg_code_int, set())
                if ghlx_name not in db_types:
                    type_issues.append(
                        f"- 模板 \"{template['id']}\": 定价组 {pg_code} "
                        f"供货价类型 \"{ghlx_name}\" [数据库中不存在]"
                    )

    if type_issues:
        for item in type_issues:
            results.append(item)
    else:
        results.append("✓ 全部一致")
    results.append("")

    # 品牌检查
    results.append("## 品牌映射检查 (以 YAML 为基础)")
    results.append("")

    yaml_brands = yaml_data.get("品牌映射", {})

    brand_issues = []
    for code, name in sorted(yaml_brands.items()):
        db_name = db_brands.get(code)
        if db_name is None:
            brand_issues.append(f"- 编号 {code}: YAML=\"{name}\" [数据库中不存在]")
        elif db_name != name:
            brand_issues.append(f"- 编号 {code}: YAML=\"{name}\" vs 数据库=\"{db_name}\" [不一致]")

    if brand_issues:
        for item in brand_issues:
            results.append(item)
    else:
        results.append("✓ 全部一致")
    results.append("")

    # 统计
    results.append("## 统计")
    results.append("")
    results.append(f"- YAML 产品细分: {len(yaml_products)} 个")
    results.append(f"- YAML 定价组: {len(yaml_pricing)} 个")
    results.append(f"- YAML 品牌: {len(yaml_brands)} 个")
    results.append(f"- 模板规则: {len(templates)} 个")
    results.append(f"- 产品细分问题: {len(product_issues)} 个")
    results.append(f"- 定价组问题: {len(pricing_issues)} 个")
    results.append(f"- 品牌问题: {len(brand_issues)} 个")
    results.append(f"- 供货价类型问题: {len(type_issues)} 个")
    results.append("")

    total_issues = len(product_issues) + len(pricing_issues) + len(brand_issues) + len(type_issues)
    results.append(f"**总问题数: {total_issues} 个**")

    return "\n".join(results), total_issues


def main():
    yaml_path = PROJECT_ROOT / "config" / "template_rules.yaml"
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)

    # 加载 YAML
    print(f"读取 YAML: {yaml_path}")
    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    # 从数据库加载数据
    print("从数据库加载数据...")
    try:
        db_products, db_pricing, db_pg_id_map, db_pricing_types, db_brands = load_db_data()
        print(f"  产品细分: {len(db_products)} 个")
        print(f"  定价组: {len(db_pricing)} 个")
        print(f"  定价组供货价类型: {len(db_pricing_types)} 个")
        print(f"  品牌: {len(db_brands)} 个")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return 1

    # 检查
    print("检查映射...")
    report, issue_count = check_mappings(yaml_data, db_products, db_pricing, db_pricing_types, db_brands)

    # 保存结果
    output_file = output_dir / "mapping_check_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"检查完成，发现 {issue_count} 个问题")
    print(f"报告已保存: {output_file}")

    return 0 if issue_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
