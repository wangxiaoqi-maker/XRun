#!/bin/bash
# 安装所有依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📦 安装 UI 自动化平台依赖..."
echo ""

# 检查系统依赖
echo "🔍 检查系统依赖..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi
echo "✅ npm: $(npm --version)"

# 检查 adb
if command -v adb &> /dev/null; then
    echo "✅ adb: $(adb version | head -n 1)"
else
    echo "⚠️  adb 未安装 (Android 自动化需要)"
    echo "   macOS: brew install android-platform-tools"
fi

# 检查 tidevice
if command -v tidevice &> /dev/null; then
    echo "✅ tidevice: 已安装"
else
    echo "⚠️  tidevice 未安装 (iOS 自动化需要)"
    echo "   安装: pip install tidevice"
fi

echo ""

# 安装后端依赖
echo "📦 安装后端依赖..."
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q
echo "✅ 后端依赖安装完成"

# 安装执行器依赖
echo ""
echo "📦 安装执行器依赖..."
cd "$PROJECT_DIR/executor"
npm install --silent
echo "✅ 执行器依赖安装完成"

# 安装前端依赖
echo ""
echo "📦 安装前端依赖..."
cd "$PROJECT_DIR/frontend"
npm install --silent
echo "✅ 前端依赖安装完成"

echo ""
echo "🎉 所有依赖安装完成！"
echo ""
echo "下一步："
echo "  1. 启动服务: ./scripts/start-all.sh"
echo "  2. 访问前端: http://localhost:3000"
echo "  3. 在「AI 配置」页面添加大模型配置"

