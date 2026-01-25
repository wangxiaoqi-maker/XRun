#!/bin/bash
# 启动移动端自动化前端

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODULE_DIR="$PROJECT_DIR/modules/mobile_automation"

echo "🎨 启动移动端自动化前端..."

cd "$MODULE_DIR/frontend"

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

echo ""
echo "🌐 启动服务..."
echo "   前端: http://localhost:5173"
echo ""

npm run dev
