"""pytest 全局配置和共享 fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator

import pytest

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============ Settings Fixtures ============


@pytest.fixture
def mock_settings():
    """模拟配置 fixture."""
    from src.config.settings import Settings, AppSettings, DatabaseSettings, TemplateSettings, LoggingSettings
    from pydantic import SecretStr

    return Settings(
        app=AppSettings(
            name="价格附件生成系统",
            debug=True,
            host="127.0.0.1",
            port=8000,
            version="1.0.0",
            _env_file=None,
        ),
        database=DatabaseSettings(
            dsn=SecretStr("oracle://test:test@localhost:1521/TEST"),
            min_pool_size=1,
            max_pool_size=10,
            pool_timeout=30,
            _env_file=None,
        ),
        template=TemplateSettings(
            path="docs/template",
            output_dir="output",
            _env_file=None,
        ),
        logging=LoggingSettings(
            level="INFO",
            _env_file=None,
        ),
    )


@pytest.fixture
def mock_settings_debug():
    """模拟调试模式配置."""
    from src.config.settings import Settings, AppSettings, DatabaseSettings, TemplateSettings, LoggingSettings
    from pydantic import SecretStr

    return Settings(
        app=AppSettings(
            name="测试系统",
            debug=True,
            host="127.0.0.1",
            port=8000,
            version="1.0.0",
            _env_file=None,
        ),
        database=DatabaseSettings(
            dsn=SecretStr("oracle://test:test@localhost:1521/TEST"),
            _env_file=None,
        ),
        template=TemplateSettings(_env_file=None),
        logging=LoggingSettings(level="DEBUG", _env_file=None),
    )


# ============ Database Fixtures ============


@pytest.fixture
def mock_db_pool():
    """模拟数据库连接池."""
    mock = MagicMock()
    mock.acquire.return_value = MagicMock()
    return mock


@pytest.fixture
def mock_db_connection():
    """创建模拟的数据库连接和上下文管理器."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # 设置 context manager
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    mock_pool = MagicMock()
    mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)

    return {"pool": mock_pool, "conn": mock_conn, "cursor": mock_cursor}


# ============ File Fixtures ============


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """临时输出目录 fixture."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def temp_template_dir(tmp_path) -> Path:
    """临时模板目录 fixture."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir


# ============ API Fixtures ============


@pytest.fixture
def auth_headers() -> dict:
    """认证请求头."""
    return {"Authorization": "Bearer sk_test_12345678"}


@pytest.fixture
def mock_api_key() -> str:
    """模拟API Key."""
    return "sk_test_12345678"


# ============ Task Fixtures ============


@pytest.fixture
def mock_task_manager():
    """模拟任务管理器."""
    mock = MagicMock()
    return mock


# ============ Generator Fixtures ============


@pytest.fixture
def sample_quotation_data() -> dict:
    """示例报价单数据."""
    return {
        "报价单号": "WYBS20260310",
        "客户名称": "XX医院",
        "标题": "通用生化产品供货价",
        "金额单位": "元",
        "产品细分": "通用生化试剂",
        "是否集采": "否",
        "肝功扣率": "85",
    }


@pytest.fixture
def sample_detail_data() -> list:
    """示例明细数据."""
    return [
        {
            "WLDM": "MAT001",
            "WLMS": "测试物料1",
            "GG": "10ml",
            "LSJ": 100.00,
            "GHJY": 70.00,
        },
        {
            "WLDM": "MAT002",
            "WLMS": "测试物料2",
            "GG": "20ml",
            "LSJ": 200.00,
            "GHJY": 140.00,
        },
    ]


# ============ Cleanup Fixtures ============


@pytest.fixture
def clean_audit_logger():
    """清理审计日志单例，确保测试隔离."""
    import src.services.audit_logger as audit_module
    original = audit_module._audit_logger
    audit_module._audit_logger = None

    yield

    audit_module._audit_logger = original
