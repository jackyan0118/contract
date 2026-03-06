# 待办事项清单

## 优先级说明

- **P0**: 必须在 Phase 1 完成前解决
- **P1**: 建议在 Phase 1 完成前解决
- **P2**: 可以在后续迭代中解决

---

## P0 - 必须修复

### A-001: DSN 使用 SecretStr 加密

| 项目 | 说明 |
|------|------|
| 文件 | 03-config-management.md, 06-config-template.md |
| 负责人 | 安全专家 |
| 状态 | 待修复 |

**修复代码**:

```python
# src/config/settings.py
from pydantic import SecretStr

class DatabaseSettings(BaseSettings):
    dsn: SecretStr = Field(
        default=SecretStr(""),
        description="Oracle 连接字符串",
    )

    @field_validator("dsn")
    @classmethod
    def validate_dsn(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("数据库连接字符串不能为空")
        return v

    def get_dsn(self) -> str:
        """获取解密后的 DSN."""
        return self.dsn.get_secret_value()
```

---

### A-002: 添加数据库连接参数边界验证

| 项目 | 说明 |
|------|------|
| 文件 | 03-config-management.md |
| 负责人 | Python 专家 |
| 状态 | 待修复 |

**修复代码**:

```python
class DatabaseSettings(BaseSettings):
    min_connections: int = Field(default=2, description="最小连接数")
    max_connections: int = Field(default=10, description="最大连接数")

    @field_validator("max_connections")
    @classmethod
    def validate_max_connections(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("最大连接数必须在 1-100 范围内")
        return v

    @model_validator(mode="after")
    def validate_pool_size(self):
        if self.max_connections < self.min_connections:
            raise ValueError("最大连接数不能小于最小连接数")
        return self
```

---

### A-003: SQL 查询日志脱敏处理

| 项目 | 说明 |
|------|------|
| 文件 | 05-exception-handling.md |
| 负责人 | 安全专家 |
| 状态 | 待修复 |

**修复代码**:

```python
# src/exceptions/database.py
class QueryException(DatabaseException):
    def __init__(self, query: str, reason: str, **kwargs):
        # 脱敏处理
        sanitized_query = self._sanitize_query(query)
        super().__init__(
            message=f"数据库查询失败：{reason}",
            error_code=ErrorCode.QUERY_ERROR,
            detail={"query": sanitized_query, "reason": reason, **kwargs.get("detail", {})},
            **kwargs,
        )

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """脱敏 SQL 查询中的敏感信息."""
        import re
        # 移除字符串字面量
        return re.sub(r"'[^']*'", "'***'", query)
```

---

### A-004: 日志格式化器修复 record 修改问题

| 项目 | 说明 |
|------|------|
| 文件 | 04-logging-system.md |
| 负责人 | Python 专家 |
| 状态 | 待修复 |

**修复代码**:

```python
# src/utils/logger.py
class ColoredFormatter(logging.Formatter):
    """控制台彩色日志格式化器."""

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # 保存原始值
        original_levelname = record.levelname
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        # 格式化
        result = super().format(record)
        # 恢复原始值
        record.levelname = original_levelname
        return result
```

---

### A-005: 添加配置文件权限说明

| 项目 | 说明 |
|------|------|
| 文件 | 06-config-template.md |
| 负责人 | 安全专家 |
| 状态 | ✅ 已完成 |

**修复内容**:

```bash
# 在 06-config-template.md 中添加

## 文件权限设置

```bash
# 设置配置文件权限
chmod 600 config/settings.yaml
chmod 600 .env

# 设置目录权限
chmod 750 logs/
chmod 750 output/
```

---

## P1 - 建议修复

### B-001: 添加 pre-commit 配置

| 项目 | 说明 |
|------|------|
| 文件 | 02-project-configuration.md |
| 负责人 | Python 专家 |
| 状态 | 待添加 |

**新增文件**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.10
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0.0]
```

---

### B-002: 添加覆盖率阈值配置

| 项目 | 说明 |
|------|------|
| 文件 | 02-project-configuration.md |
| 负责人 | 测试专家 |
| 状态 | 待添加 |

**修复内容**:

```toml
[tool.pytest.ini_options]
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.report]
fail_under = 80
```

---

### B-003: 添加测试标记

| 项目 | 说明 |
|------|------|
| 文件 | 02-project-configuration.md |
| 负责人 | 测试专家 |
| 状态 | 待添加 |

**修复内容**:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow running tests",
]
```

---

### B-004: 添加 import-linter 依赖检查

| 项目 | 说明 |
|------|------|
| 文件 | 01-directory-structure.md |
| 负责人 | 架构师 |
| 状态 | 待添加 |

**修复内容**:

```toml
[tool.importlinter]
root_packages = ["src"]

[[tool.importlinter.contracts]]
name = "Layer architecture"
type = "layers"
layers = [
    "src.api",
    "src.services",
    "src.matchers | src.generators",
    "src.database | src.config",
]
```

---

### B-005: 异常中间件导入优化

| 项目 | 说明 |
|------|------|
| 文件 | 05-exception-handling.md |
| 负责人 | Python 专家 |
| 状态 | 待修复 |

**修复代码**:

```python
# src/api/middleware/error_handler.py
# 将导入移到模块顶部
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from src.exceptions.base import AppException, ErrorCode
from src.utils.logger import get_logger

logger = get_logger("api.error")

def _get_status_code(error_code) -> int:
    """根据错误代码返回 HTTP 状态码."""
    status_map = {
        ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
        # ...
    }
    return status_map.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

### B-006: 结构化日志 kwargs 覆盖保护

| 项目 | 说明 |
|------|------|
| 文件 | 04-logging-system.md |
| 负责人 | Python 专家 |
| 状态 | 待修复 |

**修复代码**:

```python
# src/utils/structured_logger.py
def _log(
    self,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> None:
    extra: Dict[str, Any] = {}
    if context:
        extra["context"] = context
    # 防止覆盖保留字段
    reserved_keys = {"context"}
    for key, value in kwargs.items():
        if key in reserved_keys:
            raise ValueError(f"Cannot override reserved key: {key}")
        extra[key] = value
    self.logger.log(level, message, extra=extra)
```

---

### B-007: 添加静态资源目录定义

| 项目 | 说明 |
|------|------|
| 文件 | 01-directory-structure.md |
| 负责人 | 架构师 |
| 状态 | 待添加 |

**修复内容**:

```
contract/
├── static/                  # 静态资源（如有 Web UI）
├── uploads/                 # 上传文件（.gitignore）
├── output/                  # 生成输出（.gitignore）
└── temp/                    # 临时文件（.gitignore）
```

---

## P2 - 后续优化

### C-001 ~ C-006

| 编号 | 问题 | 负责人 | 状态 |
|------|------|--------|------|
| C-001 | 考虑异步日志支持 | 架构师 | 待评估 |
| C-002 | 引入依赖注入容器 | 架构师 | 待评估 |
| C-003 | 配置热更新机制 | 架构师 | 待评估 |
| C-004 | 添加 Makefile | Python 专家 | 待添加 |
| C-005 | 添加 py.typed 标记文件 | Python 专家 | 待添加 |
| C-006 | 添加依赖安全扫描 | 安全专家 | 待添加 |

---

## 任务跟踪

### 完成条件

Phase 1 设计文档在以下条件下可以进入实施阶段:

#### 必须完成 (P0)
- [x] A-001: DSN 安全处理
- [x] A-002: 参数边界验证
- [x] A-003: SQL 日志脱敏
- [x] A-004: 日志格式化器修复
- [x] A-005: 文件权限说明

#### 建议完成 (P1)
- [ ] B-001: pre-commit 配置
- [ ] B-002: 覆盖率阈值配置

---

*创建日期：2026-03-06*
*最后更新：2026-03-06*
