# Phase 2: Oracle 数据库连接模块设计评审

**评审日期**: 2026-03-06
**评审文件**: docs/plan/phase-2/01-database-connection.md
**评审版本**: 1.0

---

## 一、总体评价

该设计文档基本完整，包含了连接池管理、配置和健康检查三大核心模块。但存在若干需要改进的问题，主要集中在高并发支持、错误处理机制和配置扩展性方面。

---

## 二、详细评审

### 1. 连接池设计 (CRITICAL)

**问题 1.1: DSN 解析方式不合理** (CRITICAL)
- **位置**: `connection.py` 第 82-84 行
- **问题**: 使用字符串分割方式解析 DSN，代码脆弱且容易出错
- **建议**: 直接调用 `DatabaseConfig.to_oracledb_params()` 方法获取连接参数

```python
# 当前代码 (不推荐)
dsn=db_config.get_dsn().split("@")[1] if "@" in db_config.get_dsn() else ...

# 建议修改
db_config = get_database_config()
oracledb_params = db_config.to_oracledb_params()
self._pool = oracledb.create_pool(**oracledb_params, ...)
```

**问题 1.2: 缺少连接验证配置** (HIGH)
- **问题**: 未设置连接获取时的验证机制，可能获取到已断开的连接
- **建议**: 添加 `connection_validated` 参数或在获取连接后进行有效性检查

```python
# 建议添加
self._pool = oracledb.create_pool(
    ...
    getmode=oracledb.POOL_GETMODE_WAIT,
    connection_validated=False,  # 获取时验证连接
)
```

**问题 1.3: 缺少连接生命周期管理** (MEDIUM)
- **问题**: 没有设置连接最大生存时间，可能导致连接长期占用
- **建议**: 添加 `max_lifetime` 配置参数

---

### 2. 高并发场景支持 (HIGH)

**问题 2.1: 默认最大连接数过低** (HIGH)
- **位置**: 配置默认值 `max_connections=10`
- **问题**: 默认值无法满足高并发场景需求
- **建议**:
  - 提高默认值到 20-50
  - 添加根据 CPU 核心数自动计算的逻辑
  - 在文档中明确说明如何根据并发量调整

**问题 2.2: 缺少连接池耗尽处理机制** (HIGH)
- **位置**: `connection.py` 第 113-115 行
- **问题**: 获取连接失败时直接抛出异常，没有重试或等待机制
- **建议**: 添加重试逻辑和指数退避

```python
# 建议添加获取连接重试逻辑
def get_connection(self, max_retries: int = 3, retry_delay: float = 0.1) -> oracledb.Connection:
    for attempt in range(max_retries):
        try:
            return self._pool.acquire()
        except oracledb.Error as e:
            if attempt == max_retries - 1:
                raise PoolExhaustedException(detail={"reason": str(e)})
            time.sleep(retry_delay * (2 ** attempt))  # 指数退避
```

**问题 2.3: 阻塞模式获取连接** (MEDIUM)
- **位置**: `getmode=oracledb.POOL_GETMODE_WAIT`
- **问题**: 使用阻塞等待模式，高并发时可能导致请求堆积
- **建议**: 考虑支持 `POOL_GETMODE_NO_WAIT` 或添加超时控制

---

### 3. 错误处理和重试机制 (HIGH)

**问题 3.1: 缺少连接重试机制** (HIGH)
- **问题**: 对于瞬时故障（如网络抖动、数据库暂时不可用）没有重试
- **建议**: 实现指数退避重试装饰器或上下文管理器

**问题 3.2: 缺少熔断器模式** (HIGH)
- **问题**: 数据库故障时，所有请求都会直接失败
- **建议**: 实现 Circuit Breaker 模式，在连续失败后暂停请求一段时间

**问题 3.3: 健康检查无重试** (MEDIUM)
- **位置**: `health.py` 第 283-320 行
- **问题**: 健康检查失败时直接返回失败，没有重试验证
- **建议**: 添加重试机制，避免误报

---

### 4. 健康检查机制 (MEDIUM)

**问题 4.1: 缺少检查结果缓存** (MEDIUM)
- **位置**: `health.py` 每次调用 `check()` 都执行实际查询
- **问题**: 频繁调用会增加数据库负载
- **建议**: 添加缓存机制，支持配置检查间隔

```python
# 建议添加
@dataclass
class HealthChecker:
    check_interval_seconds: int = 30  # 可配置

    def check(self) -> HealthStatus:
        # 如果距离上次检查小于间隔，直接返回缓存结果
        if self.last_check_time:
            elapsed = (datetime.now() - self.last_check_time).total_seconds()
            if elapsed < self.check_interval_seconds:
                return self.last_status
        # ... 执行实际检查
```

**问题 4.2: 缺少连接池统计信息** (MEDIUM)
- **问题**: 健康检查只返回连接是否可用，没有暴露连接池状态
- **建议**: 扩展 HealthStatus 包含连接池统计

```python
@dataclass
class HealthStatus:
    ...
    pool_stats: Optional[dict] = None  # 连接池统计
```

**问题 4.3: 浅层健康检查** (LOW)
- **问题**: 只执行 `SELECT 1 FROM DUAL`，无法检测更深层的数据库问题
- **建议**: 可选地执行更全面的检查（如检查表空间、会话数等）

---

### 5. 配置管理 (MEDIUM)

**问题 5.1: 配置项不够完善** (MEDIUM)
- **缺少配置项**:
  - `connection_max_lifetime` - 连接最大生存时间
  - `health_check_interval` - 健康检查间隔
  - `health_check_timeout` - 健康检查超时
  - `retry_max_attempts` - 最大重试次数
  - `retry_base_delay` - 重试基础延迟

**问题 5.2: 配置来源单一** (LOW)
- **问题**: 目前只支持从 settings 读取
- **建议**: 预留支持环境变量覆盖的接口

---

## 三、改进建议汇总

| 优先级 | 问题 | 建议 |
|--------|------|------|
| CRITICAL | DSN 解析方式不合理 | 使用 `DatabaseConfig.to_oracledb_params()` |
| HIGH | 默认最大连接数过低 | 提高默认值或添加自动计算逻辑 |
| HIGH | 缺少连接获取重试机制 | 添加指数退避重试 |
| HIGH | 缺少熔断器模式 | 实现 Circuit Breaker |
| MEDIUM | 缺少连接验证配置 | 添加 `connection_validated` |
| MEDIUM | 健康检查缺少缓存 | 添加可配置的检查间隔 |
| MEDIUM | 配置项不够完善 | 添加更多可配置参数 |
| LOW | 配置来源单一 | 预留环境变量支持 |

---

## 四、验收标准补充建议

在原验收标准基础上，建议补充：

- [ ] DSN 解析使用标准方法而非字符串分割
- [ ] 连接获取支持重试机制
- [ ] 健康检查支持缓存和配置间隔
- [ ] 连接池配置可通过环境变量覆盖
- [ ] 单元测试覆盖连接池核心路径

---

## 五、结论

**评审结果**: 需要修改 (REVIEW REQUIRED)

该设计文档在连接池基础功能上是完整的，但在高并发支持、错误处理机制和配置扩展性方面存在不足。建议按照上述评审意见进行修改后重新评审。

---

*评审人: Claude Code*
*评审日期: 2026-03-06*
