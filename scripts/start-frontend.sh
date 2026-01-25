#!/bin/bash
# 启动前端服务

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动前端服务..."

cd "$PROJECT_DIR/frontend"

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

echo ""
echo "🌐 启动服务..."
echo "   地址: http://localhost:3000"
echo ""

npm run dev

