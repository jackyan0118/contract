# 安全评审意见

## 评审人：安全专家

---

## 1. 安全风险识别

### 1.1 严重风险

#### 风险 1: 数据库连接字符串明文存储

```yaml
# config/settings.yaml.example - 问题代码
database:
  dsn: "oracle://user:password@localhost:1521/ORCL"  # 密码明文！
```

**影响**: 密码泄露风险

**修复建议**:

```python
# 使用 Pydantic SecretStr
from pydantic import SecretStr

class DatabaseSettings(BaseSettings):
    dsn: SecretStr = Field(
        default=SecretStr(""),
        description="Oracle 连接字符串",
    )

    def get_dsn(self) -> str:
        """获取解密后的 DSN."""
        return self.dsn.get_secret_value()
```

```yaml
# 配置文件中使用环境变量引用
database:
  dsn: "${DB_DSN}"  # 从环境变量读取
```

---

### 1.2 高风险

#### 风险 2: `.env.example` 中的示例凭据

```bash
# .env.example - 问题示例
DB_DSN=oracle://user:password@localhost:1521/ORCL
```

**问题**: 虽然是示例文件，但用户可能直接复制使用

**修复建议**:

```bash
# 使用占位符
DB_DSN=oracle://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:1521/YOUR_SERVICE
```

#### 风险 3: 日志中可能泄露敏感信息

```python
# src/exceptions/database.py - 问题代码
class QueryException(DatabaseException):
    def __init__(self, query: str, reason: str, **kwargs):
        detail={"query": query, ...}  # SQL 可能包含敏感数据
```

**问题**: SQL 查询可能包含敏感数据（如用户信息），不应直接记录

**修复建议**:

```python
def __init__(self, query: str, reason: str, **kwargs):
    # 脱敏处理
    sanitized_query = self._sanitize_query(query)
    detail={"query": sanitized_query, ...}

@staticmethod
def _sanitize_query(query: str) -> str:
    """脱敏 SQL 查询中的敏感信息."""
    import re
    # 移除字符串字面量
    return re.sub(r"'[^']*'", "'***'", query)
```

---

### 1.3 中风险

#### 风险 4: 配置文件权限未定义

`.gitignore` 中忽略了 `config/settings.yaml`，但未说明文件权限要求

**建议**: 在文档中添加文件权限说明:

```bash
# 设置配置文件权限
chmod 600 config/settings.yaml
chown app:app config/settings.yaml
```

#### 风险 5: 缺少输入验证边界说明

配置验证器存在，但缺少对配置值边界的完整验证

```python
# 当前验证
@field_validator("port")
def validate_port(cls, v: int) -> int:
    if not 1 <= v <= 65535:
        raise ValueError("端口必须在 1-65535 范围内")
    return v

# 建议补充
@field_validator("max_connections")
def validate_max_connections(cls, v: int) -> int:
    if v < 1 or v > 100:
        raise ValueError("最大连接数必须在 1-100 范围内")
    if v < cls.min_connections:
        raise ValueError("最大连接数不能小于最小连接数")
    return v
```

---

## 2. 安全检查清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 敏感数据加密 | ❌ 待改进 | DSN 需使用 SecretStr |
| 环境变量隔离 | ✅ 通过 | 支持 .env 文件 |
| 配置文件权限 | ❌ 待补充 | 需添加权限说明 |
| 日志脱敏 | ❌ 待改进 | SQL 查询需脱敏 |
| 输入验证边界 | ⚠️ 部分通过 | 需补充连接池参数验证 |
| 依赖安全扫描 | ❌ 缺失 | 建议添加 safety/pip-audit |

---

## 3. 安全改进建议

### 3.1 添加安全扫描工具

```toml
# pyproject.toml
[project.optional-dependencies]
security = [
    "safety>=2.3.0",
    "pip-audit>=2.6.0",
    "bandit>=1.7.0",
]
```

### 3.2 添加安全扫描命令

```bash
# 依赖漏洞扫描
safety check -r requirements.txt
pip-audit -r requirements.txt

# 代码安全扫描
bandit -r src/
```

### 3.3 安全配置模板

```bash
# .env.security (新增，用于参考)
# 安全配置示例 - 不要提交到版本控制！

# 数据库连接必须使用环境变量
export DB_DSN="oracle://user:password@host:1521/ORCL"

# 文件权限设置
chmod 600 .env
chmod 600 config/settings.yaml
```

---

## 4. 安全评审结论

| 项目 | 状态 | 说明 |
|------|------|------|
| 敏感数据保护 | ❌ 待修复 | DSN 需加密 |
| 日志脱敏 | ❌ 待修复 | SQL 需脱敏 |
| 配置权限 | ❌ 待补充 | 需文档说明 |
| 参数验证 | ⚠️ 待加强 | 边界检查 |
| 安全扫描 | ❌ 待添加 | 需工具集成 |

---

*评审日期：2026-03-06*
