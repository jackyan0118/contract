# 03. 配置管理模块设计

## 设计目标

实现类型安全的配置管理系统，支持从环境变量和 YAML 文件加载配置，提供默认值和验证机制。

## 技术选型

- **Pydantic Settings** - 类型安全的配置管理
- **PyYAML** - YAML 文件解析
- **环境变量** - 容器化部署支持

## 配置类层次结构

```
BaseSettings (pydantic)
    ├── AppSettings (应用配置)
    ├── DatabaseSettings (数据库配置)
    ├── LoggingSettings (日志配置)
    ├── TemplateSettings (模板配置)
    └── Settings (聚合配置)
```

## 代码实现

### src/config/settings.py

```python
"""配置管理模块 - 类型安全的配置加载系统."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator, model_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """应用配置."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )

    name: str = Field(default="价格附件生成系统", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    version: str = Field(default="0.1.0", description="版本号")
    host: str = Field(default="0.0.0.0", description="监听地址")
    port: int = Field(default=8000, description="监听端口")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("端口必须在 1-65535 范围内")
        return v


class DatabaseSettings(BaseSettings):
    """数据库配置."""

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        extra="ignore",
    )

    dsn: SecretStr = Field(
        default=SecretStr(""),
        description="Oracle 连接字符串",
        examples=["oracle://user:password@host:1521/service_name"]
    )
    min_connections: int = Field(default=2, description="最小连接数", ge=1, le=100)
    max_connections: int = Field(default=10, description="最大连接数", ge=1, le=100)
    pool_increment: int = Field(default=1, description="连接池增量", ge=1)
    connect_timeout: int = Field(default=30, description="连接超时 (秒)", ge=5, le=300)
    command_timeout: int = Field(default=60, description="命令超时 (秒)", ge=10, le=600)

    @field_validator("dsn")
    @classmethod
    def validate_dsn(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("数据库连接字符串不能为空")
        return v

    @model_validator(mode="after")
    def validate_pool_size(self):
        if self.max_connections < self.min_connections:
            raise ValueError("最大连接数不能小于最小连接数")
        return self

    def get_dsn(self) -> str:
        """获取解密后的 DSN."""
        return self.dsn.get_secret_value()


class LoggingSettings(BaseSettings):
    """日志配置."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        extra="ignore",
    )

    level: str = Field(default="INFO", description="日志级别")
    format_console: str = Field(
        default="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        description="控制台日志格式"
    )
    format_file: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="文件日志格式"
    )
    file_path: str = Field(default="logs/app.log", description="日志文件路径")
    max_bytes: int = Field(default=10485760, description="单文件最大大小 (10MB)")
    backup_count: int = Field(default=5, description="备份文件数")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是 {valid_levels}")
        return v.upper()


class TemplateSettings(BaseSettings):
    """模板配置."""

    model_config = SettingsConfigDict(
        env_prefix="TEMPLATE_",
        env_file=".env",
        extra="ignore",
    )

    path: str = Field(default="templates", description="模板文件目录")
    rule_file: str = Field(
        default="价格模板规则 - 更新 2026306.xlsx",
        description="规则 Excel 文件名"
    )
    output_dir: str = Field(default="output", description="输出文件目录")
    max_file_size: int = Field(default=10485760, description="最大文件大小 (10MB)")


class Settings(BaseSettings):
    """聚合配置."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    template: TemplateSettings = Field(default_factory=TemplateSettings)

    @classmethod
    def load_from_yaml(cls, yaml_path: str) -> "Settings":
        """从 YAML 文件加载配置."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls(
            app=AppSettings(**data.get("app", {})),
            database=DatabaseSettings(**data.get("database", {})),
            logging=LoggingSettings(**data.get("logging", {})),
            template=TemplateSettings(**data.get("template", {})),
        )


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（单例模式）."""
    # 尝试从 YAML 加载
    yaml_path = Path("config/settings.yaml")
    if yaml_path.exists():
        return Settings.load_from_yaml(str(yaml_path))

    # 从环境变量加载
    return Settings()


# 全局配置实例
settings = get_settings()
```

### src/config/__init__.py

```python
"""配置管理模块."""

from .settings import (
    AppSettings,
    DatabaseSettings,
    LoggingSettings,
    Settings,
    TemplateSettings,
    get_settings,
    settings,
)

__all__ = [
    "AppSettings",
    "DatabaseSettings",
    "LoggingSettings",
    "Settings",
    "TemplateSettings",
    "get_settings",
    "settings",
]
```

## 配置项清单

### 应用配置 (APP_*)

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `app.name` | `APP_NAME` | "价格附件生成系统" | 应用名称 |
| `app.debug` | `APP_DEBUG` | false | 调试模式 |
| `app.version` | `APP_VERSION` | "0.1.0" | 版本号 |
| `app.host` | `APP_HOST` | "0.0.0.0" | 监听地址 |
| `app.port` | `APP_PORT` | 8000 | 监听端口 |

### 数据库配置 (DB_*)

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `database.dsn` | `DB_DSN` | - | Oracle 连接字符串 |
| `database.min_connections` | `DB_MIN_CONNECTIONS` | 2 | 最小连接数 |
| `database.max_connections` | `DB_MAX_CONNECTIONS` | 10 | 最大连接数 |
| `database.pool_increment` | `DB_POOL_INCREMENT` | 1 | 连接池增量 |
| `database.connect_timeout` | `DB_CONNECT_TIMEOUT` | 30 | 连接超时 (秒) |
| `database.command_timeout` | `DB_COMMAND_TIMEOUT` | 60 | 命令超时 (秒) |

### 日志配置 (LOG_*)

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `logging.level` | `LOG_LEVEL` | "INFO" | 日志级别 |
| `logging.format_console` | `LOG_FORMAT_CONSOLE` | - | 控制台日志格式 |
| `logging.format_file` | `LOG_FORMAT_FILE` | - | 文件日志格式 |
| `logging.file_path` | `LOG_FILE_PATH` | "logs/app.log" | 日志文件路径 |
| `logging.max_bytes` | `LOG_MAX_BYTES` | 10485760 | 单文件最大大小 |
| `logging.backup_count` | `LOG_BACKUP_COUNT` | 5 | 备份文件数 |

### 模板配置 (TEMPLATE_*)

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|----------|--------|------|
| `template.path` | `TEMPLATE_PATH` | "templates" | 模板文件目录 |
| `template.rule_file` | `TEMPLATE_RULE_FILE` | - | 规则 Excel 文件名 |
| `template.output_dir` | `TEMPLATE_OUTPUT_DIR` | "output" | 输出文件目录 |
| `template.max_file_size` | `TEMPLATE_MAX_FILE_SIZE` | 10485760 | 最大文件大小 |

## 使用示例

```python
# 导入配置
from src.config import settings

# 访问配置
print(settings.app.name)
print(settings.app.port)
print(settings.database.dsn)
print(settings.logging.level)

# 在 FastAPI 中使用
from fastapi import FastAPI

app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    version=settings.app.version,
)
```

## 验收标准

- [ ] 配置类支持类型提示
- [ ] 可从环境变量加载配置
- [ ] 可从 YAML 文件加载配置
- [ ] 配置验证正常工作
- [ ] 默认值正确设置
- [ ] 单例模式正常工作

---

*文档版本：1.0*
*创建日期：2026-03-06*
