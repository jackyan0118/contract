# Phase-6 API 设计文档专家评审报告

**评审日期**: 2026-03-10

**评审文件**: docs/plan/phase-6/README.md

**评审专家**:
- 架构专家 (architect)
- Python 代码专家 (python-reviewer)

---

## 一、评审结论

| 评审项 | 状态 | 说明 |
|--------|------|------|
| API 架构设计 | ⚠️ 需改进 | 响应格式不统一 |
| 接口设计 | ⚠️ 需改进 | 输入验证不足 |
| 安全性 | ❌ 需修复 | 缺少认证授权 |
| 代码质量 | ✅ 基本通过 | 需补充实现细节 |

---

## 二、发现的问题

### 问题 1: 安全性 - 缺少认证授权 [严重]

| 现状 | 风险 |
|------|------|
| 文档中未提及任何认证/授权机制 | 任意人均可生成/查询报价单文件 |

**建议修复**:
```python
# 添加 API Key 认证
POST /api/v1/generate
Authorization: Bearer <api_key>
```

---

### 问题 2: 响应格式不统一 [中等]

| 问题 | 说明 |
|------|------|
| 单文件生成接口存在两种响应方式 | 文档给定了文件流和 Base64 两种方案 |

**建议**: 统一为 JSON 返回 Base64 方式

---

### 问题 3: 输入验证不足 [中等]

| 字段 | 问题 | 建议 |
|------|------|------|
| wybs | 未定义格式 | 正则 `^[A-Z0-9_-]+$` |
| wybs | 未定义长度 | 建议 50 字符内 |
| wybs_list | 未处理重复 | 应去重或拒绝重复 |
| wybs_list | 未处理空列表 | 应拒绝空列表 |

---

### 问题 4: 限流参数缺失 [中等]

**现状**: 文档提到限流中间件，但未定义具体参数

**建议补充**:
```yaml
# config/settings.yaml
rate_limit:
  default: "100/minute"
  generate: "20/minute"
  batch: "5/minute"
```

---

### 问题 5: 错误码体系不完整 [低]

| 问题 | 说明 |
|------|------|
| 只列出 VALIDATION_ERROR | 缺少业务错误码（报价单不存在、模板匹配失败等） |

---

### 问题 6: 任务队列持久化 [低]

| 问题 | 说明 |
|------|------|
| 内存队列重启后任务丢失 | 生产环境需要 Redis 持久化 |

---

## 三、代码质量评审

### 架构设计 - 良好

| 评估项 | 状态 |
|--------|------|
| 路由结构 | ✅ 清晰，使用 APIRouter 模块化 |
| 中间件设计 | ✅ 完整（4个中间件） |
| 响应格式 | ✅ 统一使用 ApiResponse[T] 泛型 |

### 需补充的实现细节

| 项目 | 建议 |
|------|------|
| Pydantic 模型 | 补充 GenerateRequest, BatchRequest 等具体定义 |
| 依赖注入 | 明确 service 层注入方式 |
| 配置加载 | 补充 Config 类设计 |
| 异常集成 | 添加与现有 AppException 体系的整合说明 |

---

## 四、改进建议（按优先级）

### P0 (必须修复)

1. **添加基础认证机制** (API Key)
2. **完善输入验证** (wybs 格式、长度)
3. **统一响应格式** (统一使用 JSON Base64)

### P1 (强烈建议)

4. **补充限流参数配置**
5. **定义完整错误码体系**
6. **补充任务超时机制**

### P2 (可选优化)

7. 模板指定参数
8. 日志脱敏处理
9. 健康检查增加更多指标

---

## 五、风险评估

| 风险项 | 等级 | 影响 |
|--------|------|------|
| 无认证授权 | 🔴 高 | 数据泄露、滥用 |
| 输入验证不足 | 🟡 中 | 异常崩溃 |
| 限流参数缺失 | 🟡 中 | DoS 风险 |
| 响应格式不统一 | 🟡 中 | 前端兼容困难 |
| 内存队列生产不可用 | 🟡 中 | 任务丢失 |

---

## 六、建议的改进方案

### 1. 响应格式统一

```python
# 统一为 JSON 返回 Base64
class GenerateResponse(BaseModel):
    success: bool
    data: Optional[GenerateData]
    error: Optional[ErrorDetail]
    request_id: str  # 用于日志追踪
```

### 2. 认证方案

```
内部系统 → API Key (简单)
需要用户级权限 → JWT
```

### 3. 输入验证

```python
class GenerateRequest(BaseModel):
    wybs: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9_-]+$")
```

### 4. 错误码体系

```python
class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    QUOTE_NOT_FOUND = "QUOTE_NOT_FOUND"
    TEMPLATE_NOT_MATCHED = "TEMPLATE_NOT_MATCHED"
    GENERATION_FAILED = "GENERATION_FAILED"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_CANCELLED = "TASK_CANCELLED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

---

## 七、总结

**评审结论**: ⚠️ 需修改后实施

**主要问题**:
1. 安全性缺失（认证授权）
2. 响应格式不统一
3. 输入验证不足

**建议**:
- 实施前先修复 P0 问题
- 补充实现细节文档
- 生产环境需添加 Redis 持久化

---

*评审完成时间: 2026-03-10*
