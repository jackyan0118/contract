#!/usr/bin/env python3
"""
泛微OA接口测试脚本
用于验证价格附件URL回写接口是否可以正常调用
"""

import requests
import json
import hashlib
import time
from typing import Optional

# ==================== 配置项 ====================
# OA服务器地址
OA_HOST = "172.16.14.6"
OA_PORT = "8080"
# 备用OA服务器地址
OA_HOST_BACKUP = "172.16.14.19"

# 接口路径
API_PATH = "/api/cube/restful/interface/saveOrUpdateModeData/SalesContract_PriceUrl_Update"

# 系统标识
SYSTEM_ID = "SalesContract_PriceUrl_Update"

# MD5签名密码（由OA提供）
MD5_PASSWORD = "weaver2025"

# 测试数据
TEST_RECORD_ID = "2026030006"  # OA记录ID（主键）
TEST_OPERATOR_ID = "5288"       # 操作人ID

# 价格附件URL（替换为实际生成的URL）
TEST_PRICE_URL = "https://biaoxun.skhb.com:7990/xxx.pdf"

# Cookie认证（可选）
OA_COOKIE = None


def generate_md5(data: str) -> str:
    """生成MD5值"""
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def build_request_body(record_id: str, price_url: str, operator_id: str) -> dict:
    """构建请求体"""
    # header 使用: yyyyMMddHHmmss
    current_datetime = time.strftime("%Y%m%d%H%M%S")
    # operationinfo 使用: yyyy-MM-dd 和 HH:mm:ss
    operation_date = time.strftime("%Y-%m-%d")
    operation_time = time.strftime("%H:%M:%S")

    # 根据文档：Md5 = MD5(systemid + password + currentDateTime)
    md5_string = SYSTEM_ID + MD5_PASSWORD + current_datetime
    md5_value = generate_md5(md5_string)

    # 构建header
    header = {
        "systemid": SYSTEM_ID,
        "currentDateTime": current_datetime,
        "Md5": md5_value
    }

    # 构建mainTable (V2版本)
    # jgqdbh: 价格清单编号（主键）
    # htjgfjlj: 合同价格附件链接
    # htjgfj: 合同价格附件（数组）
    main_table = {
        "jgqdbh": record_id,  # V2版本主键
        "htjgfjlj": price_url,
        "htjgfj": [
            {
                "name": "价格附件.pdf",
                "content": "https://biaoxun.skhb.com:7990/operations-management-center/434154724_1/f13693ac-c763-11ef-b691-0fafe4eb4b68.pdf"
            }
        ]
    }

    # 构建operationinfo
    operation_info = {
        "operationDate": operation_date,
        "operator": operator_id,
        "operationTime": operation_time
    }

    # 构建完整请求
    request_data = {
        "data": [{
            "operationinfo": operation_info,
            "mainTable": main_table,
            "detail1": [],
            "detail2": [],
            "detail3": [],
            "detail4": []
        }],
        "header": header
    }

    return request_data


def call_weaver_api(
    host: str,
    port: str,
    datajson: dict,
    cookie: Optional[str] = None
) -> dict:
    """调用泛微OA接口"""
    url = f"http://{host}:{port}{API_PATH}"

    # 将请求体转为JSON字符串
    json_string = json.dumps(datajson, ensure_ascii=False)

    # 构建表单数据
    form_data = {
        "datajson": json_string
    }

    # 设置请求头
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
    }

    if cookie:
        headers["Cookie"] = cookie

    try:
        print(f"\n{'='*60}")
        print(f"请求URL: {url}")
        print(f"请求头: {headers}")
        print(f"请求体: {json_string[:200]}...")
        print(f"{'='*60}\n")

        response = requests.post(
            url,
            data=form_data,
            headers=headers,
            timeout=30
        )

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        try:
            return response.json()
        except:
            return {"raw_response": response.text}

    except requests.exceptions.Timeout:
        return {"error": "请求超时"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"连接失败: {str(e)}"}
    except Exception as e:
        return {"error": f"未知错误: {str(e)}"}


def test_connection(host: str = OA_HOST, port: str = OA_PORT):
    """测试OA接口连通性"""
    print(f"\n{'#'*60}")
    print(f"# 测试泛微OA接口")
    print(f"# 目标: {host}:{port}")
    print(f"{'#'*60}")

    # 构建测试数据
    request_body = build_request_body(
        record_id=TEST_RECORD_ID,
        price_url=TEST_PRICE_URL,
        operator_id=TEST_OPERATOR_ID
    )

    # 调用接口
    result = call_weaver_api(host, port, request_body, OA_COOKIE)

    # 解析结果
    print(f"\n{'='*60}")
    print("结果分析:")
    print(f"{'='*60}")

    if "error" in result:
        print(f"❌ 调用失败: {result['error']}")
        return False

    # 尝试解析响应
    response_text = result.get("raw_response", "")

    # 检查status字段
    if "status" in response_text:
        if '"status":"1"' in response_text or '"status":1' in response_text:
            print("✅ 接口调用成功 (status=1)")
            return True
        elif '"status":"2"' in response_text or '"status":2' in response_text:
            print("⚠️ 接口调用成功但有异常 (status=2)")
            return True
        elif '"status":"3"' in response_text or '"status":3' in response_text:
            print("❌ 数据异常 (status=3)")
            return False
        elif '"status":"4"' in response_text or '"status":4' in response_text:
            print("❌ 系统异常 (status=4)")
            return False

    print(f"响应: {response_text[:500]}")
    return True


def test_with_backup():
    """使用备用服务器测试"""
    print("\n" + "="*60)
    print("尝试主服务器...")
    print("="*60)

    success = test_connection(OA_HOST, OA_PORT)

    if not success:
        print("\n主服务器连接失败，尝试备用服务器...")
        print("="*60)
        success = test_connection(OA_HOST_BACKUP, OA_PORT)

    return success


if __name__ == "__main__":
    print("""
    ==================================================
    泛微OA价格附件URL回写接口测试
    ==================================================

    配置信息:
    - 主服务器: {0}:{1}
    - 备用服务器: {2}:{1}
    - 接口路径: {3}

    测试数据:
    - 记录ID: {4}
    - 价格URL: {5}
    - 操作人ID: {6}

    ==================================================
    """.format(
        OA_HOST, OA_PORT, OA_HOST_BACKUP, API_PATH,
        TEST_RECORD_ID, TEST_PRICE_URL, TEST_OPERATOR_ID
    ))

    # 执行测试
    success = test_with_backup()

    if success:
        print("\n✅ 测试完成")
    else:
        print("\n❌ 测试失败，请检查配置")
