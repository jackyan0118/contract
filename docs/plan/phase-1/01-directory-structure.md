# 01. 项目目录结构设计

## 设计目标

建立清晰、可扩展的项目目录结构，遵循 Python 项目最佳实践，支持模块化开发和测试。

## 目录结构

```
contract/
├── src/                          # 源代码目录
│   ├── api/                      # API 接口层
│   │   ├── __init__.py
│   │   ├── app.py                # FastAPI 应用入口
│   │   ├── schemas.py            # Pydantic 请求/响应模型
│   │   ├── router.py             # 路由聚合
│   │   ├── routes/               # 路由定义
│   │   │   ├── __init__.py
│   │   │   ├── health.py         # 健康检查接口
│   │   │   ├── templates.py      # 模板列表接口
│   │   │   ├── generate.py       # 单文件生成接口
│   │   │   └── batch_generate.py # 批量生成接口
│   │   ├── middleware/           # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── request_logger.py # 请求日志
│   │   │   └── error_handler.py  # 错误处理
│   │   ├── handlers/             # 处理器
│   │   │   ├── __init__.py
│   │   │   └── file_handler.py   # 文件下载处理
│   │   └── tasks/                # 异步任务
│   │       ├── __init__.py
│   │       └── async_tasks.py    # 异步任务处理
│   ├── config/                   # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py           # 配置加载器
│   ├── database/                 # 数据库访问层
│   │   ├── __init__.py
│   │   ├── connection.py         # 连接池管理
│   │   ├── config.py             # 数据库配置
│   │   └── health.py             # 健康检查
│   ├── exceptions/               # 异常类定义
│   │   ├── __init__.py           # 异常层次结构
│   │   ├── base.py               # 基础异常
│   │   ├── config.py             # 配置异常
│   │   ├── database.py           # 数据库异常
│   │   ├── template.py           # 模板异常
│   │   └── api.py                # API 异常
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── quotation.py          # 报价单模型
│   │   ├── template_rule.py      # 模板规则模型
│   │   └── match_result.py       # 匹配结果模型
│   ├── queries/                  # 查询逻辑
│   │   ├── __init__.py
│   │   ├── quotation.py          # 报价单查询
│   │   └── quotation_detail.py   # 明细查询
│   ├── transformers/             # 数据转换
│   │   ├── __init__.py
│   │   └── data_transformer.py   # Oracle -> 内部模型
│   ├── parsers/                  # 解析器
│   │   ├── __init__.py
│   │   └── rule_parser.py        # Excel 规则解析
│   ├── matchers/                 # 匹配引擎
│   │   ├── __init__.py
│   │   ├── template_matcher.py   # 模板匹配器
│   │   └── multi_matcher.py      # 多模板处理
│   ├── readers/                  # 读取器
│   │   ├── __init__.py
│   │   └── word_template_reader.py # Word 模板读取
│   ├── fillers/                  # 填充器
│   │   ├── __init__.py
│   │   ├── data_filler.py        # 数据填充
│   │   ├── row_expander.py       # 表格行扩展
│   │   └── format_preserver.py   # 格式保持
│   ├── generators/               # 生成器
│   │   ├── __init__.py
│   │   └── document_generator.py # 文档生成
│   ├── services/                 # 服务层
│   │   ├── __init__.py
│   │   ├── rule_loader.py        # 规则加载服务
│   │   └── audit_logger.py       # 业务日志服务
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py             # 日志配置
│   │   ├── structured_logger.py  # 结构化日志
│   │   └── file_packer.py        # ZIP 打包
│   └── __init__.py
├── config/                       # 配置文件目录
│   ├── settings.yaml.example     # 配置模板
│   └── field_mapping.yaml        # 字段映射配置
├── tests/                        # 测试目录
│   ├── __init__.py
│   ├── conftest.py               # pytest 配置
│   ├── unit/                     # 单元测试
│   │   ├── test_config.py
│   │   ├── test_logger.py
│   │   └── test_exceptions.py
│   ├── integration/              # 集成测试
│   │   ├── test_database.py
│   │   └── test_matcher.py
│   └── e2e/                      # E2E 测试
│       └── test_api_flow.py
├── docs/                         # 文档目录
│   ├── api/                      # API 文档
│   ├── plan/                     # 项目计划
│   └── template/                 # 模板说明
├── scripts/                      # 脚本目录
│   └── deploy.sh                 # 部署脚本
├── templates/                    # Word 模板文件
│   └── (35 个 Word 模板)
├── .env.example                  # 环境变量模板
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                # 项目配置
├── requirements.txt              # 运行时依赖
└── requirements-dev.txt          # 开发依赖
```

## 目录说明

| 目录 | 职责 | 示例 |
|------|------|------|
| `src/api/` | REST API 接口层 | routes, middleware, schemas |
| `src/config/` | 配置管理 | settings.py |
| `src/database/` | 数据库连接 | connection.py, health.py |
| `src/exceptions/` | 异常类定义 | base.py, database.py |
| `src/models/` | 数据模型 | quotation.py, template_rule.py |
| `src/queries/` | SQL 查询逻辑 | quotation.py |
| `src/transformers/` | 数据转换 | data_transformer.py |
| `src/parsers/` | 文件解析 | rule_parser.py |
| `src/matchers/` | 模板匹配 | template_matcher.py |
| `src/readers/` | 模板读取 | word_template_reader.py |
| `src/fillers/` | 数据填充 | data_filler.py, row_expander.py |
| `src/generators/` | 文档生成 | document_generator.py |
| `src/services/` | 业务服务 | rule_loader.py, audit_logger.py |
| `src/utils/` | 通用工具 | logger.py, file_packer.py |
| `tests/` | 测试代码 | unit, integration, e2e |
| `config/` | 配置文件 | settings.yaml.example |
| `templates/` | Word 模板 | 35 个 docx 文件 |

## 模块依赖关系

```
api (依赖) -> services, models, schemas
services (依赖) -> matchers, generators, parsers
matchers (依赖) -> models, parsers
generators (依赖) -> readers, fillers, models
readers (依赖) -> python-docx
fillers (依赖) -> models
parsers (依赖) -> openpyxl
database (独立)
config (独立)
exceptions (独立)
utils (独立)
```

## 验收标准

- [ ] 目录结构创建完成
- [ ] 所有 `__init__.py` 文件存在
- [ ] 模块依赖关系清晰
- [ ] 符合 Python 项目布局规范

---

*文档版本：1.0*
*创建日期：2026-03-06*
