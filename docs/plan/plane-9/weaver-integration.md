# 泛微OA集成方案

## 1. 业务场景

价格附件生成系统与泛微OA集成，实现：
- 泛微OA发起请求 → 生成价格附件 → 回写URL到OA表单

## 2. 核心需求

| 需求 | 说明 |
|------|------|
| 内网直连 | OA服务器直接调用API |
| 自动生成 | 根据报价单号自动生成价格附件 |
| 附件回写 | 生成后将文件URL回写到OA表单 |

## 3. OA接口配置

### 3.1 接口地址

| 配置项 | 值 |
|--------|-----|
| OA地址1 | 172.16.14.6:8080 |
| OA地址2 | 172.16.14.19:8080 |
| 接口路径 | /api/cube/restful/interface/saveOrUpdateModeData/SalesContract_PriceUrl_Update |

### 3.2 请求格式

**接口信息**
- HTTP方法：POST
- Content-Type：application/x-www-form-urlencoded
- 请求格式：key=datajson&value=jsonString

**header参数**

```json
{
  "systemid": "SalesContract_PriceUrl_Update",
  "currentDateTime": "20260319103000",
  "Md5": "MD5(systemid + password + currentDateTime)"
}
```

- MD5计算：`MD5("SalesContract_PriceUrl_Update" + "weaver2025" + "20260319103000")`
- password：weaver2025

**mainTable参数**

| 字段 | 说明 | 示例 |
|------|------|------|
| jgqdbh | 价格清单编号（主键） | 2026030006 |
| htjgfjlj | 合同价格附件链接 | https://example.com/xxx.pdf |
| htjgfj | 合同价格附件（数组） | 见下文 |

**htjgfj字段格式**
```json
"htjgfj": [
  {
    "name": "价格附件.pdf",
    "content": "https://example.com/downloads/xxx.pdf"
  }
]
```

**operationinfo参数**
```json
{
  "operationDate": "2026-03-19",
  "operator": "5288",
  "operationTime": "10:30:00"
}
```
- operator：OA系统用户ID

### 3.3 响应格式

```json
{
  "status": "1",  // 1=成功, 2=成功有异常, 3=数据异常, 4=系统异常
  "datajson": "..."
}
```

### 3.4 请求示例

```json
{
  "data": [{
    "operationinfo": {
      "operationDate": "2026-03-19",
      "operator": "5288",
      "operationTime": "10:30:00"
    },
    "mainTable": {
      "jgqdbh": "2026030006",
      "htjgfjlj": "https://example.com/downloads/price.pdf",
      "htjgfj": [{"name": "价格附件.pdf", "content": "https://example.com/downloads/price.pdf"}]
    },
    "detail1": [],
    "detail2": [],
    "detail3": [],
    "detail4": []
  }],
  "header": {
    "systemid": "SalesContract_PriceUrl_Update",
    "currentDateTime": "20260319103000",
    "Md5": "xxx"
  }
}
```

## 4. API接口设计

### 4.1 生成并回写接口

```
POST /api/v1/generate-with-oa
Authorization: Bearer {api_key}

{
  "wybs": "报价单号",
  "weaver": {
    "operator_id": "5288"
  }
}
```

### 4.2 OA配置接口

```
GET /api/v1/oa-config/status    # 获取OA连接状态
POST /api/v1/oa-config/validate # 测试OA连接
```

## 5. 实现方案

### 5.1 模块设计

```
src/
├── services/
│   └── weaver_service.py    # OA集成服务
├── api/routes/
│   └── weaver.py            # OA接口
└── config/
    └── settings.py          # 配置
```

### 5.2 服务实现要点

```python
class WeaverService:
    def __init__(self):
        self.hosts = ["172.16.14.6:8080", "172.16.14.19:8080"]
        self.system_id = "SalesContract_PriceUrl_Update"
        self.password = "weaver2025"

    def build_header(self) -> dict:
        """构建请求头"""
        current_datetime = time.strftime("%Y%m%d%H%M%S")
        md5_value = md5(self.system_id + self.password + current_datetime)
        return {
            "systemid": self.system_id,
            "currentDateTime": current_datetime,
            "Md5": md5_value
        }

    def build_main_table(self, jgqdbh: str, file_url: str, filename: str) -> dict:
        """构建主表数据"""
        return {
            "jgqdbh": jgqdbh,
            "htjgfjlj": file_url,
            "htjgfj": [{"name": filename, "content": file_url}]
        }

    async def write_attachment(self, jgqdbh: str, file_url: str, filename: str, operator_id: str) -> dict:
        """回写附件到OA"""
        # 1. 构建请求
        # 2. 调用OA接口
        # 3. 返回结果
```

## 6. 部署配置

```yaml
weaver:
  hosts:
    - "172.16.14.6:8080"
    - "172.16.14.19:8080"
  system_id: "SalesContract_PriceUrl_Update"
  password: "weaver2025"
  timeout: 30
  retry_count: 3
```

环境变量：
- WEAVER_SYSTEM_ID
- WEAVER_PASSWORD
- WEAVER_OPERATOR_ID

## 7. 接口清单

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/generate` | POST | 生成文档 |
| `/api/v1/generate-with-oa` | POST | 生成并回写OA |
| `/api/v1/oa-config/status` | GET | OA状态 |
| `/api/v1/oa-config/validate` | POST | 测试连接 |

## 8. 已确认事项

- ✅ 接口地址：172.16.14.6:8080 / 172.16.14.19:8080
- ✅ 接口路径：/api/cube/restful/interface/saveOrUpdateModeData/SalesContract_PriceUrl_Update
- ✅ 主键字段：jgqdbh
- ✅ 附件字段：htjgfj（数组格式）
- ✅ 存储方式：URL方式（已测试通过）
- ✅ 认证方式：MD5签名
- ✅ operator：OA用户ID

## 9. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-19 | 初始版本，接口测试通过 |
