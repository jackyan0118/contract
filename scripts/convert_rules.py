#!/usr/bin/env python3
"""规则文件转换脚本 - Excel → YAML"""

import os
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def load_db_brands() -> dict:
    """从数据库加载品牌映射 (ID -> 名称)."""
    import oracledb

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
    cursor.execute("SELECT ID, MS FROM ECOLOGY.UF_PP WHERE MS IS NOT NULL ORDER BY ID")
    rows = cursor.fetchall()

    brands = {}
    for row in rows:
        brand_id = row[0]
        brand_name = row[1]
        if brand_id and brand_name:
            brands[brand_id] = brand_name

    cursor.close()
    conn.close()

    return brands


def load_excel_rules(excel_path: str) -> tuple:
    """加载 Excel 规则文件.

    Returns:
        tuple: (全部数据, 有模板的数据)
    """
    df = pd.read_excel(excel_path, sheet_name="模板类型", header=1)

    # 向下填充产品细分和编码
    df["产品细分描述"] = df["产品细分描述"].ffill()
    df["产品细分编码"] = df["产品细分编码"].ffill()

    # 有模板的行
    df_valid = df[df["模板"].notna()].copy()

    return df, df_valid


def convert_to_yaml_structure(df_all: pd.DataFrame, df_templates: pd.DataFrame, db_brands: dict = None) -> dict:
    """转换为 YAML 结构."""
    templates = []
    product_categories = {}

    # 从 Excel 提取产品细分映射（编号 -> 名称）
    for _, row in df_templates.iterrows():
        product = row["产品细分描述"]
        product_code = row["产品细分编码"]
        if pd.notna(product_code) and pd.notna(product):
            product_categories[int(product_code)] = product

    # 从全部 Excel 数据提取品牌映射（编号 -> 名称）
    excel_brands = {}
    for _, row in df_all.iterrows():
        brand_code = row["品牌"]
        if pd.notna(brand_code):
            brand_code = int(brand_code)
            brand_name = db_brands.get(brand_code) if db_brands else None
            if brand_name and brand_code not in excel_brands:
                excel_brands[brand_code] = brand_name

    # 从全部 Excel 数据提取定价组映射（编号 -> 名称，包括非数字编号）
    excel_pricing_groups = {}
    for _, row in df_all.iterrows():
        code = row["定价组"]
        name = row["Unnamed: 5"]
        if pd.notna(code) and pd.notna(name):
            try:
                code = int(code)
                excel_pricing_groups[code] = name
            except (ValueError, TypeError):
                # 非数字编号如 A1, A2, A3, A4
                excel_pricing_groups[str(code)] = name

    # 从有模板的数据生成规则
    for _, row in df_templates.iterrows():
        product = row["产品细分描述"]
        product_code = row["产品细分编码"]

        # 获取产品细分编号
        if pd.notna(product_code):
            product_code = int(product_code)
        else:
            product_code = None

        # 定价组信息
        pricing_group_code = row["定价组"] if pd.notna(row["定价组"]) else None
        pricing_group_name = row["Unnamed: 5"] if pd.notna(row["Unnamed: 5"]) else None

        # 构建条件
        conditions = [{"产品细分编号": product_code, "产品细分": product}]

        if pricing_group_code:
            # 支持数字和字符串编号
            try:
                code_key = int(pricing_group_code)
            except (ValueError, TypeError):
                code_key = str(pricing_group_code)

            conditions[0]["定价组编号"] = code_key
            conditions[0]["定价组名称"] = pricing_group_name

        # 是否集采
        if pd.notna(row["是否集采"]) and row["是否集采"] not in ["空", ""]:
            jicai_map = {"是": 1, "否": 0}
            conditions[0]["是否集采"] = jicai_map.get(row["是否集采"])

        # 供货价类型
        if pd.notna(row["本年供货价类型"]):
            conditions[0]["供货价类型"] = row["本年供货价类型"]

        # 排序规则
        sort_rule = row["排序规则"] if pd.notna(row["排序规则"]) else None

        # 模板文件路径
        template_name = row["模板"]
        template_file = f"templates/{template_name}.docx"

        template_entry = {
            "id": template_name,
            "name": template_name,
            "file": template_file,
            "条件": conditions,
        }

        if sort_rule:
            template_entry["排序规则"] = sort_rule

        templates.append(template_entry)

    # 分离数字和非数字键
    numeric_groups = {k: v for k, v in excel_pricing_groups.items() if isinstance(k, int)}
    string_groups = {k: v for k, v in excel_pricing_groups.items() if isinstance(k, str)}

    # 排序：数字键和非数字键分开
    sorted_numeric = dict(sorted(numeric_groups.items()))
    sorted_string = dict(sorted(string_groups.items()))
    sorted_pricing = {**sorted_numeric, **sorted_string}

    # 构建 YAML 结构
    yaml_data = {
        "version": "1.0",
        "更新日期": "2026-03-09",
        "说明": "模板匹配规则配置文件 - 由 Excel 自动生成",
        "产品细分映射": dict(sorted(product_categories.items())),
        "定价组映射": sorted_pricing,
        "品牌映射": dict(sorted(excel_brands.items())) if excel_brands else {},
        "模板规则": templates,
    }

    return yaml_data


def generate_yaml_file(yaml_data: dict, output_path: str) -> None:
    """生成 YAML 文件."""
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            yaml_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )
    print(f"已生成 YAML 文件: {output_path}")


def main():
    base_dir = PROJECT_ROOT
    excel_path = base_dir / "docs" / "template" / "价格模板规则-更新2026306.xlsx"
    output_path = base_dir / "config" / "template_rules.yaml"

    if not excel_path.exists():
        print(f"错误: Excel 文件不存在: {excel_path}")
        sys.exit(1)

    print(f"读取 Excel: {excel_path}")

    # 加载数据：全部数据用于定价组，有模板的数据用于规则
    df_all, df_templates = load_excel_rules(str(excel_path))
    print(f"加载 {len(df_templates)} 条规则, {len(df_all)} 行数据")

    # 从数据库加载品牌映射
    print("从数据库加载品牌...")
    try:
        db_brands = load_db_brands()
        print(f"品牌数量: {len(db_brands)}")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        db_brands = {}

    # 转换
    yaml_data = convert_to_yaml_structure(df_all, df_templates, db_brands)

    # 生成文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_yaml_file(yaml_data, str(output_path))

    print(f"\n转换完成!")
    print(f"  - 模板数量: {len(yaml_data['模板规则'])}")
    print(f"  - 产品细分: {len(yaml_data['产品细分映射'])}")
    print(f"  - 定价组: {len(yaml_data['定价组映射'])}")
    print(f"  - 品牌: {len(yaml_data['品牌映射'])}")


if __name__ == "__main__":
    main()
