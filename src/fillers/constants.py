"""填充模块常量定义."""

# 字段映射配置
# 中文别名 -> (ID字段, 名称字段)
# 注意：数据库返回的字段是大写（如 CPXF, DJZMC），需要同时支持大小写
FIELD_MAPPING = {
    "产品细分": ("CPXF", None),
    "CPXF": ("CPXF", None),  # 产品细分ID
    "CPXF_BM": ("CPXF_BM", None),  # 产品细分BM编码
    "定价组": ("DJZ", "DJZMC"),
    "定价组名称": ("DJZ", "DJZMC"),
    "DJZMC": ("DJZ", "DJZMC"),  # 话术条件中使用的字段名
    "是否集采": ("SFJC", None),
    "SFJC": ("SFJC", None),  # 话术条件中使用的字段名
    "供货价类型": ("BNGHJLX", "BNGHJLXZ"),
    "BNGHJLX": ("BNGHJLX", "BNGHJLXZ"),  # 话术条件中使用的字段名
    "物料生成来源": ("LYXH", None),
}

# 默认话术变量
DEFAULT_SPEECH_VARIABLES = {
    "话术1": "85",
    "话术2": "70",
    "话术3": "25",
    "话术4": "50",
    "肝功扣率": "85",
    "通用扣率": "70",
    "北极星扣率": "25",
    "耗材扣率": "50",
}

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
