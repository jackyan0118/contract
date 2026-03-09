"""数据库配置模块."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

import oracledb

from src.config import DatabaseSettings, settings


@dataclass
class DatabaseConfig:
    """数据库配置类."""

    dsn: str
    schema: str = ""  # Oracle Schema/用户
    min_connections: int = 2
    max_connections: int = 10
    pool_increment: int = 1
    connect_timeout: int = 30
    command_timeout: int = 60
    max_lifetime: int = 3600  # 连接最大生命周期（秒）
    retry_attempts: int = 3  # 重试次数
    retry_delay: float = 0.5  # 重试延迟（秒）

    @classmethod
    def from_settings(cls, db_settings: DatabaseSettings) -> DatabaseConfig:
        """从应用设置创建配置.

        Args:
            db_settings: 数据库配置对象

        Returns:
            DatabaseConfig 实例
        """
        return cls(
            dsn=db_settings.get_dsn(),
            schema=db_settings.db_schema,
            min_connections=db_settings.min_connections,
            max_connections=db_settings.max_connections,
            pool_increment=db_settings.pool_increment,
            connect_timeout=db_settings.connect_timeout,
            command_timeout=db_settings.command_timeout,
        )

    def get_qualified_table(self, table_name: str) -> str:
        """获取带 schema 的表名.

        Args:
            table_name: 原始表名

        Returns:
            带 schema 的表名，如 "schema.table_name"
        """
        if not self.schema:
            return table_name
        if "." in table_name:  # 已有 schema 前缀
            return table_name
        return f"{self.schema}.{table_name}"

    def to_oracledb_params(self) -> dict:
        """转换为 oracledb 连接参数（安全方式）.

        使用 python-oracledb 的安全解析方式解析 DSN，
        避免手动字符串分割导致敏感信息泄露。

        Returns:
            包含连接参数的字典
        """
        try:
            # 使用 python-oracledb 的安全解析方式
            parsed = oracledb.parse_dsn(self.dsn)
            return {
                "user": parsed.get("user", ""),
                "password": parsed.get("password", ""),
                "dsn": oracledb.makedsn(
                    parsed.get("host", "localhost"),
                    parsed.get("port", 1521),
                    parsed.get("service_name", "ORCL"),
                ),
            }
        except Exception:
            # 回退到手动解析（仅用于兼容旧格式）
            # 格式: oracle://user:password@host:1521/service_name
            parts = self.dsn.replace("oracle://", "").split("@")
            if len(parts) < 2:
                return {"dsn": self.dsn}

            user_info = parts[0].split(":")
            host_port_service = parts[1].split("/")

            user = user_info[0] if len(user_info) > 0 else ""
            password = user_info[1] if len(user_info) > 1 else ""
            host_port = host_port_service[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 1521
            service_name = host_port_service[1] if len(host_port_service) > 1 else "ORCL"

            return {
                "user": user,
                "password": password,
                "dsn": oracledb.makedsn(host, port, service_name),
            }


# 全局配置实例
_config: Optional[DatabaseConfig] = None
_config_lock = threading.Lock()


def get_database_config() -> DatabaseConfig:
    """获取数据库配置实例（线程安全单例）.

    Returns:
        DatabaseConfig 实例
    """
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = DatabaseConfig.from_settings(settings.database)
    return _config
