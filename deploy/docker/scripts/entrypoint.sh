#!/bin/bash
set -e

echo "Starting Contract Application..."

# 等待 Oracle 数据库就绪
echo "Waiting for Oracle database..."
until (echo > /dev/tcp/${ORACLE_HOST:-oracle-db}/${ORACLE_PORT:-1521}) 2>/dev/null; do
    echo "Oracle is unavailable - sleeping"
    sleep 5
done

echo "Oracle is up!"

# 执行数据库迁移（如果有）
# python -m src.migrations.run

# 启动应用
echo "Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
