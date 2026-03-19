#!/bin/bash
# 一键部署脚本 - Linux/Mac

set -e

echo "=========================================="
echo "  问卷星智能填写系统 - 一键部署"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查 Docker
check_docker() {
    echo "检查 Docker 环境..."
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker 未安装${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker 已安装${NC}"

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose 已安装${NC}"
}

# 检查端口
check_port() {
    echo ""
    echo "检查端口占用..."
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠ 端口 5000 已被占用${NC}"
        read -p "是否停止占用进程并继续? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:5000 | xargs kill -9 2>/dev/null || true
            echo -e "${GREEN}✓ 已释放端口 5000${NC}"
        else
            echo "部署已取消"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ 端口 5000 可用${NC}"
    fi
}

# 配置环境变量
setup_env() {
    echo ""
    echo "配置环境变量..."

    if [ ! -f .env ]; then
        if [ -f .env.docker ]; then
            cp .env.docker .env
            echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
        fi
    else
        echo -e "${GREEN}✓ .env 文件已存在${NC}"
    fi

    # 生成随机 SECRET_KEY
    if [ -f .env ]; then
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
        sed -i.bak "s/your-random-secret-key-change-this-in-production/$SECRET_KEY/" .env
        rm -f .env.bak
        echo -e "${GREEN}✓ 已生成随机 SECRET_KEY${NC}"
    fi
}

# 构建镜像
build_images() {
    echo ""
    echo "构建 Docker 镜像..."
    docker-compose build
    echo -e "${GREEN}✓ 镜像构建完成${NC}"
}

# 启动服务
start_services() {
    echo ""
    echo "启动服务..."
    docker-compose up -d
    echo -e "${GREEN}✓ 服务启动成功${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo ""
    echo "等待服务就绪..."
    sleep 10
    echo -e "${GREEN}✓ 服务已就绪${NC}"
}

# 显示信息
show_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}部署完成！${NC}"
    echo "=========================================="
    echo ""
    echo "访问地址: http://localhost:5000"
    echo ""
    echo "默认管理员账号:"
    echo "  用户名: Bear"
    echo "  密码: xzx123456"
    echo ""
    echo -e "${YELLOW}⚠ 请立即修改默认密码！${NC}"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose stop"
    echo "  启动服务: docker-compose start"
    echo "  重启服务: docker-compose restart"
    echo "  删除服务: docker-compose down"
    echo ""
    echo "=========================================="
}

# 主流程
main() {
    check_docker
    check_port
    setup_env
    build_images
    start_services
    wait_for_services
    show_info
}

# 执行
main
