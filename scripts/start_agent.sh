#!/bin/bash
# Sonic Agent 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
AGENT_DIR="$PROJECT_DIR/sonic-agent"

echo "=========================================="
echo "  Sonic Agent 启动脚本"
echo "=========================================="

# 检查 Agent 目录
if [ ! -d "$AGENT_DIR" ]; then
    echo "❌ 未找到 Sonic Agent 目录"
    echo ""
    echo "请手动下载 Sonic Agent："
    echo "1. 访问 https://github.com/SonicCloudOrg/sonic-agent/releases"
    echo "2. 下载 sonic-agent-v2.6.6-macos_arm64.zip (M1 Mac)"
    echo "   或 sonic-agent-v2.6.6-macos_x86_64.zip (Intel Mac)"
    echo "3. 解压到 $AGENT_DIR 目录"
    exit 1
fi

cd "$AGENT_DIR"

# 检查 agent.sh
if [ ! -f "agent.sh" ]; then
    echo "❌ 未找到 agent.sh"
    echo "请确保已正确解压 Sonic Agent"
    exit 1
fi

# 配置 Agent（独立模式，无需 Sonic Server）
if [ ! -f "config.properties" ]; then
    echo "创建配置文件..."
    cat > config.properties << EOF
# Sonic Agent 独立模式配置
# 不连接 Sonic Server，作为独立服务运行
sonic.agent.port=7912
sonic.agent.host=0.0.0.0
EOF
fi

echo ""
echo "📱 启动 Sonic Agent..."
echo "   端口: 7912"
echo "   API: http://localhost:7912"
echo ""

chmod +x agent.sh
./agent.sh








