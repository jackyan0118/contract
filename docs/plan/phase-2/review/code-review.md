# Code Review: Oracle 数据库连接模块

**评审文件**: `docs/plan/phase-2/01-database-connection.md`
**评审日期**: 2026-03-06
**评审结果**: 需要修改 (存在 HIGH 级别问题)

---

## 总体评价

代码整体结构清晰，遵循了模块化设计原则，采用了单例模式管理连接池。但存在**严重的设计缺陷**和**代码重复问题**，需要重构后才能实施。

---

## CRITICAL 问题

### 1. DSN 解析方式存在严重缺陷

**文件**: `src/database/connection.py:82-84`

```python
self._pool = oracledb.create_pool(
    user=db_config.get_dsn().split("//")[1].split("@")[0].split(":")[0],
    password=db_config.get_dsn().split("//")[1].split("@")[0].split(":")[1] if "@" in db_config.get_dsn() else "",
    dsn=db_config.get_dsn().split("@")[1] if "@" in db_config.get_dsn() else db_config.get_dsn(),
    ...
)
```

**问题**:
- 使用字符串分割解析 DSN极易出错，无法处理复杂场景
- 如果密码包含特殊字符（如 `@`, `:`, `/`），会导致解析错误
- 无法处理 URL 编码的密码
- `config.py:221-230` 存在完全相同的重复代码

**修复建议**:
使用 `urllib.parse.urlparse` 或 `DatabaseConfig.to_oracledb_params()` 方法：

```python
# 推荐：在 connection.py 中使用 config.py 已有的解析方法
from src.database.config import get_database_config

db_config = get_database_config()
oracledb_params = db_config.to_oracledb_params()
self._pool = oracledb.create_pool(
    **oracledb_params,
    min=db_config.min_connections,
    max=db_config.max_connections,
    ...
)
```

---

### 2. 游标未使用上下文管理器

**文件**:
- `src/database/connection.py:156-158`
- `src/database/health.py:293-296`

```python
cursor = conn.cursor()
cursor.execute("SELECT 1 FROM DUAL")
cursor.fetchone()
cursor.close()
```

**问题**:
- 如果 `execute` 或 `fetchone` 抛出异常，`cursor.close()` 不会执行
- Oracle 游标是宝贵资源，应该确保释放

**修复建议**:
```python
with conn.cursor() as cursor:
    cursor.execute("SELECT 1 FROM DUAL")
    cursor.fetchone()
```

---

## HIGH 问题

### 3. 数据库凭据可能泄露到日志

**文件**: `src/database/connection.py:93-99`

```python
logger.info(
    "数据库连接池初始化成功",
    context={
        "min_connections": db_config.min_connections,
        "max_connections": db_config.max_connections,
    },
)
```

**问题**:
- 虽然当前日志内容不包含密码，但 DSN 解析过程可能因异常而记录敏感信息
- 如果 `db_config.get_dsn()` 被错误地包含在日志中，会导致凭据泄露

**修复建议**:
确保日志中不包含任何 DSN 信息，使用结构化日志时明确排除敏感字段。

---

### 4. 缺少返回类型注解

**文件**:
- `src/database/connection.py:169` - `get_connection_pool()`
- `src/database/config.py:243` - `get_database_config()`
- `src/database/health.py:327` - `check_database_health()`

**问题**:
- 公共函数缺少类型注解不符合项目规范

**修复建议**:
```python
def get_connection_pool() -> ConnectionPool:
def get_database_config() -> DatabaseConfig:
def check_database_health() -> HealthStatus:
```

---

### 5. import 语句位置不规范

**文件**: `src/database/health.py:286`

```python
def check(self) -> HealthStatus:
    from src.database.connection import get_connection_pool
    import time
    ...
```

**问题**:
- `import time` 放在函数内部不是 Python 最佳实践
- 顶层导入应该在文件顶部

**修复建议**:
将 `import time` 移到文件顶部

---

## MEDIUM 问题

### 6. 代码重复

**问题**: DSN 解析逻辑在 `connection.py` 和 `config.py` 中重复实现

**修复建议**: `connection.py` 应该复用 `DatabaseConfig.to_oracledb_params()` 方法

---

### 7. 健康检查未使用游标上下文管理器

**文件**: `src/database/health.py:293-296`

**问题**: 与 issue #2 相同

**修复建议**: 使用 `with conn.cursor() as cursor:`

---

### 8. 连接池单例初始化可改进

**文件**: `src/database/connection.py:169-178`

```python
def get_connection_pool() -> ConnectionPool:
    global _connection_pool

    if _connection_pool is None:
        with _pool_lock:
            if _connection_pool is None:
                _connection_pool = ConnectionPool()

    return _connection_pool
```

**问题**:
- 当前实现使用了双重检查锁定模式（Double-Checked Locking），但 `ConnectionPool` 的 `initialize()` 方法也有类似的逻辑
- 可能导致连接池被初始化两次

**修复建议**: 考虑在 `get_connection_pool()` 中直接调用 `initialize()`，或在 `ConnectionPool` 内部统一管理初始化逻辑

---

## 代码风格检查 (PEP 8)

- 整体缩进和空格符合 PEP 8
- 行长度控制在合理范围内
- 模块 docstring 格式正确
- 建议：添加更多详细的 docstring 说明参数和返回值

---

## 安全性检查

| 检查项 | 状态 |
|--------|------|
| SQL 注入 | 无风险（使用硬编码查询） |
| 凭据泄露 | 需注意日志配置 |
| 命令注入 | 无风险 |
| 弱加密 | 无风险 |

---

## 建议的修复优先级

1. **立即修复**: DSN 解析逻辑（使用 config.py 的方法）
2. **立即修复**: 游标上下文管理器
3. **高优先级**: 添加返回类型注解
4. **中优先级**: 整理 import 语句位置
5. **低优先级**: 代码注释完善

---

## 结论

**评审结论**: 不推荐实施

**原因**: 存在 CRITICAL 级别的 DSN 解析缺陷，会导致：
- 无法正确处理包含特殊字符的密码
- 代码重复，维护困难
- 潜在的凭据泄露风险

**下一步**: 请根据本评审意见修改设计文档中的代码实现，重点修复 DSN 解析和游标管理问题。
