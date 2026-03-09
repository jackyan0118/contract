"""数据转换器模块测试."""

import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.models import Quotation, QuotationDetail, QuotationItem
from src.transformers.data_transformer import (
    DataTransformer,
    FieldMappingConfig,
    get_transformer,
    transform_quotation,
)


class TestFieldMappingConfig:
    """FieldMappingConfig 测试类."""

    def test_load_from_yaml(self):
        """测试从 YAML 加载配置."""
        config_data = {
            "quotation": {
                "mapping": {
                    "ID": "id",
                    "WYBS": "wybs",
                    "LCBH": "lcbh",
                }
            },
            "quotation_detail": {
                "mapping": {
                    "ID": "id",
                    "WLDM": "wldm",
                }
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = FieldMappingConfig(temp_path)
            assert config.get_quotation_mapping() == {
                "ID": "id",
                "WYBS": "wybs",
                "LCBH": "lcbh",
            }
            assert config.get_quotation_detail_mapping() == {
                "ID": "id",
                "WLDM": "wldm",
            }
        finally:
            Path(temp_path).unlink()

    def test_default_config_path(self):
        """测试默认配置文件路径."""
        # 使用默认配置
        config = FieldMappingConfig()
        # 验证能成功加载默认配置
        assert config.get_quotation_mapping() is not None
        assert config.get_quotation_detail_mapping() is not None


class TestDataTransformer:
    """DataTransformer 测试类."""

    @pytest.fixture
    def config(self):
        """创建测试配置."""
        config_data = {
            "quotation": {
                "mapping": {
                    "ID": "id",
                    "WYBS": "wybs",
                    "REQUESTID": "requestid",
                    "FORMMODEID": "formmodeid",
                    "LCBH": "lcbh",
                    "HTBH": "htbh",
                    "XGLC": "xglc",
                }
            },
            "quotation_detail": {
                "mapping": {
                    "ID": "id",
                    "MAINID": "mainid",
                    "WYBS": "wybs",
                    "LYXH": "lyxh",
                    "WLDM": "wldm",
                    "WLMS": "wlms",
                    "GG": "gg",
                    "DW": "dw",
                    "LSJ": "lsj",
                    "BZJXJ": "bzjxj",
                    "GHJY": "ghjy",
                    "JSJ": "jsj",
                    "KLBFB": "klbfb",
                    "YHFDBFB": "yhfdbfb",
                }
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            return FieldMappingConfig(temp_path)
        finally:
            Path(temp_path).unlink()

    @pytest.fixture
    def transformer(self, config):
        """创建测试转换器."""
        return DataTransformer(config)

    def test_transform_quotation(self, transformer):
        """测试报价单主表转换."""
        data = {
            "ID": 123,
            "WYBS": "TEST001",
            "REQUESTID": 456,
            "FORMMODEID": 789,
            "LCBH": "LC001",
            "HTBH": "HT001",
            "XGLC": 1,
        }

        result = transformer.transform_quotation(data)

        assert isinstance(result, Quotation)
        assert result.id == 123
        assert result.wybs == "TEST001"
        assert result.requestid == 456
        assert result.formmodeid == 789
        assert result.lcbh == "LC001"
        assert result.htbh == "HT001"
        assert result.xglc == 1

    def test_transform_quotation_detail(self, transformer):
        """测试报价单明细转换."""
        data = {
            "ID": 100,
            "MAINID": 123,
            "WYBS": "TEST001",
            "LYXH": 1,
            "WLDM": "M001",
            "WLMS": "物料1",
            "GG": "规格1",
            "DW": "个",
            "LSJ": 100.50,
            "BZJXJ": 90.00,
            "GHJY": 80.00,
            "JSJ": 75.00,
            "KLBFB": 0.85,
            "YHFDBFB": 0.10,
        }

        result = transformer.transform_quotation_detail(data)

        assert isinstance(result, QuotationDetail)
        assert result.id == 100
        assert result.mainid == 123
        assert result.wybs == "TEST001"
        assert result.lyxh == 1
        assert result.wldm == "M001"
        assert result.wlms == "物料1"
        assert result.gg == "规格1"
        assert result.dw == "个"
        assert result.lsj == Decimal("100.50")
        assert result.bzjxj == Decimal("90.00")
        assert result.ghjy == Decimal("80.00")
        assert result.jsj == Decimal("75.00")
        assert result.klbfb == Decimal("0.85")
        assert result.yhfdbfb == Decimal("0.10")

    def test_transform_quotation_details_list(self, transformer):
        """测试报价单明细列表转换."""
        data_list = [
            {
                "ID": 100,
                "MAINID": 123,
                "WYBS": "TEST001",
                "LYXH": 1,
                "WLDM": "M001",
                "LSJ": 100.50,
            },
            {
                "ID": 101,
                "MAINID": 123,
                "WYBS": "TEST001",
                "LYXH": 2,
                "WLDM": "M002",
                "LSJ": 200.75,
            },
        ]

        results = transformer.transform_quotation_details(data_list)

        assert len(results) == 2
        assert results[0].id == 100
        assert results[0].lyxh == 1
        assert results[0].lsj == Decimal("100.50")
        assert results[1].id == 101
        assert results[1].lyxh == 2
        assert results[1].lsj == Decimal("200.75")

    def test_convert_to_decimal(self, transformer):
        """测试 Decimal 转换."""
        # 正常转换
        assert transformer._convert_to_decimal(100.556) == Decimal("100.56")
        assert transformer._convert_to_decimal("100.554") == Decimal("100.55")
        assert transformer._convert_to_decimal(100) == Decimal("100.00")

        # None 值
        assert transformer._convert_to_decimal(None) is None

    def test_convert_to_int(self, transformer):
        """测试 Int 转换."""
        # 正常转换
        assert transformer._convert_to_int(100) == 100
        assert transformer._convert_to_int("200") == 200
        assert transformer._convert_to_int(100.5) == 100

        # None 值
        assert transformer._convert_to_int(None) is None


class TestTransformQuotation:
    """transform_quotation 函数测试类."""

    @patch("src.transformers.data_transformer.get_quotation_by_wybs")
    @patch("src.transformers.data_transformer.get_quotation_details")
    def test_transform_quotation_success(
        self, mock_details, mock_quotation
    ):
        """测试完整转换流程 - 成功."""
        # Mock 主表数据
        mock_quotation.return_value = {
            "ID": 123,
            "WYBS": "TEST001",
            "LCBH": "LC001",
            "HTBH": "HT001",
            "XGLC": 1,
        }

        # Mock 明细数据
        mock_details.return_value = [
            {
                "ID": 100,
                "MAINID": 123,
                "WYBS": "TEST001",
                "LYXH": 1,
                "WLDM": "M001",
                "WLMS": "物料1",
                "LSJ": 100.50,
            }
        ]

        result = transform_quotation("TEST001")

        assert isinstance(result, QuotationItem)
        assert result.wybs == "TEST001"
        assert result.id == 123
        assert result.lcbh == "LC001"
        assert result.htbh == "HT001"
        assert result.item_count == 1
        assert result.items[0].wldm == "M001"

    @patch("src.transformers.data_transformer.get_quotation_by_wybs")
    def test_transform_quotation_not_found(self, mock_quotation):
        """测试报价单不存在的情况."""
        mock_quotation.return_value = None

        result = transform_quotation("NOTEXIST")

        assert isinstance(result, QuotationItem)
        assert result.wybs == "NOTEXIST"
        assert result.item_count == 0


class TestGetTransformer:
    """get_transformer 函数测试类."""

    def test_get_transformer_singleton(self):
        """测试单例模式."""
        transformer1 = get_transformer()
        transformer2 = get_transformer()

        assert transformer1 is transformer2
