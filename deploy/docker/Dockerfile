# 价格附件生成系统 - Docker 构建文件

# =============================================================================
# 阶段1: 构建依赖 (linux/amd64)
# =============================================================================
FROM --platform=linux/amd64 python:3.11-slim-bookworm AS builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存）
COPY pyproject.toml ./
COPY requirements.txt ./

# 安装 Python 依赖（如果 requirements.txt 没变，这层会被缓存）
RUN pip install --no-cache-dir --user --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# 再复制其余项目文件（这些改变不会导致 pip install 重新执行）
COPY src ./src
COPY config ./config
COPY deploy/docker/instantclient_11_2 ./instantclient_11_2

# =============================================================================
# 阶段2: 运行镜像
# =============================================================================
FROM --platform=linux/amd64 python:3.11-slim-bookworm

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libaio1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 Oracle Instant Client（本地已解压）
COPY --from=builder /app/instantclient_11_2 /opt/oracle/instantclient

# 复制 Python 依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY --from=builder /app/src /app/src
COPY --from=builder /app/config /app/config
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# 设置工作目录
WORKDIR /app

# 先创建目录并设置权限，再复制文件
RUN mkdir -p /app/output/downloads /app/logs /app/config

# 创建用户
RUN useradd -m -u 1000 appuser

# 复制文件并设置所有者
RUN cp -r /root/.local /home/appuser/.local && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /opt/oracle

# 设置环境变量
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient \
    LD_LIBRARY_PATH=/opt/oracle/instantclient:$LD_LIBRARY_PATH

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
