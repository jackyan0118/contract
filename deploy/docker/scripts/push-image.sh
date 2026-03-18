#!/bin/bash
#
# Docker 镜像推送脚本
# 将镜像推送到远程服务器
#

# 配置
REMOTE_HOST="192.168.20.162"
REMOTE_USER="root"
REMOTE_PASSWORD="local_KHB_002022"
IMAGE_NAME="docker-app"
IMAGE_TAG="latest"
TEMP_DIR="/tmp/docker-deploy"

echo "=========================================="
echo "  Docker 镜像推送脚本"
echo "=========================================="
echo "目标服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo "镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# 检查 Docker
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker 未运行"
    exit 1
fi

# 检查镜像
if ! docker image inspect ${IMAGE_NAME}:${IMAGE_TAG} > /dev/null 2>&1; then
    echo "[ERROR] 镜像 ${IMAGE_NAME}:${IMAGE_TAG} 不存在"
    exit 1
fi

# 检查 sshpass
if ! command -v sshpass > /dev/null 2>&1; then
    echo "[ERROR] sshpass 未安装"
    exit 1
fi

# 导出镜像
echo "[INFO] 正在导出镜像..."
mkdir -p ${TEMP_DIR}
docker save -o ${TEMP_DIR}/${IMAGE_NAME}.tar ${IMAGE_NAME}:${IMAGE_TAG}
echo "[INFO] 镜像已导出"

# 复制到远程
echo "[INFO] 正在复制到远程服务器..."
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${TEMP_DIR}" 2>/dev/null
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no ${TEMP_DIR}/${IMAGE_NAME}.tar ${REMOTE_USER}@${REMOTE_HOST}:${TEMP_DIR}/
echo "[INFO] 镜像已复制到远程服务器"

# 加载镜像
echo "[INFO] 正在加载镜像..."
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "docker load -i ${TEMP_DIR}/${IMAGE_NAME}.tar"
echo "[INFO] 镜像加载完成"

# 清理
rm -rf ${TEMP_DIR}
echo "[INFO] 本地临时文件已清理"

echo ""
echo "=========================================="
echo "  推送完成!"
echo "=========================================="
echo ""
echo "在远程服务器上验证:"
echo "  docker images | grep ${IMAGE_NAME}"
echo ""
echo "启动容器:"
echo "  cd /opt/contract-app && docker-compose up -d"
