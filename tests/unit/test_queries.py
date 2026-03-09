"""报价单查询模块测试."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import QueryException


class TestGetQuotationByWybs:
    """get_quotation_by_wybs 函数测试类."""

    @patch("src.queries.quotation.get_connection_pool")
    @patch("src.queries.quotation.get_database_config")
    @patch("src.queries.quotation.logger")
    def test_get_quotation_by_wybs_success(self, mock_logger, mock_config, mock_pool):
        """测试查询报价单成功."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = "TEST_SCHEMA.uf_htjgkst"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # 使用上下文管理器
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("ID",),
            ("REQUESTID",),
            ("FORMMODEID",),
            ("MODEDATACREATER",),
            ("MODEDATACREATEDATE",),
            ("MODEDATACREATETIME",),
            ("MODEUUID",),
            ("FORM_BIZ_ID",),
            ("LCBH",),
            ("HTBH",),
            ("XGLC",),
            ("WYBS",),
        ]
        mock_cursor.fetchone.return_value = (
            123,  # ID
            456,  # REQUESTID
            10,  # FORMMODEID
            50,  # MODEDATACREATER
            "2024-01-01",  # MODEDATACREATEDATE
            "10:00:00",  # MODEDATACREATETIME
            "uuid-123",  # MODEUUID
            "BIZ001",  # FORM_BIZ_ID
            "LC001",  # LCBH
            "HT001",  # HTBH
            1,  # XGLC
            "TEST001",  # WYBS
        )

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        # 导入并调用函数
        from src.queries.quotation import get_quotation_by_wybs

        result = get_quotation_by_wybs("TEST001")

        assert result is not None
        assert result["ID"] == 123
        assert result["WYBS"] == "TEST001"
        assert result["LCBH"] == "LC001"
        assert result["HTBH"] == "HT001"

    @patch("src.queries.quotation.get_connection_pool")
    @patch("src.queries.quotation.get_database_config")
    @patch("src.queries.quotation.logger")
    def test_get_quotation_by_wybs_not_found(self, mock_logger, mock_config, mock_pool):
        """测试报价单不存在."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = "TEST_SCHEMA.uf_htjgkst"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [("ID",), ("WYBS",)]
        mock_cursor.fetchone.return_value = None

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation import get_quotation_by_wybs

        result = get_quotation_by_wybs("NOTEXIST")

        assert result is None

    def test_get_quotation_by_wybs_empty_wybs(self):
        """测试 wybs 为空时抛出异常."""
        from src.queries.quotation import get_quotation_by_wybs

        with pytest.raises(QueryException) as exc_info:
            get_quotation_by_wybs("")

        assert "报价单号不能为空" in str(exc_info.value)

    def test_get_quotation_by_wybs_whitespace_only(self):
        """测试 wybs 仅包含空白字符时抛出异常."""
        from src.queries.quotation import get_quotation_by_wybs

        with pytest.raises(QueryException) as exc_info:
            get_quotation_by_wybs("   ")

        assert "报价单号不能为空" in str(exc_info.value)


class TestListQuotations:
    """list_quotations 函数测试类."""

    @patch("src.queries.quotation.get_connection_pool")
    @patch("src.queries.quotation.get_database_config")
    @patch("src.queries.quotation.logger")
    def test_list_quotations_success(self, mock_logger, mock_config, mock_pool):
        """测试查询报价单列表成功."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = "TEST_SCHEMA.uf_htjgkst"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("WYBS",),
            ("LCBH",),
            ("HTBH",),
            ("XGLC",),
            ("MODEDATACREATEDATE",),
        ]
        mock_cursor.fetchall.return_value = [
            ("TEST001", "LC001", "HT001", 1, "2024-01-01"),
            ("TEST002", "LC002", "HT002", 2, "2024-01-02"),
        ]

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation import list_quotations

        result = list_quotations(limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["WYBS"] == "TEST001"
        assert result[1]["WYBS"] == "TEST002"

    @patch("src.queries.quotation.get_connection_pool")
    @patch("src.queries.quotation.get_database_config")
    @patch("src.queries.quotation.logger")
    def test_list_quotations_empty(self, mock_logger, mock_config, mock_pool):
        """测试查询空列表."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = "TEST_SCHEMA.uf_htjgkst"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [
            ("WYBS",),
            ("LCBH",),
            ("HTBH",),
            ("XGLC",),
            ("MODEDATACREATEDATE",),
        ]
        mock_cursor.fetchall.return_value = []

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation import list_quotations

        result = list_quotations(limit=10, offset=0)

        assert result == []

    def test_list_quotations_invalid_limit_zero(self):
        """测试 limit 为 0 时抛出异常."""
        from src.queries.quotation import list_quotations

        with pytest.raises(QueryException) as exc_info:
            list_quotations(limit=0)

        assert "limit 必须大于 0" in str(exc_info.value)

    def test_list_quotations_invalid_limit_negative(self):
        """测试 limit 为负数时抛出异常."""
        from src.queries.quotation import list_quotations

        with pytest.raises(QueryException) as exc_info:
            list_quotations(limit=-1)

        assert "limit 必须大于 0" in str(exc_info.value)

    def test_list_quotations_invalid_limit_exceed_max(self):
        """测试 limit 超过最大值时抛出异常."""
        from src.queries.quotation import list_quotations, MAX_LIMIT

        with pytest.raises(QueryException) as exc_info:
            list_quotations(limit=MAX_LIMIT + 1)

        assert f"limit 不能超过 {MAX_LIMIT}" in str(exc_info.value)

    def test_list_quotations_invalid_offset_negative(self):
        """测试 offset 为负数时抛出异常."""
        from src.queries.quotation import list_quotations

        with pytest.raises(QueryException) as exc_info:
            list_quotations(limit=10, offset=-1)

        assert "offset 不能为负数" in str(exc_info.value)


class TestGetQuotationDetails:
    """get_quotation_details 函数测试类."""

    @patch("src.queries.quotation_detail.get_connection_pool")
    @patch("src.queries.quotation_detail.get_database_config")
    @patch("src.queries.quotation_detail.logger")
    def test_get_quotation_details_success(self, mock_logger, mock_config, mock_pool):
        """测试查询明细成功."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = (
            "TEST_SCHEMA.uf_htjgkst_dt1"
        )
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接和游标
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (
                100,  # ID
                123,  # MAINID
                "TEST001",  # WYBS
                1,  # LYXH
                "M001",  # WLDM
                "物料1",  # WLMS
                "规格A",  # GG
                "个",  # DW
                "价格描述",  # JGMS
                Decimal("100.00"),  # LSJ
                Decimal("90.00"),  # BZJXJ
                Decimal("80.00"),  # GHJY
                Decimal("75.00"),  # ZXKHKPDJY
                Decimal("70.00"),  # JSJ
                Decimal("0.85"),  # KLBFB
                Decimal("0.15"),  # YHFDBFB
                "备注",  # BZ
                1,  # SFWC
                1,  # SFJL
                1,  # SFJJ
                # 价格更新相关字段（新增）
                1,  # JGGXBJ
                2,  # SJJD
                0,  # SFTQSJ
                0,  # SFTPSYBJG
                1,  # SJLX
                "2024-01-01 10:00:00",  # SJSJ
                # 扩展价格字段（新增）
                Decimal("95.00"),  # XZXJG
                Decimal("85.00"),  # TPJ
                Decimal("90.00"),  # SCZDJJC
                Decimal("88.00"),  # SCZDJFJC
                Decimal("92.00"),  # BZJXJJC
                Decimal("90.00"),  # BZJXJFJC
                Decimal("82.00"),  # JCZBJ
                Decimal("80.00"),  # JCJXJ
                Decimal("5.00"),  # JGJCY
                "特殊价格说明",  # TSJGSM
                # 新增字段（本年供货价类型、是否集采）
                "供货类型A",  # BNGHJLX
                1,  # BNGHJLXZ
                1,  # SFJC
            ),
        ]

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation_detail import get_quotation_details

        result = get_quotation_details("TEST001")

        assert len(result) == 1
        assert result[0]["ID"] == 100
        assert result[0]["WLDM"] == "M001"
        assert result[0]["LYXH"] == 1
        # 验证新字段
        assert result[0]["JGGXBJ"] == 1
        assert result[0]["SJJD"] == 2
        assert result[0]["XZXJG"] == Decimal("95.00")

    @patch("src.queries.quotation_detail.get_connection_pool")
    @patch("src.queries.quotation_detail.get_database_config")
    @patch("src.queries.quotation_detail.logger")
    def test_get_quotation_details_empty(self, mock_logger, mock_config, mock_pool):
        """测试查询空明细."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_db_config.get_qualified_table.return_value = (
            "TEST_SCHEMA.uf_htjgkst_dt1"
        )
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接和游标
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation_detail import get_quotation_details

        result = get_quotation_details("TEST001")

        assert result == []

    def test_get_quotation_details_empty_wybs(self):
        """测试 wybs 为空时抛出异常."""
        from src.queries.quotation_detail import get_quotation_details

        with pytest.raises(QueryException) as exc_info:
            get_quotation_details("")

        assert "报价单号（wybs）不能为空" in str(exc_info.value)

    def test_get_quotation_details_whitespace_only(self):
        """测试 wybs 仅包含空白字符时抛出异常."""
        from src.queries.quotation_detail import get_quotation_details

        with pytest.raises(QueryException) as exc_info:
            get_quotation_details("   ")

        assert "报价单号（wybs）不能为空" in str(exc_info.value)


class TestGetQuotationDetailCount:
    """get_quotation_detail_count 函数测试类."""

    @patch("src.queries.quotation_detail.get_connection_pool")
    @patch("src.queries.quotation_detail.get_database_config")
    @patch("src.queries.quotation_detail.logger")
    def test_get_quotation_detail_count_success(
        self, mock_logger, mock_config, mock_pool
    ):
        """测试查询明细数量成功."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接和游标
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation_detail import get_quotation_detail_count

        result = get_quotation_detail_count("TEST001")

        assert result == 5

    @patch("src.queries.quotation_detail.get_connection_pool")
    @patch("src.queries.quotation_detail.get_database_config")
    @patch("src.queries.quotation_detail.logger")
    def test_get_quotation_detail_count_zero(
        self, mock_logger, mock_config, mock_pool
    ):
        """测试查询数量为 0."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接和游标
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation_detail import get_quotation_detail_count

        result = get_quotation_detail_count("TEST001")

        assert result == 0

    @patch("src.queries.quotation_detail.get_connection_pool")
    @patch("src.queries.quotation_detail.get_database_config")
    @patch("src.queries.quotation_detail.logger")
    def test_get_quotation_detail_count_none_result(
        self, mock_logger, mock_config, mock_pool
    ):
        """测试查询结果为 None 时返回 0."""
        # Mock 配置
        mock_db_config = MagicMock()
        mock_db_config.schema = "TEST_SCHEMA"
        mock_config.return_value = mock_db_config

        # Mock 连接池
        mock_pool_instance = MagicMock()
        mock_pool.return_value = mock_pool_instance

        # Mock 连接和游标
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None

        # 设置上下文管理器
        mock_pool_instance.connection.return_value.__enter__ = MagicMock(
            return_value=mock_conn
        )
        mock_pool_instance.connection.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_conn.cursor.return_value.__enter__ = MagicMock(
            return_value=mock_cursor
        )
        mock_conn.cursor.return_value.__exit__ = MagicMock(
            return_value=False
        )

        from src.queries.quotation_detail import get_quotation_detail_count

        result = get_quotation_detail_count("TEST001")

        assert result == 0


class TestValidateWybs:
    """_validate_wybs 内部函数测试类."""

    def test_validate_wybs_valid(self):
        """测试有效的 wybs."""
        from src.queries.quotation_detail import _validate_wybs

        result = _validate_wybs("TEST001")

        assert result == "TEST001"

    def test_validate_wybs_with_whitespace(self):
        """测试带前后空白的 wybs."""
        from src.queries.quotation_detail import _validate_wybs

        result = _validate_wybs("  TEST001  ")

        assert result == "TEST001"

    def test_validate_wybs_empty(self):
        """测试空 wybs."""
        from src.queries.quotation_detail import _validate_wybs

        with pytest.raises(QueryException) as exc_info:
            _validate_wybs("")

        assert "报价单号（wybs）不能为空" in str(exc_info.value)

    def test_validate_wybs_none(self):
        """测试 None wybs."""
        from src.queries.quotation_detail import _validate_wybs

        with pytest.raises(QueryException) as exc_info:
            _validate_wybs(None)

        assert "报价单号（wybs）不能为空" in str(exc_info.value)

    def test_validate_wybs_whitespace_only(self):
        """测试仅空白字符的 wybs."""
        from src.queries.quotation_detail import _validate_wybs

        with pytest.raises(QueryException) as exc_info:
            _validate_wybs("   ")

        assert "报价单号（wybs）不能为空" in str(exc_info.value)


class TestRowToDict:
    """_row_to_dict 内部函数测试类."""

    def test_row_to_dict_basic(self):
        """测试基本转换."""
        from src.queries.quotation_detail import _row_to_dict

        row = (1, "TEST001", "LC001")
        columns = ["ID", "WYBS", "LCBH"]

        result = _row_to_dict(row, columns)

        assert result == {"ID": 1, "WYBS": "TEST001", "LCBH": "LC001"}

    def test_row_to_dict_mismatch_length(self):
        """测试行和列长度不匹配."""
        from src.queries.quotation_detail import _row_to_dict

        row = (1, "TEST001")
        columns = ["ID", "WYBS", "LCBH"]

        result = _row_to_dict(row, columns)

        # zip 会截断为较短的长度
        assert result == {"ID": 1, "WYBS": "TEST001"}
