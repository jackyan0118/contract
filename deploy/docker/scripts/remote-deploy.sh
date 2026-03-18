#!/bin/bash
#
# 远程服务器部署脚本
# 在远程服务器上运行
#

set -e

# 配置
APP_DIR="/opt/contract-app"
IMAGE_NAME="docker-app"
IMAGE_TAG="latest"
COMPOSE_FILE="docker-compose.yml"

# 彩色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 部署函数
deploy() {
    log_info "开始部署..."

    # 创建应用目录
    log_info "创建应用目录: ${APP_DIR}"
    mkdir -p ${APP_DIR}

    # 复制 docker-compose 文件（需要预先配置）
    if [ ! -f "${APP_DIR}/${COMPOSE_FILE}" ]; then
        log_error "请先配置 ${APP_DIR}/${COMPOSE_FILE}"
        log_info "可以从以下位置复制模板:"
        log_info "  /path/to/project/deploy/docker/docker-compose.yml"
        exit 1
    fi

    # 启动服务
    log_info "启动服务..."
    cd ${APP_DIR}
    docker-compose up -d

    log_info "部署完成!"
    log_info "检查服务状态: docker-compose ps"
    log_info "查看日志: docker-compose logs -f"
}

# 查看状态
status() {
    cd ${APP_DIR}
    docker-compose ps
}

# 查看日志
logs() {
    cd ${APP_DIR}
    docker-compose logs -f
}

# 停止服务
stop() {
    cd ${APP_DIR}
    docker-compose down
}

# 重启服务
restart() {
    cd ${APP_DIR}
    docker-compose restart
}

# 显示用法
usage() {
    echo "用法: $0 {deploy|status|logs|stop|restart}"
    echo ""
    echo "命令:"
    echo "  deploy   - 部署应用"
    echo "  status   - 查看服务状态"
    echo "  logs     - 查看日志"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
}

# 主函数
case "$1" in
    deploy)
        deploy
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        usage
        exit 1
        ;;
esac
