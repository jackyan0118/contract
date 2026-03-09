"""数据转换模块.

将 Oracle 数据库查询结果转换为系统内部模型。
"""

from .data_transformer import (
    DataTransformer,
    FieldMappingConfig,
    get_transformer,
    transform_quotation,
)

__all__ = [
    "DataTransformer",
    "FieldMappingConfig",
    "get_transformer",
    "transform_quotation",
]
