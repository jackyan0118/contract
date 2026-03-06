# Phase 2: Oracle 数据库连接模块安全评审

**评审日期**: 2026-03-06
**评审文件**: docs/plan/phase-2/01-database-connection.md
**评审类型**: 安全专项评审
**评审版本**: 1.0

---

## 一、评审概述

本评审聚焦于该设计文档的安全相关问题，重点关注凭据管理、信息泄露风险、访问控制和常见安全漏洞。

---

## 二、安全问题详细分析

### 1. 凭据管理问题 (CRITICAL)

#### 问题 1.1: 密码通过 DSN 字符串解析传递 (CRITICAL)

**位置**: `connection.py` 第 82-84 行

```python
self._pool = oracledb.create_pool(
    user=db_config.get_dsn().split("//")[1].split("@")[0].split(":")[0],
    password=db_config.get_dsn().split("//")[1].split("@")[0].split(":")[1] if "@" in db_config.get_dsn() else "",
    dsn=db_config.get_dsn().split("@")[1] if "@" in db_config.get_dsn() else db_config.get_dsn(),
    ...
)
```

**风险分析**:
- 密码以明文形式在代码中进行字符串操作
- 这种解析方式容易出错且难以维护
- DSN 格式变化可能导致密码解析错误

**建议修复**:
```python
# 使用已存在的 to_oracledb_params() 方法
db_config = get_database_config()
oracledb_params = db_config.to_oracledb_params()
oracledb_params.update({
    "min": db_config.min_connections,
    "max": db_config.max_connections,
    "increment": db_config.pool_increment,
    "timeout": db_config.connect_timeout,
    "wait_timeout": db_config.command_timeout * 1000,
    "getmode": oracledb.POOL_GETMODE_WAIT,
})
self._pool = oracledb.create_pool(**oracledb_params)
```

---

### 2. 凭据泄露风险 (CRITICAL)

#### 问题 2.1: 错误日志可能泄露数据库敏感信息 (CRITICAL)

**位置**: `connection.py` 第 101 行

```python
except oracledb.Error as e:
    logger.error(f"数据库连接池初始化失败：{e}")
    raise ConnectionException(reason=str(e))
```

**风险分析**:
- `str(e)` 可能包含数据库版本、连接地址、用户名等敏感信息
- 日志可能输出到文件或日志系统，存在信息泄露风险

**建议修复**:
```python
except oracledb.Error as e:
    logger.error("数据库连接池初始化失败", exc_info=True)
    # 使用通用错误消息，不暴露具体原因
    raise ConnectionException(reason="数据库连接失败，请检查配置")
```

#### 问题 2.2: 异常信息通过 API 泄露 (CRITICAL)

**位置**: `connection.py` 第 115 行

```python
raise PoolExhaustedException(detail={"reason": str(e)})
```

**风险分析**:
- 异常详情可能通过 API 响应返回给客户端
- 可能暴露数据库连接字符串、用户名等敏感信息

**建议修复**:
```python
except oracledb.Error as e:
    logger.error(f"获取数据库连接失败：{e}", exc_info=True)
    raise PoolExhaustedException(detail={"reason": "连接池获取失败"})
```

#### 问题 2.3: 健康检查错误信息泄露 (HIGH)

**位置**: `health.py` 第 313 行

```python
message=f"数据库连接异常：{str(e)}",
```

**风险分析**:
- 健康检查接口可能对外暴露，错误信息可能被攻击者利用

**建议修复**:
```python
message="数据库连接异常",
logger.error(f"数据库健康检查失败: {type(e).__name__}")
```

---

### 3. SQL 注入风险 (MEDIUM)

#### 问题 3.1: 动态 SQL 执行存在注入风险 (MEDIUM)

**位置**: `connection.py` 第 157 行、示例代码第 357 行

```python
cursor.execute("SELECT 1 FROM DUAL")
cursor.execute("SELECT * FROM table_name")  # 示例代码
```

**风险分析**:
- 虽然当前代码使用硬编码 SQL，但设计文档未明确要求使用参数化查询
- 实际使用时可能引入 SQL 注入漏洞

**建议修复**:
- 在文档中明确要求所有 SQL 使用参数化查询
- 禁止字符串拼接构建 SQL 语句
- 添加 SQL 注入检测的代码审查清单

---

### 4. 连接池访问控制 (MEDIUM)

#### 问题 4.1: 缺少连接池访问控制机制 (MEDIUM)

**问题分析**:
- 当前设计没有对连接池的访问进行权限控制
- 任何模块都可以直接获取连接池实例

**建议修复**:
```python
class ConnectionPool:
    def __init__(self):
        self._pool: Optional[oracledb.ConnectionPool] = None
        self._lock = threading.Lock()
        self._initialized = False
        self._allowed_roles: set = set()  # 添加角色控制

    def initialize(self, allowed_roles: Optional[set] = None) -> None:
        """初始化连接池，可指定允许访问的角色"""
        self._allowed_roles = allowed_roles or {"admin", "service"}
```

---

### 5. 其他安全问题

#### 问题 5.1: 缺少 TLS/SSL 加密传输配置 (MEDIUM)

**问题分析**:
- 文档未提及 Oracle 连接是否使用加密
- 生产环境应强制使用 TLS 加密

**建议修复**:
```python
# 添加加密配置选项
oracledb_params = db_config.to_oracledb_params()
oracledb_params["ssl=True"] = db_config.enable_ssl  # 添加 SSL 选项
```

#### 问题 5.2: 缺少连接池操作审计日志 (MEDIUM)

**问题分析**:
- 未记录连接获取、释放等敏感操作
- 无法追溯数据库访问行为

**建议修复**:
```python
def get_connection(self) -> oracledb.Connection:
    # 记录审计日志
    logger.audit(
        "获取数据库连接",
        context={
            "user": get_current_user(),  # 获取当前用户
            "trace_id": get_trace_id(),  # 获取追踪ID
        }
    )
    ...
```

#### 问题 5.3: 配置中密码以明文存储风险 (HIGH)

**位置**: `config.py` 第 217-236 行

```python
def to_oracledb_params(self) -> dict:
    # 解析 DSN
    parts = self.dsn.replace("oracle://", "").split("@")
    user_info = parts[0].split(":")
    ...
    password = user_info[1] if len(user_info) > 1 else ""
```

**风险分析**:
- 如果 DSN 存储在配置文件或环境变量中，密码以明文形式存在
- 建议使用安全的凭据存储机制

**建议**:
- 使用 Python 的 `keyring` 库或云服务提供的 Secret Manager
- 或使用 Oracle Wallet 存储凭据

---

## 三、安全问题汇总

| 优先级 | 问题 | 位置 | 建议 |
|--------|------|------|------|
| CRITICAL | 密码通过字符串解析传递 | connection.py:82-84 | 使用 to_oracledb_params() 方法 |
| CRITICAL | 错误日志泄露敏感信息 | connection.py:101 | 使用通用错误消息 |
| CRITICAL | API 异常泄露敏感信息 | connection.py:115 | 移除 detail 中的详细信息 |
| HIGH | 健康检查信息泄露 | health.py:313 | 使用通用错误消息 |
| HIGH | 密码明文存储风险 | config.py | 使用 Secret Manager |
| MEDIUM | SQL 注入风险 | 文档示例 | 明确要求参数化查询 |
| MEDIUM | 缺少访问控制 | 连接池设计 | 添加角色权限控制 |
| MEDIUM | 缺少 TLS 配置 | 连接配置 | 添加 SSL 选项 |
| MEDIUM | 缺少审计日志 | 全局 | 添加审计日志记录 |

---

## 四、安全修复建议代码示例

### 修复 1: 使用标准方法获取连接参数

```python
def initialize(self) -> None:
    """初始化连接池."""
    if self._initialized:
        return

    with self._lock:
        if self._initialized:
            return

        try:
            db_config = get_database_config()
            oracledb_params = db_config.to_oracledb_params()

            # 添加连接池配置
            oracledb_params.update({
                "min": db_config.min_connections,
                "max": db_config.max_connections,
                "increment": db_config.pool_increment,
                "timeout": db_config.connect_timeout,
                "wait_timeout": db_config.command_timeout * 1000,
                "getmode": oracledb.POOL_GETMODE_WAIT,
            })

            # 可选：启用 SSL
            if db_config.get("enable_ssl", False):
                oracledb_params["ssl"] = True
                oracledb_params["ssl_cert"] = db_config.get("ssl_cert_path")

            self._pool = oracledb.create_pool(**oracledb_params)
            self._initialized = True
            logger.info(
                "数据库连接池初始化成功",
                context={
                    "min_connections": db_config.min_connections,
                    "max_connections": db_config.max_connections,
                },
            )
        except oracledb.Error as e:
            logger.error("数据库连接池初始化失败", exc_info=True)
            raise ConnectionException(reason="数据库连接配置无效")
```

### 修复 2: 安全的事件处理

```python
def get_connection(self) -> oracledb.Connection:
    """获取数据库连接."""
    if not self._initialized:
        self.initialize()

    try:
        conn = self._pool.acquire()
        logger.debug("获取数据库连接成功")
        return conn
    except oracledb.Error as e:
        logger.error("获取数据库连接失败", exc_info=True)
        raise PoolExhaustedException(detail={"reason": "连接池获取失败"})
```

---

## 五、安全检查清单

在实现该模块时，请确保完成以下安全检查：

- [ ] 凭据不通过字符串解析传递
- [ ] 错误消息不包含敏感信息
- [ ] API 响应不泄露数据库详情
- [ ] 所有 SQL 使用参数化查询
- [ ] 生产环境启用 TLS 加密
- [ ] 添加连接池操作审计日志
- [ ] 实现连接池访问控制
- [ ] 使用安全的凭据存储方案

---

## 六、结论

**评审结果**: 需要修改 (REVIEW REQUIRED)

该设计文档存在多个严重的安全问题，主要集中在凭据管理和信息泄露方面。建议优先修复 CRITICAL 级别的问题后再进行开发。

---

*评审人: Claude Code (安全专项评审)*
*评审日期: 2026-03-06*
