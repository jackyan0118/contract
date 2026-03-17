"""数据转换器模块.

将 Oracle 数据库查询结果转换为系统内部模型。
"""

from __future__ import annotations

import os
import threading
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import yaml

from src.exceptions import ConfigException
from src.models import Quotation, QuotationDetail, QuotationItem
from src.queries import get_quotation_by_wybs, get_quotation_details
from src.utils.logger import get_logger

logger = get_logger("transformers.data_transformer")

# 默认配置文件路径
DEFAULT_MAPPING_FILE = "config/field_mapping.yaml"

# 价格字段精度
PRICE_DECIMAL_PLACES = 2


class FieldMappingConfig:
    """字段映射配置类.

    从 YAML 文件加载字段映射配置。
    """

    def __init__(self, config_path: str | None = None):
        """初始化字段映射配置.

        Args:
            config_path: 配置文件路径，默认使用 config/field_mapping.yaml
        """
        self._config_path = config_path or DEFAULT_MAPPING_FILE
        self._mapping: dict[str, dict[str, str]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载 YAML 配置文件."""
        config_file = Path(self._config_path)

        if not config_file.exists():
            # 尝试从项目根目录查找
            project_root = Path.cwd()
            config_file = project_root / self._config_path

        if not config_file.exists():
            raise ConfigException(
                message=f"字段映射配置文件不存在: {self._config_path}",
                error_code="CONFIG_NOT_FOUND",
                detail={"config_path": self._config_path},
            )

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 加载主表映射
            self._mapping["quotation"] = config.get("quotation", {}).get("mapping", {})

            # 加载明细表映射
            self._mapping["quotation_detail"] = config.get(
                "quotation_detail", {}
            ).get("mapping", {})

            logger.info(
                "字段映射配置加载成功",
                extra={
                    "quotation_fields": len(self._mapping["quotation"]),
                    "quotation_detail_fields": len(self._mapping["quotation_detail"]),
                },
            )

        except yaml.YAMLError as e:
            raise ConfigException(
                message=f"字段映射配置文件解析失败: {e}",
                error_code="CONFIG_VALIDATION_ERROR",
                detail={"config_path": self._config_path, "error": str(e)},
            ) from e
        except Exception as e:
            raise ConfigException(
                message=f"加载字段映射配置失败: {e}",
                error_code="CONFIG_ERROR",
                detail={"config_path": self._config_path, "error": str(e)},
            ) from e

    def get_quotation_mapping(self) -> dict[str, str]:
        """获取报价单主表字段映射.

        Returns:
            Oracle 字段名 -> 系统内部字段名的映射字典
        """
        return self._mapping.get("quotation", {})

    def get_quotation_detail_mapping(self) -> dict[str, str]:
        """获取报价单明细表字段映射.

        Returns:
            Oracle 字段名 -> 系统内部字段名的映射字典
        """
        return self._mapping.get("quotation_detail", {})


class DataTransformer:
    """数据转换器.

    将 Oracle 数据库查询结果（字典列表）转换为系统内部模型。
    支持字段名映射和数据类型转换。
    """

    # 价格字段列表
    PRICE_FIELDS = frozenset([
        "lsj",       # 零售价
        "bzjxj",     # 标准价(升级价)
        "ghjy",      # 供货价
        "zxkhkpdjy", # 执行客户开单价
        "jsj",       # 结算价
        "klbfb",     # 扣率百分比
        "yhfdbfb",   # 优惠幅度百分比
        # 扩展价格字段（新增）
        "xzxjg",     # 现执行价格
        "tpj",       # 突破价
        "sczdjjc",   # 市场指导价_集采
        "sczdjfjc",  # 市场指导价_非集采
        "bzjxjjc",   # 标准经销价_集采
        "bzjxjfjc",  # 标准经销价_非集采
        "jczbj",     # 集采中标价
        "jcjxj",     # 集采经销价
        "jgjcy",     # 价格间差异
    ])

    # 整数字段列表
    INTEGER_FIELDS = frozenset([
        "id",        # 主键
        "mainid",    # 关联主表ID
        "lyxh",      # 序号
        "requestid", # 流程RequestID
        "formmodeid", # 表单模式ID
        "xglc",      # 相关流程
        "creater",   # 创建人
        "sfwc",      # 是否完成
        "sfjl",      # 是否记录
        "sfjj",      # 是否计价
        # 价格更新相关字段（新增）
        "jggxbj",    # 价格更新标记
        "sjjd",      # 设价节点
        "sftqsj",    # 是否提前设价
        "sftpsybjg", # 是否突破事业部价格
        "sjlx",      # 设价类型
        # 新增字段
        "bnghjlxz",  # 本年供货价类型值
        "sfjc",      # 是否集采
    ])

    def __init__(self, mapping_config: FieldMappingConfig | None = None):
        """初始化数据转换器.

        Args:
            mapping_config: 字段映射配置，默认从 YAML 文件加载
        """
        self._mapping_config = mapping_config or FieldMappingConfig()

    def transform_quotation(self, data: dict[str, Any]) -> Quotation:
        """转换报价单主表数据.

        Args:
            data: Oracle 查询返回的字典

        Returns:
            Quotation 模型实例
        """
        mapping = self._mapping_config.get_quotation_mapping()
        result = {}

        for oracle_field, value in data.items():
            # 获取系统内部字段名
            internal_field = mapping.get(oracle_field, oracle_field.lower())

            # 类型转换
            result[internal_field] = self._convert_value(
                internal_field, value
            )

        return Quotation(
            id=result.get("id", 0),
            wybs=result.get("wybs", ""),
            requestid=result.get("requestid"),
            formmodeid=result.get("formmodeid"),
            modeuuid=result.get("modeuuid"),
            form_biz_id=result.get("form_biz_id"),
            lcbh=result.get("lcbh"),
            htbh=result.get("htbh"),
            xglc=result.get("xglc"),
            creater=result.get("creater"),
            createdate=result.get("createdate"),
            createtime=result.get("createtime"),
        )

    def transform_quotation_detail(self, data: dict[str, Any]) -> QuotationDetail:
        """转换报价单明细数据.

        Args:
            data: Oracle 查询返回的字典

        Returns:
            QuotationDetail 模型实例
        """
        mapping = self._mapping_config.get_quotation_detail_mapping()
        result = {}

        for oracle_field, value in data.items():
            # 获取系统内部字段名
            internal_field = mapping.get(oracle_field, oracle_field.lower())

            # 类型转换
            result[internal_field] = self._convert_value(
                internal_field, value
            )

        return QuotationDetail(
            id=result.get("id", 0),
            mainid=result.get("mainid", 0),
            wybs=result.get("wybs", ""),
            lyxh=result.get("lyxh", 0),
            wldm=result.get("wldm"),
            wlms=result.get("wlms"),
            gg=result.get("gg"),
            dw=result.get("dw"),
            lsj=result.get("lsj"),
            bzjxj=result.get("bzjxj"),
            ghjy=result.get("ghjy"),
            zxkhkpdjy=result.get("zxkhkpdjy"),
            jsj=result.get("jsj"),
            klbfb=result.get("klbfb"),
            yhfdbfb=result.get("yhfdbfb"),
            jgms=result.get("jgms"),
            sfwc=result.get("sfwc"),
            sfjl=result.get("sfjl"),
            sfjj=result.get("sfjj"),
            bz=result.get("bz"),
            # 价格更新相关字段（新增）
            jggxbj=result.get("jggxbj"),
            sjjd=result.get("sjjd"),
            sftqsj=result.get("sftqsj"),
            sftpsybjg=result.get("sftpsybjg"),
            sjlx=result.get("sjlx"),
            sjsj=result.get("sjsj"),
            # 扩展价格字段（新增）
            xzxjg=result.get("xzxjg"),
            tpj=result.get("tpj"),
            sczdjjc=result.get("sczdjjc"),
            sczdjfjc=result.get("sczdjfjc"),
            bzjxjjc=result.get("bzjxjjc"),
            bzjxjfjc=result.get("bzjxjfjc"),
            jczbj=result.get("jczbj"),
            jcjxj=result.get("jcjxj"),
            jgjcy=result.get("jgjcy"),
            # 扩展字段（Browser类型）
            sjkht=result.get("sjkht"),
            djz=result.get("djz"),
            djzmc=result.get("djzmc"),
            sjkhan=result.get("sjkhan"),
            sjkhan_zd=result.get("sjkhan_zd"),
            cpxf=result.get("cpxf"),
            cpxf_name=result.get("cpxf_name"),
            cpxf_bm=result.get("cpxf_bm"),
            pp=result.get("pp"),
            jytc=result.get("jytc"),
            xmjc=result.get("xmjc"),
            tsjgsm=result.get("tsjgsm"),
            # 新增字段（本年供货价类型、是否集采）
            bnghjlx=result.get("bnghjlx"),
            bnghjlxz=result.get("bnghjlxz"),
            sfjc=result.get("sfjc"),
        )

    def transform_quotation_details(
        self, data_list: list[dict[str, Any]]
    ) -> list[QuotationDetail]:
        """转换报价单明细列表.

        Args:
            data_list: Oracle 查询返回的明细字典列表

        Returns:
            QuotationDetail 模型实例列表
        """
        return [self.transform_quotation_detail(data) for data in data_list]

    def _convert_value(self, field_name: str, value: Any) -> Any:
        """根据字段类型进行数据转换.

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            转换后的值
        """
        # 处理 None 值
        if value is None:
            return None

        # 价格字段 -> Decimal
        if field_name in self.PRICE_FIELDS:
            return self._convert_to_decimal(value)

        # 整数字段 -> int
        if field_name in self.INTEGER_FIELDS:
            return self._convert_to_int(value)

        # 其他字段直接返回
        return value

    def _convert_to_decimal(self, value: Any) -> Decimal | None:
        """将值转换为 Decimal（保留2位小数）.

        Args:
            value: 原始值

        Returns:
            Decimal 类型的值
        """
        if value is None:
            return None

        try:
            decimal_value = Decimal(str(value))
            # 保留2位小数，使用ROUND_HALF_UP舍入
            return decimal_value.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except Exception as e:
            logger.warning(
                "Decimal 转换失败",
                extra={"value": str(value), "error": str(e)},
            )
            return None

    def _convert_to_int(self, value: Any) -> int | None:
        """将值转换为 int.

        Args:
            value: 原始值

        Returns:
            int 类型的值
        """
        if value is None:
            return None

        try:
            return int(value)
        except Exception as e:
            logger.warning(
                "Int 转换失败",
                extra={"value": str(value), "error": str(e)},
            )
            return None


# 全局数据转换器实例
_transformer: DataTransformer | None = None
_lock = threading.Lock()


def get_transformer() -> DataTransformer:
    """获取全局数据转换器实例（线程安全的单例模式）.

    Returns:
        DataTransformer 实例
    """
    global _transformer
    if _transformer is None:
        with _lock:
            if _transformer is None:
                _transformer = DataTransformer()
    return _transformer


def transform_quotation(wybs: str) -> QuotationItem:
    """根据报价单号查询并转换报价单数据.

    这是主要入口函数：
    1. 调用 get_quotation_by_wybs 查询主表
    2. 调用 get_quotation_details 查询明细
    3. 使用 DataTransformer 转换数据
    4. 返回 QuotationItem 实例

    Args:
        wybs: 报价单号（唯一标识）

    Returns:
        QuotationItem 实例，包含主表和明细数据

    Raises:
        QueryException: 查询失败时抛出
    """
    logger.info(
        "开始转换报价单数据",
        extra={"wybs": wybs},
    )

    # 1. 查询主表数据
    quotation_data = get_quotation_by_wybs(wybs)

    if quotation_data is None:
        logger.warning(
            "报价单不存在",
            extra={"wybs": wybs},
        )
        # 返回空的 QuotationItem
        return QuotationItem(wybs=wybs, items=[])

    # 2. 查询明细数据
    detail_data_list = get_quotation_details(wybs)

    # 3. 获取转换器
    transformer = get_transformer()

    # 4. 转换主表数据
    quotation = transformer.transform_quotation(quotation_data)

    # 5. 转换明细数据
    details = transformer.transform_quotation_details(detail_data_list)

    # 6. 构建 QuotationItem
    item = QuotationItem(
        wybs=quotation.wybs,
        id=quotation.id,
        lcbh=quotation.lcbh,
        htbh=quotation.htbh,
        xglc=quotation.xglc,
        items=details,
    )

    logger.info(
        "报价单数据转换成功",
        extra={
            "wybs": wybs,
            "main_id": item.id,
            "detail_count": item.item_count,
        },
    )

    return item
