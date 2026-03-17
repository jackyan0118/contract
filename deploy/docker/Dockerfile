# 价格附件生成系统 - Docker 构建文件
# Python 3.11 + Oracle Instant Client

# =============================================================================
# 阶段1: 构建依赖
# =============================================================================
FROM python:3.11-slim AS builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libaio1 \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir --user -e .

# =============================================================================
# 阶段2: 运行镜像
# =============================================================================
FROM python:3.11-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

# 复制 Python 依赖（从 builder 阶段）
COPY --from=builder /root/.local /home/appuser/.local

# 复制 Oracle Instant Client（本地目录，已下载到 deploy/docker/instantclient_21_19）
COPY deploy/docker/instantclient_21_19 /opt/oracle/instantclient

# 复制应用代码
COPY --from=builder /app /app

# 复制模板文件
COPY --chown=appuser:appuser templates /app/templates

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient \
    LD_LIBRARY_PATH=/opt/oracle/instantclient \
    TNS_ADMIN=/opt/oracle/instantclient/network/admin

# 创建必要目录
RUN mkdir -p /app/output/downloads /app/logs /app/config && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
