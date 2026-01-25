#!/bin/bash
# 启动后端服务

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动后端服务..."

cd "$PROJECT_DIR/backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt -q

# 创建目录
mkdir -p static/screenshots static/reports data

echo ""
echo "🌐 启动服务..."
echo "   API: http://localhost:8000"
echo "   文档: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
