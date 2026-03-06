# 测试评审意见

## 评审人：测试专家

---

## 1. 测试策略评估

当前设计文档中提到了测试要求，但缺少详细的测试策略文档。

### 1.1 测试配置评估

```toml
# pyproject.toml - 当前配置
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing"
```

**优点**:
- 启用了覆盖率报告
- 配置了异步测试支持
- 覆盖率报告包含缺失行号

**待改进**:
- 未设置覆盖率阈值
- 未配置测试标记

### 1.2 建议改进

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "src/__init__.py",
    "tests/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
fail_under = 80
```

---

## 2. 测试覆盖计划

### 2.1 单元测试

| 模块 | 测试文件 | 测试重点 | 优先级 |
|------|----------|----------|--------|
| config/settings.py | tests/unit/test_config.py | 配置加载、验证、默认值 | P0 |
| utils/logger.py | tests/unit/test_logger.py | 日志格式、轮转、彩色输出 | P0 |
| exceptions/*.py | tests/unit/test_exceptions.py | 异常层次、错误码、序列化 | P0 |

### 2.2 集成测试

| 模块 | 测试文件 | 测试重点 | 优先级 |
|------|----------|----------|--------|
| config + logger | tests/integration/test_config_logger.py | 配置驱动的日志初始化 | P1 |
| exceptions + middleware | tests/integration/test_error_handling.py | 异常捕获和 API 响应 | P1 |

### 2.3 E2E 测试

| 测试场景 | 测试文件 | 测试重点 | 优先级 |
|----------|----------|----------|--------|
| 完整生成流程 | tests/e2e/test_generate_flow.py | wybs -> Word 文件生成 | P0 |
| 批量生成 | tests/e2e/test_batch_generate.py | 批量处理 + ZIP 打包 | P1 |

---

## 3. 测试用例示例

### 3.1 配置测试

```python
# tests/unit/test_config.py
"""配置管理模块单元测试."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, AppSettings, DatabaseSettings


class TestAppSettings:
    """AppSettings 测试类."""

    def test_default_values(self):
        """测试默认值."""
        settings = AppSettings()
        assert settings.name == "价格附件生成系统"
        assert settings.debug is False
        assert settings.port == 8000

    def test_port_validation_valid(self):
        """测试有效端口验证."""
        settings = AppSettings(port=8080)
        assert settings.port == 8080

    def test_port_validation_invalid_low(self):
        """测试端口过小验证."""
        with pytest.raises(ValidationError, match="端口必须在"):
            AppSettings(port=0)

    def test_port_validation_invalid_high(self):
        """测试端口过大验证."""
        with pytest.raises(ValidationError, match="端口必须在"):
            AppSettings(port=65536)

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖."""
        monkeypatch.setenv("APP_PORT", "9000")
        settings = AppSettings()
        assert settings.port == 9000


class TestDatabaseSettings:
    """DatabaseSettings 测试类."""

    def test_dsn_required(self):
        """测试 DSN 必填."""
        with pytest.raises(ValidationError, match="数据库连接字符串不能为空"):
            DatabaseSettings()

    def test_dsn_valid(self):
        """测试有效 DSN."""
        settings = DatabaseSettings(dsn="oracle://user:pass@host:1521/ORCL")
        assert settings.dsn == "oracle://user:pass@host:1521/ORCL"


class TestSettings:
    """Settings 聚合配置测试类."""

    def test_load_from_yaml(self, tmp_path: Path):
        """测试从 YAML 加载配置."""
        yaml_content = """
app:
  name: 测试系统
  port: 9000
database:
  dsn: oracle://test:test@localhost:1521/TEST
"""
        yaml_file = tmp_path / "settings.yaml"
        yaml_file.write_text(yaml_content, encoding="utf-8")

        settings = Settings.load_from_yaml(str(yaml_file))
        assert settings.app.name == "测试系统"
        assert settings.app.port == 9000

    def test_singleton_cache(self):
        """测试单例缓存."""
        from src.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
```

### 3.2 异常测试

```python
# tests/unit/test_exceptions.py
"""异常处理模块单元测试."""

import pytest

from src.exceptions import (
    AppException,
    ErrorCode,
    ConfigNotFoundError,
    TemplateNotFoundError,
    MatchException,
)


class TestAppException:
    """AppException 测试类."""

    def test_basic_exception(self):
        """测试基本异常."""
        exc = AppException("测试错误")
        assert exc.message == "测试错误"
        assert exc.error_code == ErrorCode.UNKNOWN_ERROR

    def test_exception_with_detail(self):
        """测试带详情的异常."""
        exc = AppException(
            message="测试错误",
            error_code=ErrorCode.VALIDATION_ERROR,
            detail={"field": "name"},
        )
        assert exc.detail == {"field": "name"}
        assert exc.to_dict()["error_code"] == "1001"

    def test_exception_with_cause(self):
        """测试异常链."""
        original = ValueError("原始错误")
        exc = AppException("包装错误", cause=original)
        assert exc.cause is original


class TestTemplateExceptions:
    """模板异常测试类."""

    def test_template_not_found(self):
        """测试模板未找到异常."""
        exc = TemplateNotFoundError(template_name="模板 1")
        assert exc.error_code == ErrorCode.TEMPLATE_NOT_FOUND
        assert "模板 1" in exc.message
        assert exc.detail["template_name"] == "模板 1"

    def test_match_exception(self):
        """测试匹配异常."""
        exc = MatchException(wybs="QTD001", reason="无匹配规则")
        assert exc.error_code == ErrorCode.MATCH_ERROR
        assert exc.detail["wybs"] == "QTD001"
```

---

## 4. 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|------------|----------|
| src/config/ | 90% | 待实现 |
| src/utils/ | 85% | 待实现 |
| src/exceptions/ | 95% | 待实现 |
| 总体 | 80% | 待实现 |

---

## 5. 测试评审结论

| 项目 | 状态 | 说明 |
|------|------|------|
| 测试目录结构 | ✅ 通过 | unit/integration/e2e 分层 |
| 测试配置 | ⚠️ 部分通过 | 需添加覆盖率阈值 |
| 测试用例 | ❌ 待实现 | 需按计划实现 |
| 测试标记 | ❌ 待添加 | 建议添加 markers |
| Mock 策略 | ❌ 待定义 | 需要 conftest.py 配置 |

---

## 6. 推荐 conftest.py 配置

```python
# tests/conftest.py
"""pytest 全局配置和 fixtures."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.config import Settings, AppSettings, DatabaseSettings


@pytest.fixture
def mock_settings() -> Settings:
    """模拟配置（用于单元测试）."""
    return Settings(
        app=AppSettings(debug=True, port=8000),
        database=DatabaseSettings(dsn="oracle://test:test@localhost:1521/TEST"),
    )


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """临时输出目录."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_db_connection():
    """模拟数据库连接."""
    mock = MagicMock()
    mock.query.return_value = []
    return mock
```

---

*评审日期：2026-03-06*
