#!/usr/bin/env python3
"""
Word 模板生成测试脚本

使用正式数据库进行 Word 模板生成测试。
支持单个报价单和批量报价单的生成测试。

用法:
    python scripts/test_word_generation.py                    # 交互模式
    python scripts/test_word_generation.py --wybs WYBS20240301  # 指定报价单
    python scripts/test_word_generation.py --list              # 列出可用报价单
    python scripts/test_word_generation.py --batch WYBS001,WYBS002  # 批量生成
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 初始化 Thick Mode (需要 Oracle Instant Client)
ORACLE_INSTANT_CLIENT_PATH = os.environ.get("ORACLE_INSTANT_CLIENT", "/opt/oracle/instantclient")
try:
    import oracledb
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print(f"[INFO] Thick Mode 初始化成功: {ORACLE_INSTANT_CLIENT_PATH}")
except Exception as e:
    print(f"[WARN] Thick Mode 初始化失败: {e}")

# 预先初始化数据库连接池
from src.database.connection import get_connection_pool
pool = get_connection_pool()
pool.initialize()
print("[INFO] 数据库连接池初始化成功")

from src.config.settings import get_settings
from src.database.connection import get_connection_pool
from src.queries.quotation import get_quotation_by_wybs
from src.queries.quotation_detail import get_quotation_details
from src.matchers.template_matcher import TemplateMatcher
from src.generators.document_generator import DocumentGenerator
from src.services.rule_loader import RuleLoader
from src.utils.logger import get_logger

logger = get_logger("test_generation")


def print_header(title: str) -> None:
    """打印标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_quotation_info(data: dict) -> None:
    """打印报价单信息"""
    print("报价单信息:")
    print(f"  报价单号: {data.get('报价单号', 'N/A')}")
    print(f"  客户名称: {data.get('客户名称', 'N/A')}")
    print(f"  标题: {data.get('标题', 'N/A')}")
    print(f"  产品细分: {data.get('产品细分', 'N/A')}")
    print(f"  是否集采: {data.get('是否集采', 'N/A')}")
    print(f"  金额单位: {data.get('金额单位', 'N/A')}")


def print_detail_info(details: list) -> None:
    """打印明细信息"""
    print(f"\n明细信息 (共 {len(details)} 条):")
    if details:
        # 打印表头
        keys = list(details[0].keys())
        print(f"  {' | '.join(keys[:5])}")
        print(f"  {'-' * 60}")
        # 打印前5条
        for i, row in enumerate(details[:5]):
            values = [str(row.get(k, ''))[:15] for k in keys[:5]]
            print(f"  {' | '.join(values)}")
        if len(details) > 5:
            print(f"  ... 还有 {len(details) - 5} 条")


async def test_single_generation(wybs: str, output_dir: str = "output/test", templates: list = None) -> bool:
    """测试单个报价单生成

    Args:
        wybs: 报价单号
        output_dir: 输出目录
        templates: 模板编号或名称列表，如果为None则自动匹配所有适用模板

    Returns:
        是否成功
    """
    print_header(f"测试单个报价单生成: {wybs}")

    try:
        # 1. 查询报价单主数据
        print("1. 查询报价单数据...")
        quotation = get_quotation_by_wybs(wybs)

        if not quotation:
            print(f"❌ 报价单不存在: {wybs}")
            return False

        print_quotation_info(quotation)

        # 2. 查询明细数据
        print("\n2. 查询明细数据...")
        details = get_quotation_details(wybs)
        print(f"   查询到 {len(details)} 条明细数据")

        # 显示关键字段用于调试
        if details:
            lyxh_values = set([d.get('LYXH') for d in details])
            cpxf_values = set([d.get('CPXF') for d in details])
            print(f"   LYXH值: {lyxh_values}")
            print(f"   CPXF值: {cpxf_values}")

        if not details:
            print(f"❌ 报价单明细为空: {wybs}")
            return False

        print_detail_info(details)

        # 3. 模板匹配
        print("\n3. 匹配模板...")

        # 构建匹配数据
        # 注意: 实际业务中这些字段需要从报价单主表或其他数据源获取
        # 这里使用模拟数据进行测试
        print(f"   原始数据字段: {list(quotation.keys())}")

        rule_loader = RuleLoader()
        rules = rule_loader.load()

        # 如果指定了模板列表，使用指定的模板；否则自动匹配
        if templates:
            # 使用指定的模板列表
            matched_templates = []
            for t in templates:
                match_data = get_match_data_by_template(t)
                matcher = TemplateMatcher(rules)
                match_result = matcher.match(match_data)
                if match_result.success and match_result.templates:
                    matched_templates.append((match_result.templates[0], match_data))
            print(f"   指定模板: {templates}")
            print(f"   匹配到 {len(matched_templates)} 个模板")
        else:
            # 自动匹配所有适用模板 - 先获取报价单包含的产品细分
            cpxf_names = set()
            for d in details:
                cpxf_name = d.get('CPXF_NAME')
                if cpxf_name:
                    cpxf_names.add(cpxf_name)
            print(f"   报价单包含的产品细分: {cpxf_names}")

            # 遍历所有模板规则，匹配适用的
            matched_templates = []
            for rule in rules:
                conditions = rule.条件 if hasattr(rule, '条件') else []
                for cond in conditions:
                    cpxf = cond.产品细分编号 if hasattr(cond, '产品细分编号') else None
                    if cpxf:
                        # 检查报价单是否包含该产品细分
                        for cpxf_name in cpxf_names:
                            # 简单匹配逻辑：检查模板条件中的产品细分编号
                            matched = False
                            for name, code in get_all_cpxf_mapping().items():
                                if str(cpxf) == str(code) and name == cpxf_name:
                                    matched = True
                                    break
                            if matched:
                                # 找到匹配的模板
                                match_data = {
                                    "产品细分编号": cpxf,
                                    "产品细分": getattr(cond, '产品细分', ''),
                                    "定价组编号": getattr(cond, '定价组编号', None),
                                    "定价组名称": getattr(cond, '定价组名称', None),
                                    "是否集采": getattr(cond, '是否集采', '1'),
                                }
                                matched_templates.append((rule, match_data))
                                print(f"   ✅ 匹配: {rule.id} ({cpxf_name})")
                                break

            print(f"   自动匹配到 {len(matched_templates)} 个模板")

        if not matched_templates:
            print("❌ 未匹配到模板")
            return False

        # 生成所有匹配的模板
        generator = DocumentGenerator(
            template_dir="templates",
            config_dir="config/template_metadata/templates"
        )

        success_count = 0
        for matched_template, match_data in matched_templates:
            print(f"\n   处理模板: {matched_template.id} - {matched_template.name}")
            print(f"   匹配数据: {match_data}")

            # 将匹配数据合并到报价单数据中，用于话术匹配
            quotation.update(match_data)

            # 检查模板文件是否存在
            template_file = Path("templates") / matched_template.file
            if not template_file.exists():
                print(f"⚠️  模板文件不存在: {template_file}")
                print("   跳过此模板")
                continue

            # 4. 生成文档
            print("   正在生成...")
            generator = DocumentGenerator(
                template_dir="templates",
                config_dir="config/template_metadata/templates"
            )

            result = generator.generate(
                template=matched_template,
                quote_data=quotation,
                detail_data_list=details,
                output_dir=output_dir
            )

            if result.success:
                print(f"   ✅ 文档生成成功: {result.file_path}")
                success_count += 1
            else:
                print(f"   ❌ 文档生成失败: {result.error}")

        print(f"\n共成功生成 {success_count}/{len(matched_templates)} 个模板")
        return success_count > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        # 保存详细的错误日志
        import time
        error_file = f"output/test/error_{int(time.time())}.log"
        Path("output/test").mkdir(parents=True, exist_ok=True)
        with open(error_file, "w") as f:
            traceback.print_exc(file=f)
        print(f"   错误详情已保存到: {error_file}")
        return False


async def test_batch_generation(wybs_list: list, output_dir: str = "output/test") -> dict:
    """测试批量报价单生成

    Args:
        wybs_list: 报价单号列表
        output_dir: 输出目录

    Returns:
        生成结果统计
    """
    print_header(f"测试批量报价单生成: {len(wybs_list)} 个")

    results = {
        "total": len(wybs_list),
        "success": 0,
        "failed": 0,
        "details": []
    }

    for wybs in wybs_list:
        print(f"\n--- 处理: {wybs} ---")

        success = await test_single_generation(wybs, output_dir)

        if success:
            results["success"] += 1
            results["details"].append({"wybs": wybs, "status": "success"})
        else:
            results["failed"] += 1
            results["details"].append({"wybs": wybs, "status": "failed"})

    # 打印统计
    print_header("批量生成统计")
    print(f"总数量: {results['total']}")
    print(f"成功: {results['success']} ✅")
    print(f"失败: {results['failed']} ❌")

    return results


async def list_available_wybs(limit: int = 10) -> list:
    """列出可用的报价单号

    Args:
        limit: 返回数量限制

    Returns:
        报价单号列表
    """
    print(f"查询最近 {limit} 个报价单...")

    try:
        import oracledb
        # 初始化 Thick 模式
        ORACLE_INSTANT_CLIENT_PATH = os.environ.get("ORACLE_INSTANT_CLIENT", "/opt/oracle/instantclient")
        try:
            oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
        except Exception:
            pass

        # 直接连接（不使用连接池，因为需要 Thick 模式）
        settings = get_settings()
        dsn = settings.database.dsn.get_secret_value()
        # 解析 DSN
        dsn_str = dsn.replace("oracle://", "")

        conn = oracledb.connect(user='read_db', password='Skhb1189!', dsn='172.16.15.6:1521/oadata')
        cursor = conn.cursor()

        # 查询报价单 - 使用正确的表名和字段
        sql = f"SELECT WYBS, HTBH FROM ecology.UF_HTJGKST WHERE WYBS IS NOT NULL AND ROWNUM <= {limit} ORDER BY MODEDATACREATEDATE DESC"
        cursor.execute(sql)
        rows = cursor.fetchall()

        wybs_list = []
        for row in rows:
            wybs_list.append({
                "wybs": row[0],
                "title": row[1] or "N/A"
            })

        conn.close()
        return wybs_list

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_match_data_by_template(template: str) -> dict:
    """根据模板编号或名称返回匹配数据

    Args:
        template: 模板编号或名称，如 "1" 或 "酶免试剂"

    Returns:
        匹配数据字典
    """
    # 模板匹配数据映射
    template_map = {
        # 模板1：酶免和胶体金
        "1": {
            "产品细分编号": "11",
            "产品细分": "酶免试剂",
            "定价组编号": None,
            "定价组名称": None,
            "是否集采": "1",
        },
        "酶免": {
            "产品细分编号": "11",
            "产品细分": "酶免试剂",
            "定价组编号": None,
            "定价组名称": None,
            "是否集采": "1",
        },
        # 模板2：通用生化产品价格模版
        "2": {
            "产品细分编号": "21",
            "产品细分": "通用生化试剂",
            "定价组编号": "12",
            "定价组名称": "通用生化-非集采项目",
            "是否集采": "1",
        },
        "通用生化": {
            "产品细分编号": "21",
            "产品细分": "通用生化试剂",
            "定价组编号": "12",
            "定价组名称": "通用生化-非集采项目",
            "是否集采": "1",
        },
    }

    # 尝试精确匹配
    if template in template_map:
        return template_map[template]

    # 尝试模糊匹配
    for key, value in template_map.items():
        if key in template or template in key:
            return value

    # 默认返回模板2
    print(f"⚠️  未找到模板 '{template}'，使用默认模板2")
    return template_map["2"]


def get_all_cpxf_mapping() -> dict:
    """获取所有产品细分的BM编码映射

    Returns:
        产品细分名称到BM编码的映射
    """
    return {
        "酶免试剂": "11",
        "胶体金试剂": "41",
        "通用生化试剂": "21",
        "卓越生化试剂": "22",
        "化学发光试剂": "12",
        "北极星发光试剂": "14",
        "日立008试剂": "23",
        "北极星生化试剂": "24",
        "第三方试剂": "102",
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Word 模板生成测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/test_word_generation.py --list
  python scripts/test_word_generation.py --wybs WYBS20240301001
  python scripts/test_word_generation.py --batch WYBS001,WYBS002
        """
    )

    parser.add_argument(
        "--wybs", "-w",
        type=str,
        help="报价单号"
    )

    parser.add_argument(
        "--batch", "-b",
        type=str,
        help="批量报价单号，用逗号分隔"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出可用的报价单"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output/test",
        help="输出目录 (默认: output/test)"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="列出报价单的数量 (默认: 10)"
    )

    parser.add_argument(
        "--template", "-t",
        type=str,
        default=None,
        help="模板编号或名称，支持逗号分隔多个模板 (默认: 自动匹配所有适用模板)"
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="生成所有匹配的模板"
    )

    args = parser.parse_args()

    # 确保输出目录存在
    Path(args.output).mkdir(parents=True, exist_ok=True)

    # 加载配置
    print("加载配置...")
    settings = get_settings()
    print(f"数据库: {settings.database.dsn.get_secret_value()[:30]}...")
    print(f"模板目录: {settings.template.path}")

    # 执行操作
    if args.list:
        # 列出可用报价单
        wybs_list = asyncio.run(list_available_wybs(args.limit))

        print_header(f"可用报价单 (共 {len(wybs_list)} 个)")
        for i, item in enumerate(wybs_list, 1):
            print(f"{i}. {item['wybs']} - {item['title']}")

    elif args.wybs:
        # 单个生成
        # 解析模板参数
        template_list = None
        if args.template:
            # 支持逗号分隔的多个模板
            template_list = [t.strip() for t in args.template.split(",")]
        elif args.all:
            # 自动匹配所有适用模板
            template_list = None  # None表示自动匹配

        success = asyncio.run(test_single_generation(args.wybs, args.output, template_list))
        sys.exit(0 if success else 1)

    elif args.batch:
        # 批量生成
        wybs_list = [w.strip() for w in args.batch.split(",")]
        results = asyncio.run(test_batch_generation(wybs_list, args.output))

        # 返回退出码
        sys.exit(0 if results["failed"] == 0 else 1)

    else:
        # 交互模式
        print("交互模式")
        print("\n请选择操作:")
        print("1. 列出可用报价单")
        print("2. 测试单个生成")
        print("3. 测试批量生成")
        print("0. 退出")

        choice = input("\n请输入选项: ").strip()

        if choice == "1":
            wybs_list = asyncio.run(list_available_wybs())
            print_header(f"可用报价单 (共 {len(wybs_list)} 个)")
            for i, item in enumerate(wybs_list, 1):
                print(f"{i}. {item['wybs']} - {item['title']}")

        elif choice == "2":
            wybs = input("请输入报价单号: ").strip()
            if wybs:
                asyncio.run(test_single_generation(wybs, args.output, args.template))

        elif choice == "3":
            wybs_input = input("请输入报价单号 (用逗号分隔): ").strip()
            if wybs_input:
                wybs_list = [w.strip() for w in wybs_input.split(",")]
                asyncio.run(test_batch_generation(wybs_list, args.output))

        elif choice == "0":
            print("退出")
        else:
            print("无效选项")


if __name__ == "__main__":
    main()
