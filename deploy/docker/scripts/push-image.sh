#!/bin/bash
#
# Docker 镜像推送脚本
# 将镜像推送到远程服务器
#
# 包含: docker-app (应用) + nginx (反向代理)
#

# 配置
REMOTE_HOST="192.168.20.162"
REMOTE_USER="root"
REMOTE_PASSWORD="local_KHB_002022"
IMAGE_NAME="docker-app"
IMAGE_TAG="latest"
NGINX_IMAGE="nginx:alpine"
TEMP_DIR="/tmp/docker-deploy"

echo "=========================================="
echo "  Docker 镜像推送脚本"
echo "=========================================="
echo "目标服务器: ${REMOTE_USER}@${REMOTE_HOST}"
echo "镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Nginx: ${NGINX_IMAGE} (linux/amd64)"
echo ""

# 检查 Docker
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker 未运行"
    exit 1
fi

# 检查镜像
if ! docker image inspect ${IMAGE_NAME}:${IMAGE_TAG} > /dev/null 2>&1; then
    echo "[ERROR] 镜像 ${IMAGE_NAME}:${IMAGE_TAG} 不存在"
    echo "请先构建镜像: docker build -f deploy/docker/Dockerfile -t ${IMAGE_NAME}:${IMAGE_TAG} ."
    exit 1
fi

# 检查 sshpass
if ! command -v sshpass > /dev/null 2>&1; then
    echo "[ERROR] sshpass 未安装"
    exit 1
fi

# 创建临时目录
mkdir -p ${TEMP_DIR}

# 构建 amd64 架构的 nginx 镜像（远程服务器是 x86_64）
echo "[INFO] 构建 nginx amd64 镜像..."
if ! docker buildx build --platform linux/amd64 \
    -f - -t nginx:alpine-amd64 --load . <<'EOF'
FROM --platform=linux/amd64 nginx:alpine
EOF
then
    echo "[ERROR] nginx 镜像构建失败"
    exit 1
fi

# 导出镜像
echo "[INFO] 导出 docker-app 镜像..."
docker save -o ${TEMP_DIR}/${IMAGE_NAME}.tar ${IMAGE_NAME}:${IMAGE_TAG}

echo "[INFO] 导出 nginx 镜像..."
docker save -o ${TEMP_DIR}/nginx.tar nginx:alpine-amd64

echo "[INFO] 镜像已导出"

# 压缩传输
echo "[INFO] 压缩镜像文件..."
gzip -c ${TEMP_DIR}/${IMAGE_NAME}.tar > ${TEMP_DIR}/${IMAGE_NAME}.tar.gz
gzip -c ${TEMP_DIR}/nginx.tar > ${TEMP_DIR}/nginx.tar.gz
rm -f ${TEMP_DIR}/${IMAGE_NAME}.tar ${TEMP_DIR}/nginx.tar

# 复制到远程
echo "[INFO] 复制到远程服务器..."
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${TEMP_DIR}" 2>/dev/null
echo "[INFO] 复制 docker-app 镜像 (~30MB)..."
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no ${TEMP_DIR}/${IMAGE_NAME}.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${TEMP_DIR}/
echo "[INFO] 复制 nginx 镜像 (~25MB)..."
sshpass -p "${REMOTE_PASSWORD}" scp -o StrictHostKeyChecking=no ${TEMP_DIR}/nginx.tar.gz ${REMOTE_USER}@${REMOTE_HOST}:${TEMP_DIR}/

# 加载镜像
echo "[INFO] 远程服务器加载镜像..."
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} \
    "cd ${TEMP_DIR} && gunzip -c ${IMAGE_NAME}.tar.gz | docker load && gunzip -c nginx.tar.gz | docker load && docker tag nginx:alpine-amd64 nginx:alpine"
echo "[INFO] 镜像加载完成"

# 清理本地临时文件
rm -rf ${TEMP_DIR}
echo "[INFO] 本地临时文件已清理"

# 清理远程临时文件
sshpass -p "${REMOTE_PASSWORD}" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "rm -rf ${TEMP_DIR}" 2>/dev/null
echo "[INFO] 远程临时文件已清理"

echo ""
echo "=========================================="
echo "  推送完成!"
echo "=========================================="
echo ""
echo "验证镜像:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'docker images | grep -E \"docker-app|nginx\"'"
echo ""
echo "启动服务:"
echo "  ssh ${REMOTE_USER}@${REMOTE_HOST} 'cd /opt/contract-app && docker-compose -f docker-compose.remote.yml up -d'"
echo ""
echo "测试 API:"
echo "  curl http://${REMOTE_HOST}/api/v1/health"
