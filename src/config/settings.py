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
    )
    db_schema: str = Field(default="", description="Oracle Schema/用户，用于查询表时指定前缀")
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

    @field_validator("max_connections")
    @classmethod
    def validate_max_connections(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("最大连接数必须在 1-100 范围内")
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
        description="控制台日志格式",
    )
    format_file: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="文件日志格式",
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
        description="规则 Excel 文件名",
    )
    output_dir: str = Field(default="output", description="输出文件目录")
    max_file_size: int = Field(default=10485760, description="最大文件大小 (10MB)")


class SecuritySettings(BaseSettings):
    """安全配置."""

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        env_file=".env",
        extra="ignore",
    )

    api_keys: list[dict] = Field(default_factory=list, description="API Key 列表")


class RateLimitSettings(BaseSettings):
    """限流配置."""

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        env_file=".env",
        extra="ignore",
    )

    default: str = Field(default="100/minute", description="默认限流")
    generate: str = Field(default="20/minute", description="生成接口限流")
    batch: str = Field(default="5/minute", description="批量接口限流")
    by_ip: bool = Field(default=True, description="是否按IP限流")
    whitelist: list[str] = Field(default_factory=list, description="IP白名单")


class DownloadsSettings(BaseSettings):
    """下载服务配置."""

    model_config = SettingsConfigDict(
        env_prefix="DOWNLOADS_",
        env_file=".env",
        extra="ignore",
    )

    url_path: str = Field(default="/static/downloads", description="下载URL路径")
    storage_dir: str = Field(default="output/downloads", description="下载文件存储目录")
    base_url: str = Field(default="http://localhost:8000", description="生成URL的Base URL")
    expires_in: int = Field(default=86400, description="文件过期时间（秒），默认24小时")
    auto_cleanup: bool = Field(default=True, description="是否自动清理过期文件")
    cleanup_cron: str = Field(default="0 2 * *", description="定时清理Cron表达式")
    max_file_size_mb: int = Field(default=100, description="单个文件大小限制（MB）")
    disk_space_threshold: int = Field(default=80, description="磁盘空间告警阈值（%）")


class WeaverSettings(BaseSettings):
    """泛微OA配置."""

    model_config = SettingsConfigDict(
        env_prefix="WEAVER_",
        env_file=".env",
        extra="ignore",
    )

    hosts: list[str] = Field(
        default_factory=lambda: ["172.16.14.6:8080", "172.16.14.19:8080"],
        description="OA服务器地址列表"
    )
    active_host_index: int = Field(default=0, description="当前使用的服务器索引")
    system_id: str = Field(
        default="SalesContract_PriceUrl_Update",
        description="系统标识"
    )
    password: str = Field(default="weaver2025", description="MD5签名密码")
    operator_id: str = Field(default="5288", description="默认操作人ID")
    timeout: int = Field(default=30, description="请求超时（秒）")
    retry_count: int = Field(default=3, description="重试次数")


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
    downloads: DownloadsSettings = Field(default_factory=DownloadsSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    weaver: WeaverSettings = Field(default_factory=WeaverSettings)

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
            security=SecuritySettings(**data.get("security", {})),
            rate_limit=RateLimitSettings(**data.get("rate_limit", {})),
            weaver=WeaverSettings(**data.get("weaver", {})),
        )


@lru_cache
def get_settings() -> Settings:
    """获取配置实例（单例模式）."""
    yaml_path = Path("config/settings.yaml")
    if yaml_path.exists():
        return Settings.load_from_yaml(str(yaml_path))

    return Settings()


# 全局配置实例
settings = get_settings()
