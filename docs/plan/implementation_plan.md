# 价格附件生成系统 - 实施计划

## 1. 项目概述

### 1.1 项目背景
本项目旨在开发一个价格附件生成系统，该系统能够根据 Oracle 数据库中的价格清单数据，按照价格模板规则匹配到不同的模板，并自动生成 Word 价格附件。

### 1.2 核心流程
```
输入 (wybs 报价单号) -> Oracle 查询 -> 模板匹配 -> Word 生成 -> 输出文件
```

### 1.3 项目规模
- 模板数量：35 个 Word 模板
- 核心模块：5 个 (数据库连接、数据查询、模板匹配、Word 生成、API 接口)
- 预估工期：4 周
- 团队规模：2.5-3 人

### 1.4 技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 异步支持，高并发友好 |
| 数据库 | python-oracledb + SQLAlchemy | Oracle 连接池管理 |
| 文档处理 | python-docx | Word 文档生成 |
| 配置管理 | Pydantic Settings | 类型安全的配置管理 |
| 日志 | Python logging | 结构化日志 |
| 部署 | Docker + Docker Compose | 容器化部署 |
| 测试 | pytest + pytest-asyncio | 单元测试和集成测试 |

---

## 2. 实施阶段

### Phase 1: 项目基础设施搭建

**目标**: 建立项目骨架、配置管理、日志系统

**时间估算**: 2-3 天

**复杂度**: 低

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 1.1 | 创建项目目录结构 | `/src/`, `/config/`, `/tests/` | 目录结构 | 无 |
| 1.2 | 初始化 Python 项目配置 | `pyproject.toml`, `requirements.txt` | 依赖配置 | 1.1 |
| 1.3 | 配置管理模块开发 | `src/config/settings.py` | 配置加载器 | 1.1 |
| 1.4 | 日志系统搭建 | `src/utils/logger.py` | 日志模块 | 1.1 |
| 1.5 | 异常处理体系设计 | `src/exceptions/` | 自定义异常类 | 1.1 |
| 1.6 | 创建配置文件模板 | `config/settings.yaml.example` | 配置模板 | 1.3 |

#### 产出物清单
- [ ] 项目目录结构
- [ ] `pyproject.toml` / `requirements.txt`
- [ ] 配置管理模块 (`src/config/settings.py`)
- [ ] 日志模块 (`src/utils/logger.py`)
- [ ] 异常类定义 (`src/exceptions/__init__.py`)
- [ ] 配置文件模板 (`config/settings.yaml.example`)

#### 风险点
- 无重大风险

---

### Phase 2: Oracle 数据库连接模块

**目标**: 实现 Oracle 数据库连接池管理和基础查询能力

**时间估算**: 3-4 天

**复杂度**: 高

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 2.1 | Oracle SDK 集成测试 | `tests/test_oracle_connection.py` | 连接测试 | Phase 1 |
| 2.2 | 数据库连接池管理器 | `src/database/connection.py` | 连接池类 | 2.1 |
| 2.3 | 数据库配置验证 | `src/database/config.py` | 配置验证器 | 2.2 |
| 2.4 | 连接健康检查 | `src/database/health.py` | 健康检查 | 2.2 |
| 2.5 | 连接异常处理 | `src/exceptions/database.py` | 数据库异常 | 2.2 |
| 2.6 | 连接池单元测试 | `tests/test_connection_pool.py` | 测试用例 | 2.2 |

#### 产出物清单
- [ ] Oracle 连接池管理器 (`src/database/connection.py`)
- [ ] 数据库配置模块 (`src/database/config.py`)
- [ ] 健康检查模块 (`src/database/health.py`)
- [ ] 数据库异常类 (`src/exceptions/database.py`)
- [ ] 连接池单元测试

#### 风险点
- **风险**: Oracle 客户端依赖安装复杂
  - **缓解**: 使用 python-oracledb 的 Thin 模式，无需 Oracle Instant Client
- **风险**: 连接池参数调优困难
  - **缓解**: 提供可配置的连接池参数，默认值基于最佳实践
- **风险**: 网络不稳定导致连接中断
  - **缓解**: 实现连接重试机制和连接验证

---

### Phase 3: 数据查询模块

**目标**: 实现报价单数据查询和字段映射

**时间估算**: 3-4 天

**复杂度**: 中

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 3.1 | 数据模型定义 | `src/models/quotation.py` | 数据模型类 | Phase 2 |
| 3.2 | 字段映射配置 | `config/field_mapping.yaml` | 字段映射文件 | 3.1 |
| 3.3 | 报价单主表查询 | `src/queries/quotation.py` | 主表查询函数 | 3.1 |
| 3.4 | 报价单明细查询 | `src/queries/quotation_detail.py` | 明细查询函数 | 3.1 |
| 3.5 | 数据转换器 | `src/transformers/data_transformer.py` | 数据转换器 | 3.2, 3.3, 3.4 |
| 3.6 | 查询模块单元测试 | `tests/test_queries.py` | 测试用例 | 3.3, 3.4, 3.5 |

#### 产出物清单
- [ ] 数据模型定义 (`src/models/quotation.py`)
- [ ] 字段映射配置 (`config/field_mapping.yaml`)
- [ ] 报价单主表查询 (`src/queries/quotation.py`)
- [ ] 报价单明细查询 (`src/queries/quotation_detail.py`)
- [ ] 数据转换器 (`src/transformers/data_transformer.py`)
- [ ] 查询模块单元测试

#### 风险点
- **风险**: Oracle 表结构与文档不一致
  - **缓解**: 在开发初期进行表结构核对，创建字段映射文档
- **风险**: 字段名称变更风险
  - **缓解**: 使用配置化字段映射，便于后期维护

---

### Phase 4: 模板匹配引擎

**目标**: 实现智能模板匹配逻辑，支持 35 个模板的规则匹配

**时间估算**: 4-5 天

**复杂度**: 高

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 4.1 | 规则文件解析器 | `src/parsers/rule_parser.py` + `config/template_rules.yaml` | YAML 规则解析器（已转换） | Phase 3 |
| 4.2 | 模板规则模型 | `src/models/template_rule.py` | 规则数据模型 | 4.1 |
| 4.3 | 规则加载服务 | `src/services/rule_loader.py` | 规则加载服务 | 4.1, 4.2 |
| 4.4 | 模板匹配器 | `src/matchers/template_matcher.py` | 匹配引擎核心 | 4.2, 4.3 |
| 4.5 | 多模板匹配处理 | `src/matchers/multi_matcher.py` | 多模板处理 | 4.4 |
| 4.6 | 匹配结果模型 | `src/models/match_result.py` | 匹配结果模型 | 4.4 |
| 4.7 | 匹配引擎单元测试 | `tests/test_matcher.py` | 测试用例 | 4.4, 4.5, 4.6 |

#### 产出物清单
- [ ] 规则文件解析器 (`src/parsers/rule_parser.py`)
- [ ] 模板规则模型 (`src/models/template_rule.py`)
- [ ] 规则加载服务 (`src/services/rule_loader.py`)
- [ ] 模板匹配器 (`src/matchers/template_matcher.py`)
- [ ] 多模板处理器 (`src/matchers/multi_matcher.py`)
- [ ] 匹配结果模型 (`src/models/match_result.py`)
- [ ] 匹配引擎单元测试

#### 风险点
- **风险**: 规则复杂度导致匹配性能问题
  - **缓解**: 使用规则索引和缓存机制
- **风险**: 规则变更频繁
  - **缓解**: 规则外部化到 Excel，支持热加载
- **风险**: 边界条件处理不当
  - **缓解**: 完善的单元测试覆盖所有匹配场景

---

### Phase 5: Word 文档生成模块

**目标**: 实现 Word 模板读取和数据填充功能

**时间估算**: 4-5 天

**复杂度**: 高

#### 设计说明

**模板元数据配置**: 每个模板独立一个 YAML 文件在 `config/template_metadata/templates/`

```yaml
# config/template_metadata/templates/模板2.yaml 示例
id: "模板2"
name: "通用生化产品价格模版"
file: "templates/模板2.docx"

# Phase 4: 模板匹配条件
match_conditions:
  产品细分: "通用生化试剂"

# Phase 5: 明细表数据筛选规则（多组条件为 OR 关系）
detail_filter:
  condition_groups:
    - name: "规则1"
      conditions:
        - field: "CPXF"
          operator: "="
          value: "通用生化试剂"
        - field: "LYXH"
          operator: "="
          value: 2

# 表格列配置
table:
  placeholders:
    start: "{{#明细表}}"
    end: "{{/明细表}}"
  columns:
    - name: "序号"
      type: "auto_number"
    - name: "物料编码"
      source_field: "WLDM"

# 段落占位符
paragraph_placeholders:
  标题:
    value: "通用生化产品供货价"

# 话术配置（支持互斥组）
speeches:
  - id: "话术1.1"
    type: "conditional"
    mutex_group: "A"
    conditions:
      - field: "DJZMC"
        operator: "contains"
        value: "肝功"
    content: "话术内容..."
    variables:
      - name: "肝功扣率"
        default: "85"
```

**字段匹配规则**（支持双字段）:
- 数值类型 value → 匹配 ID 字段（如 DJZ, BNGHJLXZ）
- 字符串类型 value → 匹配名称字段（如 DJZMC）

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 5.1 | 模板元数据加载器 | `src/loaders/template_loader.py` | YAML 配置加载器 | Phase 4 |
| 5.2 | 条件表达式解析器 | `src/parsers/condition_parser.py` | 条件解析引擎 | 5.1 |
| 5.3 | 明细数据过滤器 | `src/filters/detail_filter.py` | 数据筛选器 | 5.2 |
| 5.4 | 字段映射层 | `src/mappers/field_mapper.py` | 字段名映射 | 5.3 |
| 5.5 | Word 模板读取器 | `src/readers/word_template_reader.py` | 模板读取器 | 5.1 |
| 5.6 | 表格结构分析器 | `src/analyzers/table_analyzer.py` | 表格分析器 | 5.5 |
| 5.7 | 数据填充引擎 | `src/fillers/data_filler.py` | 数据填充核心 | 5.3, 5.6 |
| 5.8 | 表格行扩展器 | `src/fillers/row_expander.py` | 动态行扩展 | 5.7 |
| 5.9 | 话术引擎 | `src/engines/speech_engine.py` | 话术匹配器 | 5.1, 5.3 |
| 5.10 | 格式保持器 | `src/fillers/format_preserver.py` | 格式保持 | 5.7 |
| 5.11 | 文档生成器 | `src/generators/document_generator.py` | 文档生成 | 5.8, 5.9, 5.10 |
| 5.12 | 文件打包器 | `src/utils/file_packer.py` | ZIP 打包 | 5.11 |
| 5.13 | Word 生成单元测试 | `tests/test_word_generator.py` | 测试用例 | 5.11, 5.12 |

#### 产出物清单
- [ ] 模板元数据加载器 (`src/loaders/template_loader.py`)
- [ ] 条件表达式解析器 (`src/parsers/condition_parser.py`)
- [ ] 明细数据过滤器 (`src/filters/detail_filter.py`)
- [ ] 字段映射层 (`src/mappers/field_mapper.py`)
- [ ] Word 模板读取器 (`src/readers/word_template_reader.py`)
- [ ] 表格结构分析器 (`src/analyzers/table_analyzer.py`)
- [ ] 数据填充引擎 (`src/fillers/data_filler.py`)
- [ ] 表格行扩展器 (`src/fillers/row_expander.py`)
- [ ] 话术引擎 (`src/engines/speech_engine.py`)
- [ ] 格式保持器 (`src/fillers/format_preserver.py`)
- [ ] 文档生成器 (`src/generators/document_generator.py`)
- [ ] 文件打包器 (`src/utils/file_packer.py`)
- [ ] Word 生成单元测试

#### 配置依赖
- `config/template_metadata/templates.yaml` - 模板引用主文件
- `config/template_metadata/templates/*.yaml` - 35个模板独立配置文件
- `docs/plan/phase-5/field_id_mapping.md` - 字段ID映射参考

#### 风险点
- **风险**: Word 模板格式不一致
  - **缓解**: 建立模板规范文档，模板验证器
- **风险**: 数据量过大导致性能问题
  - **缓解**: 分批处理，内存优化
- **风险**: 特殊字符导致文档损坏
  - **缓解**: 字符转义和编码处理
- **风险**: 字段ID与数据库不一致
  - **缓解**: 支持双字段匹配（ID+名称），提供映射参考文档

---

### Phase 6: API 接口模块

**目标**: 提供 RESTful API 接口，支持单个和批量生成

**时间估算**: 3-4 天

**复杂度**: 中

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 6.1 | FastAPI 应用初始化 | `src/app.py` | FastAPI 应用 | Phase 5 |
| 6.2 | 请求/响应模型 | `src/api/schemas.py` | Pydantic 模型 | 6.1 |
| 6.3 | 健康检查接口 | `src/api/routes/health.py` | /health 端点 | 6.1 |
| 6.4 | 模板列表查询接口 | `src/api/routes/templates.py` | /templates 端点 | 6.1 |
| 6.5 | 单文件生成接口 | `src/api/routes/generate.py` | /generate 端点 | Phase 5, 6.2 |
| 6.6 | 批量生成接口 | `src/api/routes/batch_generate.py` | /batch 端点 | 6.5 |
| 6.7 | 文件下载处理 | `src/api/handlers/file_handler.py` | 文件响应处理 | 6.5, 6.6 |
| 6.8 | 异步任务处理 | `src/api/tasks/async_tasks.py` | 异步任务 | 6.6 |
| 6.9 | API 路由注册 | `src/api/router.py` | 路由聚合 | 6.3-6.8 |
| 6.10 | API 单元测试 | `tests/test_api.py` | 测试用例 | 6.5, 6.6 |

#### 产出物清单
- [ ] FastAPI 应用 (`src/app.py`)
- [ ] 请求/响应模型 (`src/api/schemas.py`)
- [ ] 健康检查接口 (`src/api/routes/health.py`)
- [ ] 模板列表接口 (`src/api/routes/templates.py`)
- [ ] 单文件生成接口 (`src/api/routes/generate.py`)
- [ ] 批量生成接口 (`src/api/routes/batch_generate.py`)
- [ ] 文件下载处理器 (`src/api/handlers/file_handler.py`)
- [ ] 异步任务处理 (`src/api/tasks/async_tasks.py`)
- [ ] API 单元测试

#### 风险点
- **风险**: 高并发下资源耗尽
  - **缓解**: 使用异步处理、请求限流
- **风险**: 大文件下载超时
  - **缓解**: 流式响应、分块传输

---

### Phase 7: 日志与错误处理

**目标**: 完善日志记录和错误处理机制

**时间估算**: 2-3 天

**复杂度**: 低

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 | 状态 |
|------|------|----------|--------|------|------|
| 7.1 | 结构化日志配置 | `src/utils/structured_logger.py` | 日志配置模块 | Phase 6 | ✅ 已实现 |
| 7.2 | 日志轮转配置 | `src/utils/logger.py` | 日志轮转工具 | 7.1 | ✅ 已实现 |
| 7.3 | 异常类定义 | `src/exceptions/*.py` | 异常类层次 | Phase 6 | ✅ 已实现 |
| 7.4 | 错误处理中间件 | `src/api/middleware/error_handler.py` | 错误处理 | 7.3 | ✅ 已实现 |
| 7.5 | 请求日志中间件 | `src/api/middleware/logging.py` | 请求日志中间件 | 7.1 | 待实现 |
| 7.6 | 审计日志服务 | `src/services/audit_logger.py` | 审计日志记录 | 7.1 | 待实现 |
| 7.7 | 日志清理任务 | `src/tasks/log_cleanup.py` | 定时清理任务 | 7.2 | 待实现 |
| 7.8 | 新增认证异常 | `src/exceptions/api.py` | AuthenticationError | 7.3 | 待实现 |
| 7.9 | 新增限流异常 | `src/exceptions/api.py` | RateLimitError | 7.3 | 待实现 |

#### 产出物清单
- [x] 结构化日志模块 (`src/utils/structured_logger.py`)
- [x] 日志轮转工具 (`src/utils/logger.py`)
- [x] 错误处理中间件 (`src/api/middleware/error_handler.py`)
- [x] 异常类层次 (`src/exceptions/*.py`)
- [ ] 请求日志中间件 (`src/api/middleware/logging.py`)
- [ ] 审计日志服务 (`src/services/audit_logger.py`)
- [ ] 日志清理任务 (`src/tasks/log_cleanup.py`)
- [ ] AuthenticationError (`src/exceptions/api.py`)
- [ ] RateLimitError (`src/exceptions/api.py`)

#### 风险点
- **风险**: 日志文件过大
  - **缓解**: 7天自动清理，10MB轮转

---

### Phase 8: 测试与优化

**目标**: 完成单元测试、集成测试、性能测试

**时间估算**: 3-4 天

**复杂度**: 中

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 8.1 | 单元测试完善 | `tests/unit/` | 单元测试套件 | Phase 1-7 |
| 8.2 | 集成测试 | `tests/integration/` | 集成测试套件 | 8.1 |
| 8.3 | API 端到端测试 | `tests/e2e/test_api_flow.py` | E2E 测试 | 8.1 |
| 8.4 | 性能测试脚本 | `tests/performance/` | 性能测试脚本 | 8.2 |
| 8.5 | 并发压力测试 | `tests/performance/concurrent_test.py` | 并发测试 | 8.4 |
| 8.6 | 测试覆盖率报告 | `tests/coverage/` | 覆盖率报告 | 8.1, 8.2 |

#### 产出物清单
- [ ] 单元测试套件 (`tests/unit/`)
- [ ] 集成测试套件 (`tests/integration/`)
- [ ] E2E 测试 (`tests/e2e/`)
- [ ] 性能测试脚本 (`tests/performance/`)
- [ ] 测试覆盖率报告

#### 风险点
- **风险**: 性能不达标
  - **缓解**: 性能分析、优化热点、引入缓存

---

### Phase 9: 部署与文档

**目标**: 完成 Docker 部署和项目文档

**时间估算**: 2-3 天

**复杂度**: 低

#### 任务列表

| 序号 | 任务 | 文件路径 | 产出物 | 依赖 |
|------|------|----------|--------|------|
| 9.1 | Dockerfile 编写 | `Dockerfile` | Docker 镜像 | Phase 8 |
| 9.2 | docker-compose 配置 | `docker-compose.yml` | 编排配置 | 9.1 |
| 9.3 | 部署脚本 | `scripts/deploy.sh` | 部署脚本 | 9.2 |
| 9.4 | API 文档生成 | `docs/api/api_spec.yaml` | OpenAPI 文档 | Phase 6 |
| 9.5 | 用户使用手册 | `docs/user_guide.md` | 用户手册 | 9.4 |
| 9.6 | 部署运维文档 | `docs/deployment.md` | 运维文档 | 9.2 |

#### 产出物清单
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] 部署脚本 (`scripts/deploy.sh`)
- [ ] API 文档 (`docs/api/api_spec.yaml`)
- [ ] 用户手册 (`docs/user_guide.md`)
- [ ] 运维文档 (`docs/deployment.md`)

#### 风险点
- **风险**: 生产环境配置差异
  - **缓解**: 环境变量配置、多环境支持

---

## 3. 风险评估

### 3.1 技术风险

| 风险项 | 风险等级 | 影响范围 | 缓解措施 |
|--------|----------|----------|----------|
| Oracle 连接不稳定 | 高 | 数据查询模块 | 连接池管理、重试机制、健康检查 |
| 模板规则复杂 | 中 | 模板匹配引擎 | 规则外部化、充分测试、文档完善 |
| Word 格式兼容性 | 中 | Word 生成模块 | 格式验证器、模板规范化 |
| 并发性能问题 | 中 | API 接口模块 | 异步处理、限流、缓存 |
| 表结构变更 | 低 | 数据查询模块 | 字段映射配置化、版本管理 |

### 3.2 业务风险

| 风险项 | 风险等级 | 影响范围 | 缓解措施 |
|--------|----------|----------|----------|
| 模板匹配规则不明确 | 高 | 整体流程 | 与业务方确认规则、建立测试用例 |
| 需求变更频繁 | 中 | 开发进度 | 模块化设计、规则外部化 |
| 数据质量问题 | 中 | 输出结果 | 数据校验、异常处理 |

### 3.3 依赖风险

| 依赖项 | 风险等级 | 缓解措施 |
|--------|----------|----------|
| Oracle 数据库访问权限 | 高 | 提前申请、测试环境验证 |
| 35 个 Word 模板文件 | 中 | 提前收集、格式验证 |
| 规则 Excel 文件 | 低 | 提前获取、格式确认 |

---

## 4. 关键路径

### 4.1 依赖关系图

```
Phase 1 (基础设施)
    |
    v
Phase 2 (数据库连接) -----> Phase 3 (数据查询)
    |                              |
    |                              v
    +------------------------> Phase 4 (模板匹配)
                                   |
                                   v
Phase 5 (Word 生成) <---------------+
    |
    v
Phase 6 (API 接口)
    |
    v
Phase 7 (日志错误) -----> Phase 8 (测试优化) -----> Phase 9 (部署文档)
```

### 4.2 关键路径
```
Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 6 -> Phase 8 -> Phase 9
```

### 4.3 可并行任务

| 并行组 | 可并行任务 |
|--------|------------|
| Group A | Phase 2 数据库连接 + 规则文件分析准备 |
| Group B | Phase 4 模板匹配 + Word 模板格式分析 |
| Group C | Phase 7 日志错误处理 + Phase 8 测试编写 |

---

## 5. 时间估算

### 5.1 总体时间线

| 阶段 | 任务 | 时间 (天) | 累计 (天) | 复杂度 |
|------|------|----------|----------|--------|
| Week 1 | Phase 1: 基础设施 | 2-3 | 3 | 低 |
| Week 1 | Phase 2: 数据库连接 | 3-4 | 6 | 高 |
| Week 2 | Phase 3: 数据查询 | 3-4 | 10 | 中 |
| Week 2-3 | Phase 4: 模板匹配 | 4-5 | 15 | 高 |
| Week 3 | Phase 5: Word 生成 | 4-5 | 20 | 高 |
| Week 3-4 | Phase 6: API 接口 | 3-4 | 23 | 中 |
| Week 4 | Phase 7: 日志错误 | 2-3 | 25 | 低 |
| Week 4 | Phase 8: 测试优化 | 3-4 | 28 | 中 |
| Week 4 | Phase 9: 部署文档 | 2-3 | 30 | 低 |

**总工期**: 约 20-23 个工作日 (4 周)

### 5.2 里程碑

| 里程碑 | 时间点 | 产出 |
|--------|--------|------|
| M1: 数据库连通 | 第 1 周末 | Oracle 连接可用 |
| M2: 数据查询可用 | 第 2 周中 | 数据查询接口可用 |
| M3: 模板匹配可用 | 第 2 周末 | 模板匹配引擎可用 |
| M4: Word 生成可用 | 第 3 周中 | 文档生成功能可用 |
| M5: API 可用 | 第 3 周末 | API 接口可用 |
| M6: 系统上线 | 第 4 周末 | 系统部署上线 |

---

## 6. 资源需求

### 6.1 人力资源

| 角色 | 人数 | 主要职责 | 参与阶段 |
|------|------|----------|----------|
| 后端开发工程师 | 1 | 核心业务逻辑、API 开发 | Phase 2-6 |
| 架构/全栈工程师 | 1 | 架构设计、配置、日志 | Phase 1, 7, 9 |
| 测试/运维工程师 | 0.5-1 | 测试、部署 | Phase 8-9 |

### 6.2 环境需求

| 环境 | 用途 | 规格 |
|------|------|------|
| 开发环境 | 日常开发 | Python 3.10+, 4GB RAM |
| 测试环境 | 集成测试 | Docker, Oracle 连接 |
| 生产环境 | 正式部署 | 8GB RAM, 4 核 CPU |

### 6.3 外部依赖

| 依赖项 | 类型 | 获取方式 | 负责人 |
|--------|------|----------|--------|
| Oracle 数据库连接信息 | 配置 | 业务方提供 | DBA |
| 35 个 Word 模板文件 | 文件 | 业务方提供 | 业务方 |
| 价格模板规则 Excel | 文件 | 业务方提供 | 业务方 |
| 测试用 wybs 报价单号 | 数据 | 业务方提供 | 业务方 |

---

## 7. 成功标准

### 7.1 功能验收标准

- [ ] 能够成功连接 Oracle 数据库并查询数据
- [ ] 能够正确解析 35 个模板的匹配规则
- [ ] 模板匹配准确率达到 100%
- [ ] Word 文档生成格式正确、数据准确
- [ ] API 接口响应时间 < 5 秒
- [ ] 支持 10+ 并发请求
- [ ] 错误处理完善，返回明确错误信息

### 7.2 质量标准

- [ ] 单元测试覆盖率 >= 80%
- [ ] 集成测试通过率 100%
- [ ] 性能测试通过
- [ ] 无 Critical 级别代码问题
- [ ] API 文档完整

### 7.3 交付标准

- [ ] 源代码及完整注释
- [ ] 单元测试和集成测试代码
- [ ] API 文档
- [ ] 部署文档
- [ ] 用户手册
- [ ] Docker 镜像

---

## 8. 附录

### 8.1 项目目录结构

```
contract/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   ├── middleware/
│   │   ├── handlers/
│   │   ├── tasks/
│   │   ├── schemas.py
│   │   └── router.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── config.py
│   │   └── health.py
│   ├── models/
│   │   ├── quotation.py
│   │   ├── template_rule.py
│   │   └── match_result.py
│   ├── queries/
│   │   ├── quotation.py
│   │   └── quotation_detail.py
│   ├── loaders/
│   │   └── template_loader.py
│   ├── parsers/
│   │   ├── rule_parser.py
│   │   └── condition_parser.py
│   ├── filters/
│   │   └── detail_filter.py
│   ├── mappers/
│   │   └── field_mapper.py
│   ├── matchers/
│   │   ├── template_matcher.py
│   │   └── multi_matcher.py
│   ├── engines/
│   │   └── speech_engine.py
│   ├── generators/
│   │   └── document_generator.py
│   ├── readers/
│   │   └── word_template_reader.py
│   ├── analyzers/
│   │   └── table_analyzer.py
│   ├── fillers/
│   │   ├── data_filler.py
│   │   ├── row_expander.py
│   │   └── format_preserver.py
│   ├── transformers/
│   │   └── data_transformer.py
│   ├── services/
│   │   ├── rule_loader.py
│   │   └── audit_logger.py
│   ├── utils/
│   │   ├── logger.py
│   │   ├── structured_logger.py
│   │   └── file_packer.py
│   ├── exceptions/
│   │   └── __init__.py
│   ├── config/
│   │   └── settings.py
│   └── app.py
├── config/
│   ├── settings.yaml.example
│   ├── field_mapping.yaml
│   └── template_metadata/
│       ├── templates.yaml
│       └── templates/
│           ├── 模板1.yaml
│           ├── 模板2.yaml
│           └── ... (35个模板)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── performance/
├── docs/
│   ├── plan/
│   │   ├── phase-4/
│   │   ├── phase-5/
│   │   │   └── field_id_mapping.md
│   │   └── implementation_plan.md
│   ├── api/
│   ├── user_guide.md
│   └── deployment.md
├── scripts/
│   └── deploy.sh
├── templates/
│   └── (35 个 Word 模板)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

### 8.2 技术依赖清单

```txt
# requirements.txt
fastapi>=0.100.0
uvicorn>=0.23.0
python-oracledb>=1.4.0
sqlalchemy>=2.0.0
python-docx>=0.8.11
openpyxl>=3.1.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
aiofiles>=23.0.0

# Dev dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
black>=23.0.0
isort>=5.12.0
mypy>=1.4.0
```

---

## 9. 总结

本实施计划将项目分解为 9 个阶段，总工期约 4 周。关键路径为数据库连接、数据查询、模板匹配、Word 生成、API 接口、测试优化、部署文档。建议优先保障 Phase 2(数据库连接) 和 Phase 4(模板匹配引擎) 的质量，这两个阶段风险最高且处于关键路径上。

---

## 10. Phase 5 设计更新记录

本文档已根据 `docs/plan/phase-5/` 设计文档更新，主要变更：

### 10.1 Phase 5 任务拆分

将原有的 8 个任务拆分为 13 个任务，新增：
- 模板元数据加载器 (`template_loader.py`)
- 条件表达式解析器 (`condition_parser.py`)
- 明细数据过滤器 (`detail_filter.py`)
- 字段映射层 (`field_mapper.py`)
- 话术引擎 (`speech_engine.py`)

### 10.2 配置结构更新

- 模板元数据从单一规则文件改为每个模板独立 YAML 文件
- 新增 `config/template_metadata/templates/` 目录
- 支持双字段匹配（ID + 名称）

### 10.3 字段ID映射

- 新增 `docs/plan/phase-5/field_id_mapping.md` 参考文档
- 产品细分、定价组、供货价类型的ID映射

---

## 11. Phase 7 设计更新记录

本文档已根据 `docs/plan/phase-7/` 设计文档更新，主要变更：

### 11.1 日志设计

- **日志格式**: JSON 结构化日志
- **日志分类**: 应用日志、访问日志、错误日志、审计日志
- **日志保留**: 7 天自动清理
- **轮转策略**: 10MB 自动轮转

### 11.2 审计日志

- **存储位置**: 本地文件 `logs/audit.log`
- **格式**: JSON Lines
- **保留周期**: 7 天
- **字段增强**: 补充 user_agent、error_message、request_id

### 11.3 错误处理

- 统一使用 Phase 6 现有数值型错误码
- 复用现有 AppException 类结构
- 新增 AuthenticationError、RateLimitError

### 11.4 任务状态

- ✅ 已实现（4项）: 结构化日志、日志轮转、异常类、错误处理中间件
- 待实现（5项）: 请求日志中间件、审计日志服务、日志清理、认证异常、限流异常
- 移除: 日志查询接口

---

*文档版本：1.3*
*创建日期：2026-03-06*
*最后更新：2026-03-10*
