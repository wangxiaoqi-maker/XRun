#!/bin/bash
# 安装移动端自动化模块的所有依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODULE_DIR="$PROJECT_DIR/modules/mobile_automation"

echo "=========================================="
echo "  安装移动端自动化模块依赖"
echo "=========================================="
echo ""

# 1. 后端依赖
echo "📦 1/3: 安装后端依赖..."
cd "$MODULE_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
deactivate

echo "✓ 后端依赖安装完成"
echo ""

# 2. 前端依赖
echo "📦 2/3: 安装前端依赖..."
cd "$MODULE_DIR/frontend"
npm install
echo "✓ 前端依赖安装完成"
echo ""

# 3. 执行器依赖
echo "📦 3/3: 安装执行器依赖..."
cd "$MODULE_DIR/executor"
npm install
echo "✓ 执行器依赖安装完成"
echo ""

echo "=========================================="
echo "✅ 所有依赖安装完成！"
echo "=========================================="
echo ""
echo "🚀 下一步："
echo "  1. 配置环境变量: vim .Env"
echo "  2. 启动后端: ./scripts/start_mobile_backend.sh"
echo "  3. 启动前端: ./scripts/start_mobile_frontend.sh"
echo ""
