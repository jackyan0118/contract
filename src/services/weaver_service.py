"""
泛微OA集成服务
"""

import hashlib
import time
from typing import Optional

import httpx

from src.config.settings import WeaverSettings


class WeaverService:
    """泛微OA集成服务"""

    def __init__(self, settings: WeaverSettings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """获取HTTP客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.settings.timeout,
                limits=httpx.Limits(max_connections=10)
            )
        return self._client

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def build_header(self) -> dict:
        """构建请求头"""
        current_datetime = time.strftime("%Y%m%d%H%M%S")
        md5_string = self.settings.system_id + self.settings.password + current_datetime
        md5_value = hashlib.md5(md5_string.encode('utf-8')).hexdigest()

        return {
            "systemid": self.settings.system_id,
            "currentDateTime": current_datetime,
            "Md5": md5_value
        }

    def build_main_table(self, jgqdbh: str, file_url: str, filename: str) -> dict:
        """构建主表数据"""
        return {
            "jgqdbh": jgqdbh,
            "htjgfjlj": file_url,
            "htjgfj": [
                {
                    "name": filename,
                    "content": file_url
                }
            ]
        }

    def build_operation_info(self, operator_id: str) -> dict:
        """构建操作信息"""
        return {
            "operationDate": time.strftime("%Y-%m-%d"),
            "operator": operator_id,
            "operationTime": time.strftime("%H:%M:%S")
        }

    def build_request_body(
        self,
        jgqdbh: str,
        file_url: str,
        filename: str,
        operator_id: str
    ) -> dict:
        """构建完整请求体"""
        return {
            "data": [{
                "operationinfo": self.build_operation_info(operator_id),
                "mainTable": self.build_main_table(jgqdbh, file_url, filename),
                "detail1": [],
                "detail2": [],
                "detail3": [],
                "detail4": []
            }],
            "header": self.build_header()
        }

    async def write_attachment(
        self,
        jgqdbh: str,
        file_url: str,
        filename: str,
        operator_id: Optional[str] = None
    ) -> dict:
        """
        回写附件到OA表单

        Args:
            jgqdbh: 价格清单编号
            file_url: 文件URL地址
            filename: 文件名
            operator_id: 操作人ID，默认使用配置中的operator_id

        Returns:
            dict: OA接口响应
        """
        if operator_id is None:
            operator_id = self.settings.operator_id

        # 构建请求体
        request_body = self.build_request_body(jgqdbh, file_url, filename, operator_id)

        # 获取客户端
        client = await self.get_client()

        # 尝试多个服务器
        last_error = None
        for host in self.settings.hosts:
            try:
                url = f"http://{host}/api/cube/restful/interface/saveOrUpdateModeData/SalesContract_PriceUrl_Update"

                response = await client.post(
                    url,
                    data={"datajson": str(request_body)},
                    headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
                )

                result = response.json()

                # 处理响应格式
                if isinstance(result, str):
                    # 如果返回的是字符串，尝试解析
                    import json
                    try:
                        result = json.loads(result)
                    except:
                        return {
                            "success": False,
                            "status": "4",
                            "message": f"OA响应格式错误: {result[:100]}"
                        }

                status = result.get("status")

                if status == "1":
                    # 解析datajson字段获取billid
                    billid = None
                    datajson_str = result.get("datajson", "")
                    if datajson_str:
                        import json
                        try:
                            datajson = json.loads(datajson_str)
                            if isinstance(datajson, dict):
                                data_list = datajson.get("data", [])
                                if data_list:
                                    billid = data_list[0].get("billid")
                        except:
                            pass

                    return {
                        "success": True,
                        "status": status,
                        "billid": billid,
                        "message": "回写成功"
                    }
                else:
                    return {
                        "success": False,
                        "status": status,
                        "message": f"OA返回异常状态: {status}"
                    }

            except Exception as e:
                last_error = e
                continue

        return {
            "success": False,
            "status": "4",
            "message": f"所有OA服务器均失败: {last_error}"
        }

    async def test_connection(self) -> dict:
        """测试OA连接"""
        client = await self.get_client()

        for host in self.settings.hosts:
            try:
                url = f"http://{host}/api/cube/restful/interface/saveOrUpdateModeData/SalesContract_PriceUrl_Update"

                # 发送空请求测试连接
                response = await client.post(
                    url,
                    data={"datajson": "{}"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "host": host,
                        "message": "连接成功"
                    }

            except Exception as e:
                continue

        return {
            "success": False,
            "message": "所有OA服务器均无法连接"
        }
