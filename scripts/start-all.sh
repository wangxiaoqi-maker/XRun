#!/bin/bash
# 启动所有服务

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 启动 UI 自动化平台..."
echo ""

# 启动后端
echo "📦 启动后端服务..."
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# 后台启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 启动执行器依赖
echo ""
echo "📦 安装执行器依赖..."
cd "$PROJECT_DIR/executor"
npm install --silent

# 启动前端
echo ""
echo "📦 启动前端服务..."
cd "$PROJECT_DIR/frontend"
npm install --silent
npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "   🌐 前端: http://localhost:3000"
echo "   🔧 后端 API: http://localhost:8000"
echo "   📚 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait

