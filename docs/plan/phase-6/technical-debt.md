# Phase 6 技术债务优化设计

本文档详细设计 Phase 6 待优化项的技术方案。

---

## 1. 同步调用阻塞事件循环 (P1)

### 问题描述

当前实现中，async 函数内部使用了同步数据库调用（python-oracledb 同步 API），导致阻塞事件循环，影响并发性能。

### 根因分析

```python
# 当前问题代码示例
async def get_quote(wybs: str):
    # 同步调用会阻塞事件循环
    result = await database.fetch_one(query)  # 实际上是同步调用
```

### 解决方案

**方案 A: 使用异步数据库驱动**

```python
# 方案 A: 使用 oracledb 异步模式
import oracledb
from typing import Optional, Any
import asyncio

async def get_quote(wybs: str) -> Optional[dict[str, Any]]:
    """异步获取报价单数据"""
    connection = None
    cursor = None
    try:
        connection = await oracledb.connect_async(dsn=DSN)
        cursor = await connection.cursor()
        await cursor.execute(query, wybs=wybs)
        return await cursor.fetchone()
    finally:
        if cursor:
            await cursor.close()
        if connection:
            await connection.close()
```

**方案 B: 使用 run_in_executor (保守方案)**

```python
# 方案 B: 将同步调用放入线程池
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio

_executor: Optional[ThreadPoolExecutor] = None

def get_executor() -> ThreadPoolExecutor:
    """获取线程池单例"""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=10)
    return _executor

async def get_quote(wybs: str) -> Optional[dict[str, Any]]:
    """在线程池中执行同步数据库查询"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_executor(), sync_db_query, wybs)
```

### 推荐方案

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 方案 A | 真正异步，性能最佳 | 需要修改查询层 | 生产环境推荐 |
| 方案 B | 改动小 | 仍有线程开销 | 快速修复 |

### 实施步骤

1. **方案 B（快速修复）**:
   - 创建 `run_in_executor` 工具函数
   - 封装数据库调用
   - 配置线程池大小

2. **方案 A（长期方案）**:
   - 评估 oracledb 异步模式兼容性
   - 重构 `src/database/` 模块
   - 更新连接池为异步版本

### 工作量估算

- 方案 B: 0.5 天
- 方案 A: 2-3 天

---

## 2. 规则重复加载 (P2) ⚠️ 已关闭

### 评审结论

**此问题已关闭，无需优化。**

查看现有代码 `src/services/rule_loader.py`：
- 规则已经缓存在内存中 (`self._rules`)
- 支持热更新 (使用 `watchdog` 监听文件变化)
- 每次请求调用 `get_rules()` 返回的是内存缓存，不是重新加载

---

## 3. 任务访问控制缺失 (P2)

### 问题描述

任务 ID 未与用户绑定，任何持有有效 API Key 的用户都可以查询任意任务状态，存在数据泄露风险。

### 问题场景

```
用户 A 创建任务 task_123
用户 B（不同 API Key）调用 GET /api/v1/tasks/task_123
→ 返回任务详情（不应该允许）
```

### 解决方案

**方案 A: 任务与用户绑定 (推荐)**

```python
# src/api/routes/tasks.py
from fastapi import Depends, Request
from typing import Optional

async def get_task_status(
    task_id: str,
    request: Request,
    auth_service: AuthService = Depends()
) -> Task:
    # 获取当前用户身份
    current_user: Optional[dict] = getattr(request.state, "user", None)
    if not current_user:
        raise HTTPException(status_code=401, detail="未认证")

    # 获取任务
    task = await task_manager.get_task(task_id)

    # 检查权限
    if task.user_id != current_user.get("api_key_id"):
        raise HTTPException(status_code=403, detail="无权访问此任务")

    return task
```

**数据模型变更**：

```python
# src/api/tasks/models.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    task_id: str
    user_id: str  # 新增：绑定用户
    status: TaskStatus
    wybs_list: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total: int = 0
    processed: int = 0
    failed: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
```

### 实施步骤

1. 修改 `Task` 模型，添加 `user_id` 字段
2. 修改任务创建逻辑，注入当前用户 ID
3. 修改任务查询逻辑，增加权限校验
4. 任务清理时按用户隔离

### 工作量估算

0.5 天

---

## 4. 限流器内存泄漏 (P3) ⚠️ 已关闭

### 评审结论

**此问题已关闭，无需优化。**

查看现有代码 `src/api/middleware/rate_limit.py`：
- 每次 `is_allowed()` 调用都会清理过期数据
- 不存在内存泄漏问题

```python
def is_allowed(self, key: str, limit: RateLimitConfig, whitelist: list[str]) -> bool:
    now = time.time()
    window_start = now - limit.window

    with self._lock:
        # 每次调用都会清理过期的请求记录
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        # ...
```

---

## 5. 生产环境 Redis 持久化 (P2)

### 问题描述

当前使用内存队列，重启后任务丢失。生产环境需要 Redis 持久化。

### 解决方案

**架构设计**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Redis     │────▶│  Worker(s)  │
│  (Producer) │     │  (Queue)    │     │ (Consumer)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   ▼                   │
       │            ┌─────────────┐            │
       └───────────▶│   Redis     │◀──────────┘
                    │ (Task State)│
                    └─────────────┘
```

### Redis 数据结构设计

```python
# 任务队列
KEY: "tasks:queue"
VALUE: List[task_id]

# 任务状态 (Hash)
KEY: "task:{task_id}"
FIELDS:
  - task_id: str
  - user_id: str
  - status: str  # pending/processing/completed/failed
  - wybs_list: str  # JSON
  - result: str  # JSON (完成后存储)
  - created_at: timestamp
  - updated_at: timestamp
  - progress: int
  - total: int
  - processed: int
  - failed: int

# 分布式锁 (防止重复消费)
KEY: "lock:task:{task_id}"
VALUE: "1"
OPTIONS: NX EX 300  # 5分钟超时
```

### 实现代码

```python
# src/api/tasks/redis_manager.py
import redis.asyncio as redis
import json
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    task_id: str
    user_id: str
    status: TaskStatus
    wybs_list: list[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total: int = 0
    processed: int = 0
    failed: int = 0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None

class RedisTaskManager:
    """基于 Redis 的任务管理器"""

    def __init__(self, redis_url: str):
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._queue_key = "tasks:queue"
        self._task_prefix = "task:"
        self._lock_prefix = "lock:task:"

    async def create_task(self, task: Task) -> str:
        """创建任务"""
        task_key = f"{self._task_prefix}{task.task_id}"
        task.total = len(task.wybs_list)

        # 存储任务详情
        await self._redis.hset(task_key, mapping={
            "task_id": task.task_id,
            "user_id": task.user_id,
            "status": task.status.value,
            "wybs_list": json.dumps(task.wybs_list),
            "created_at": task.created_at.isoformat(),
            "progress": str(task.progress),
            "total": str(task.total),
            "processed": "0",
            "failed": "0"
        })

        # 加入队列
        await self._redis.rpush(self._queue_key, task.task_id)

        # 设置过期时间（7天）
        await self._redis.expire(task_key, 7 * 24 * 3600)

        return task.task_id

    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        task_key = f"{self._task_prefix}{task_id}"
        data = await self._redis.hgetall(task_key)

        if not data:
            return None

        return Task(
            task_id=data["task_id"],
            user_id=data["user_id"],
            status=TaskStatus(data["status"]),
            wybs_list=json.loads(data["wybs_list"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            progress=int(data.get("progress", 0)),
            total=int(data.get("total", 0)),
            processed=int(data.get("processed", 0)),
            failed=int(data.get("failed", 0)),
        )

    async def acquire_task_lock(self, task_id: str, timeout: int = 300) -> bool:
        """获取任务处理锁（分布式锁）"""
        lock_key = f"{self._lock_prefix}{task_id}"
        # SET NX EX - 仅在不存在时设置，5分钟超时
        result = await self._redis.set(lock_key, "1", nx=True, ex=timeout)
        return result is not None

    async def release_task_lock(self, task_id: str):
        """释放任务处理锁"""
        lock_key = f"{self._lock_prefix}{task_id}"
        await self._redis.delete(lock_key)

    async def update_progress(self, task_id: str, processed: int = 0, failed: int = 0):
        """更新进度"""
        task_key = f"{self._task_prefix}{task_id}"
        if processed:
            await self._redis.hincrby(task_key, "processed", processed)
        if failed:
            await self._redis.hincrby(task_key, "failed", failed)

    async def pop_task(self) -> Optional[str]:
        """从队列取任务（阻塞）"""
        # 使用 BRPOP 实现阻塞取队列
        result = await self._redis.blpop(self._queue_key, timeout=5)
        if result:
            return result[1]
        return None
```

### Worker 消费逻辑

```python
# src/workers/task_worker.py
import asyncio
from typing import Optional

async def process_tasks(manager: RedisTaskManager):
    """任务消费者"""
    while True:
        task_id = await manager.pop_task()
        if not task_id:
            continue

        # 尝试获取分布式锁（防止重复消费）
        if not await manager.acquire_task_lock(task_id):
            # 获取锁失败，说明任务已被其他 Worker 处理
            continue

        try:
            # 获取任务详情
            task = await manager.get_task(task_id)
            if not task or task.status == TaskStatus.CANCELLED:
                continue

            # 更新状态为处理中
            task_key = f"task:{task_id}"
            await manager._redis.hset(task_key, "status", TaskStatus.PROCESSING.value)

            # 处理任务
            try:
                result = await process_quote_batch(task.wybs_list)
                await manager._redis.hset(task_key, mapping={
                    "status": TaskStatus.COMPLETED.value,
                    "result": json.dumps(result),
                    "completed_at": datetime.now().isoformat()
                })
            except Exception as e:
                # 更新失败状态
                await manager._redis.hset(task_key, mapping={
                    "status": TaskStatus.FAILED.value,
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                })
        finally:
            # 释放锁
            await manager.release_task_lock(task_id)
```

### 与现有 Oracle 连接池集成

```python
# src/workers/task_worker.py - 复用现有连接池
from src.database.connection import DatabaseConnectionPool

class TaskWorker:
    def __init__(self, redis_manager: RedisTaskManager):
        self.redis = redis_manager
        self.db_pool = DatabaseConnectionPool()  # 复用现有连接池

    async def process_batch(self, wybs_list: list[str]) -> dict:
        """处理报价单批次"""
        results = []
        for wybs in wybs_list:
            # 复用现有数据库连接
            with self.db_pool.get_connection() as conn:
                # 查询和处理逻辑
                result = await self.query_and_process(wybs)
                results.append(result)
        return {"results": results, "total": len(results)}
```

### 配置设计

```yaml
# config/settings.yaml
redis:
  url: "redis://localhost:6379/0"
  task:
    queue_key: "tasks:queue"
    result_ttl: 604800  # 7天
    lock_timeout: 300   # 5分钟

# 生产环境
production:
  redis:
    url: "redis://redis-prod:6379/0"
    password: "${REDIS_PASSWORD}"
```

### 实施步骤

1. 安装 `redis-py` 异步客户端
2. 创建 `RedisTaskManager` 类（支持分布式锁）
3. 修改 `TaskManager` 接口，支持内存/Redis 切换
4. 添加 Worker 消费脚本
5. 配置生产环境 Redis 连接
6. 集成现有 Oracle 连接池

### 工作量估算

2 天

---

## 总结

| 序号 | 问题 | 优先级 | 解决方案 | 工作量 | 状态 |
|------|------|--------|----------|--------|------|
| 6.11 | 同步调用阻塞事件循环 | P1 | run_in_executor 或异步改造 | 0.5-3天 | 待实施 |
| 6.12 | 规则重复加载 | P2 | - | - | ⚠️ 已关闭 |
| 6.13 | 任务访问控制缺失 | P2 | user_id 绑定 + 权限校验 | 0.5天 | 待实施 |
| 6.14 | 限流器内存泄漏 | P3 | - | - | ⚠️ 已关闭 |
| 6.15 | Redis 持久化 | P2 | Redis 队列 + Hash + 分布式锁 | 2天 | 待实施 |

**有效工作量**: 约 2.5-5 天（关闭 2 个无需优化的问题后）

---

## 专家评审反馈

### 评审发现

1. **规则重复加载 (P2)** - 已有缓存实现，无需优化
2. **限流器内存泄漏 (P3)** - 已有清理逻辑，无需优化
3. **Redis 方案** - 需补充分布式锁、与现有 Oracle 连接池集成

### 改进建议

| 优先级 | 建议 |
|--------|------|
| P0 | 添加 Redis 分布式锁防止重复消费 |
| P0 | 说明与 `src/database/connection.py` 的集成 |
| P1 | 添加任务重试机制 |
| P2 | 考虑结果数据持久化到 Oracle |

---

*文档版本：1.1*
*创建时间：2026-03-10*
*评审完成时间：2026-03-10*
