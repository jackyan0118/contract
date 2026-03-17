"""填充模块常量定义."""

# 默认话术变量（如果YAML中没有配置，则返回null）
DEFAULT_SPEECH_VARIABLES = {}

# 字段推断映射 - 表头名称 -> 数据库字段
HEADER_TO_FIELD = {
    "序号": "序号",
    "物料编码": "WLDM",
    "SAP代码": "WLDM",
    "品名": "WLMS",
    "产品名称": "WLMS",
    "简称": "WLMS",
    "规格": "GG",
    "规格型号": "GG",
    "包装规格": "GG",
    "零售价": "LSJ",
    "供货价": "GHJY",
    "产品类别": "CPXF",
    "分类": "CPXF",
}
