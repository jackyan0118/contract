# Phase 1: 项目基础设施搭建 - 设计索引

## 概述

Phase 1 是整个价格附件生成系统的基础，负责搭建项目骨架、配置管理、日志系统和异常处理体系。后续所有模块都将依赖这些基础设施。

## 设计文档清单

| 文档编号 | 文档名称 | 说明 | 状态 |
|----------|----------|------|------|
| 01 | [directory-structure.md](./01-directory-structure.md) | 项目目录结构设计 | [x] 已完成 |
| 02 | [project-configuration.md](./02-project-configuration.md) | Python 项目配置 | [x] 已完成 |
| 03 | [config-management.md](./03-config-management.md) | 配置管理模块设计 | [x] 已完成 |
| 04 | [logging-system.md](./04-logging-system.md) | 日志系统设计 | [x] 已完成 |
| 05 | [exception-handling.md](./05-exception-handling.md) | 异常处理体系设计 | [x] 已完成 |
| 06 | [config-template.md](./06-config-template.md) | 配置文件模板 | [x] 已完成 |

## 任务依赖关系

```
1.1 目录结构 ─────┬──> 1.2 项目配置
                  │
                  ├──> 1.3 配置管理
                  │
                  ├──> 1.4 日志系统
                  │
                  └──> 1.5 异常处理
                           │
                           v
                  1.6 配置模板
```

## 产出物清单

### 目录结构
```
contract/
├── src/                      # 源代码目录
│   ├── api/                  # API 接口层
│   ├── core/                 # 核心业务逻辑
│   ├── database/             # 数据库访问层
│   ├── utils/                # 工具函数
│   ├── exceptions/           # 异常类定义
│   ├── config/               # 配置管理
│   └── app.py                # 应用入口
├── config/                   # 配置文件目录
│   └── settings.yaml.example # 配置模板
├── tests/                    # 测试目录
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── docs/                     # 文档目录
├── scripts/                  # 脚本目录
├── pyproject.toml            # 项目配置
├── requirements.txt          # 运行时依赖
├── requirements-dev.txt      # 开发依赖
├── .env.example              # 环境变量模板
└── .gitignore
```

### 文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `pyproject.toml` | Python 项目配置 | [x] 已完成 |
| `requirements.txt` | 运行时依赖 | [x] 已完成 |
| `requirements-dev.txt` | 开发依赖 | [x] 已完成 |
| `src/config/settings.py` | 配置管理模块 | [x] 已完成 |
| `src/utils/logger.py` | 日志模块 | [x] 已完成 |
| `src/exceptions/__init__.py` | 异常类定义 | [x] 已完成 |
| `config/settings.yaml.example` | 配置模板 | [x] 已完成 |
| `.env.example` | 环境变量模板 | [x] 已完成 |

## 配置项清单

### 应用配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `app.name` | string | "价格附件生成系统" | 应用名称 |
| `app.debug` | boolean | false | 调试模式 |
| `app.version` | string | "0.1.0" | 版本号 |

### 数据库配置
| 配置项 | 类型 | 说明 |
|--------|------|------|
| `database.dsn` | string | Oracle 连接字符串 |
| `database.min_connections` | int | 最小连接数 |
| `database.max_connections` | int | 最大连接数 |
| `database.pool_increment` | int | 连接池增量 |

### 日志配置
| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `logging.level` | string | "INFO" | 日志级别 |
| `logging.format` | string | - | 日志格式 |
| `logging.file` | string | - | 日志文件路径 |
| `logging.max_bytes` | int | 10MB | 单文件最大大小 |
| `logging.backup_count` | int | 5 | 备份文件数 |

### 模板配置
| 配置项 | 类型 | 说明 |
|--------|------|------|
| `templates.path` | string | 模板文件目录 |
| `templates.rule_file` | string | 规则 Excel 文件 |

## 异常类层次结构

```
BaseException
    └── AppException (应用基础异常)
        ├── ConfigException (配置异常)
        ├── DatabaseException (数据库异常)
        │   ├── ConnectionException (连接异常)
        │   └── QueryException (查询异常)
        ├── TemplateException (模板异常)
        │   ├── MatchException (匹配异常)
        │   └── GenerateException (生成异常)
        └── APIException (API 异常)
            ├── ValidationError (验证异常)
            └── NotFoundException (未找到异常)
```

## 日志格式设计

### 控制台输出格式
```
[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
```

### 文件输出格式（JSON）
```json
{
  "timestamp": "2026-03-06T10:00:00Z",
  "level": "INFO",
  "logger": "app.api",
  "message": "请求处理完成",
  "context": {
    "wybs": "QTD20260306001",
    "duration_ms": 1234,
    "templates_matched": ["模板 1", "模板 2"]
  }
}
```

## 验收标准

- [x] 目录结构符合项目规范
- [x] Python 项目可正常安装和运行
- [x] 配置可从环境变量和 YAML 文件加载
- [x] 日志可按级别输出到控制台和文件
- [x] 异常可被统一捕获和处理
- [x] 所有模块有单元测试覆盖（覆盖率 >= 80%）- 覆盖率 92.74%

## 技术风险

| 风险项 | 风险等级 | 缓解措施 |
|--------|----------|----------|
| Python 版本兼容性 | 低 | 锁定 Python 3.10+ |
| 配置加载失败 | 低 | 提供默认值和详细错误信息 |
| 日志性能影响 | 低 | 异步日志、合理级别 |

## 下一步

Phase 1 完成后，进入 **Phase 2: Oracle 数据库连接模块**

---

*文档版本：1.0*
*创建日期：2026-03-06*
