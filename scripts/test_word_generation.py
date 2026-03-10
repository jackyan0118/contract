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
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import get_settings
from src.database.connection import get_connection_pool
from src.queries.quotation import get_quotation_by_wybs
from src.queries.quotation_detail import get_quotation_details
from src.matchers.template_matcher import TemplateMatcher
from src.generators.document_generator import DocumentGenerator
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


async def test_single_generation(wybs: str, output_dir: str = "output/test") -> bool:
    """测试单个报价单生成

    Args:
        wybs: 报价单号
        output_dir: 输出目录

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

        if not details:
            print(f"❌ 报价单明细为空: {wybs}")
            return False

        print_detail_info(details)

        # 3. 模板匹配
        print("\n3. 匹配模板...")
        matcher = TemplateMatcher()
        matched_template = matcher.match(quotation)

        if not matched_template:
            print("❌ 未匹配到模板")
            return False

        print(f"✅ 匹配到模板: {matched_template.id} - {matched_template.name}")
        print(f"   模板文件: {matched_template.file}")

        # 4. 生成文档
        print("\n4. 生成文档...")
        generator = DocumentGenerator(output_dir=output_dir)

        result = generator.generate(
            template=matched_template,
            quotation_data=quotation,
            detail_data=details
        )

        if result.success:
            print(f"✅ 文档生成成功!")
            print(f"   文件路径: {result.file_path}")
            print(f"   模板ID: {result.template_id}")
            return True
        else:
            print(f"❌ 文档生成失败: {result.error}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
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
        pool = get_connection_pool()
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                # 查询最近创建的报价单
                sql = """
                    SELECT wybs, btitle, customerid, createdate
                    FROM uf_htjgk
                    WHERE btitle IS NOT NULL
                    ORDER BY createdate DESC
                    FETCH FIRST :1 ROWS ONLY
                """
                await cursor.execute(sql, [limit])
                rows = await cursor.fetchall()

                wybs_list = []
                for row in rows:
                    wybs_list.append({
                        "wybs": row[0],
                        "title": row[1],
                        "customerid": row[2],
                        "createdate": row[3]
                    })

                return wybs_list

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return []


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
            print(f"{i}. {item['wybs']} - {item['title']} ({item['createdate']})")

    elif args.wybs:
        # 单个生成
        success = asyncio.run(test_single_generation(args.wybs, args.output))
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
                asyncio.run(test_single_generation(wybs, args.output))

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
