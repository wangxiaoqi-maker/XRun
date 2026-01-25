#!/bin/bash
set -e

echo "=========================================="
echo "重启所有 Sonic 服务"
echo "=========================================="

# 停止旧的 Agent 进程
echo "[1/5] 停止旧的 Sonic Agent..."
pkill -9 -f "sonic-agent" 2>/dev/null || true
sleep 2

# 检查端口
echo "[2/5] 检查端口 7777..."
if lsof -i :7777 >/dev/null 2>&1; then
    echo "端口 7777 仍被占用，强制停止..."
    kill -9 $(lsof -t -i :7777) 2>/dev/null || true
    sleep 2
fi
echo "端口 7777 空闲"

# 重启 Gateway
echo "[3/5] 重启 Sonic Gateway..."
cd /Users/wangxiaoqi/Documents/翼支付工作文件/AI相关/ui_automation/sonic-server-v2.7.2
docker compose -f docker-compose-zh.yml restart sonic-server-gateway

echo "[4/5] 等待服务启动..."
sleep 10

# 启动 Agent
echo "[5/5] 启动 Sonic Agent..."
cd /Users/wangxiaoqi/Documents/翼支付工作文件/AI相关/ui_automation/sonic-agent
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home
nohup $JAVA_HOME/bin/java -Dfile.encoding=utf-8 -jar sonic-agent-macosx-arm64.jar > /tmp/sonic-agent.log 2>&1 &

echo "等待 Agent 启动..."
sleep 15

# 检查状态
echo ""
echo "=========================================="
echo "服务状态"
echo "=========================================="
echo "Docker 容器:"
docker ps --format "  {{.Names}}: {{.Status}}" | grep sonic

echo ""
echo "Sonic Agent:"
if lsof -i :7777 >/dev/null 2>&1; then
    echo "  运行中 (端口 7777)"
else
    echo "  未运行"
fi

echo ""
echo "Agent 日志 (最后 10 行):"
tail -10 /tmp/sonic-agent.log 2>/dev/null || echo "  无日志"

echo ""
echo "=========================================="
echo "完成！请刷新页面 http://localhost:5173 测试投屏"
echo "=========================================="

