#!/bin/bash
# ========================================
# UI Automation → XRun 迁移脚本
# ========================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  UI Automation → XRun 迁移脚本"
echo "=========================================="
echo ""

# 配置路径
SOURCE_DIR="/Users/wangxiaoqi/Documents/翼支付工作文件/AI相关/ui_automation"
TARGET_DIR="/Users/wangxiaoqi/Documents/AI相关/github_ai/XRun"
MODULE_DIR="$TARGET_DIR/modules/mobile_automation"

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ 错误: 源目录不存在: $SOURCE_DIR${NC}"
    exit 1
fi

# 检查目标目录
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}❌ 错误: 目标目录不存在: $TARGET_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 迁移计划：${NC}"
echo "  源目录: $SOURCE_DIR"
echo "  目标目录: $TARGET_DIR"
echo "  模块目录: $MODULE_DIR"
echo ""

# 确认继续
read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "迁移已取消"
    exit 0
fi

echo ""
echo -e "${GREEN}🚀 开始迁移...${NC}"
echo ""

# ========================================
# 第一步：创建目录结构
# ========================================
echo "📁 步骤 1/7: 创建目录结构..."

mkdir -p "$MODULE_DIR"/{backend,frontend,executor,examples,infra,docs}
mkdir -p "$MODULE_DIR"/examples/{android,ios,web}
mkdir -p "$MODULE_DIR"/infra/{sonic,docker}
mkdir -p "$MODULE_DIR"/docs/{deployment,guides}
mkdir -p "$TARGET_DIR"/data/{logs,reports,screenshots,recordings}
mkdir -p "$TARGET_DIR"/scripts

echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# ========================================
# 第二步：迁移后端代码
# ========================================
echo "📦 步骤 2/7: 迁移后端代码..."

# 复制 backend 目录（排除 venv）
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' \
    "$SOURCE_DIR/backend/" "$MODULE_DIR/backend/"

echo -e "${GREEN}✓ 后端代码迁移完成${NC}"
echo ""

# ========================================
# 第三步：迁移前端代码
# ========================================
echo "🎨 步骤 3/7: 迁移前端代码..."

# 复制 frontend 目录（排除 node_modules）
rsync -av --exclude='node_modules' --exclude='dist' --exclude='.DS_Store' \
    "$SOURCE_DIR/frontend/" "$MODULE_DIR/frontend/"

echo -e "${GREEN}✓ 前端代码迁移完成${NC}"
echo ""

# ========================================
# 第四步：迁移执行器
# ========================================
echo "⚙️ 步骤 4/7: 迁移执行器..."

# 复制 executor（使用新版本）
rsync -av --exclude='node_modules' \
    "$SOURCE_DIR/executor/" "$MODULE_DIR/executor/"

echo -e "${GREEN}✓ 执行器迁移完成${NC}"
echo ""

# ========================================
# 第五步：迁移 Sonic Agent
# ========================================
echo "🔧 步骤 5/7: 迁移 Sonic Agent..."

# 复制 sonic-agent-src（您修改过的源码）
rsync -av --exclude='.git' --exclude='target' \
    "$SOURCE_DIR/sonic-agent-src/" "$MODULE_DIR/infra/sonic/agent-src/"

# 复制 sonic-agent 运行时（排除日志）
rsync -av --exclude='logs' --exclude='test-output' --exclude='*.log' \
    "$SOURCE_DIR/sonic-agent/" "$MODULE_DIR/infra/docker/sonic-agent/"

echo -e "${GREEN}✓ Sonic Agent 迁移完成${NC}"
echo ""

# ========================================
# 第六步：迁移示例代码
# ========================================
echo "📝 步骤 6/7: 迁移示例代码..."

cp "$SOURCE_DIR/demo-doubao.js" "$MODULE_DIR/examples/android/" 2>/dev/null || true
cp "$SOURCE_DIR/demo-ios.js" "$MODULE_DIR/examples/ios/" 2>/dev/null || true

echo -e "${GREEN}✓ 示例代码迁移完成${NC}"
echo ""

# ========================================
# 第七步：迁移文档
# ========================================
echo "📚 步骤 7/7: 迁移文档..."

# 创建 docs 目录
mkdir -p "$MODULE_DIR/docs/deployment"
mkdir -p "$MODULE_DIR/docs/guides"

# 复制文档
cp "$SOURCE_DIR/MAC_DEPLOYMENT.md" "$MODULE_DIR/docs/deployment/mac.md" 2>/dev/null || true
cp "$SOURCE_DIR/SERVER_DEPLOYMENT.md" "$MODULE_DIR/docs/deployment/server.md" 2>/dev/null || true
cp "$SOURCE_DIR/SONIC_SETUP.md" "$MODULE_DIR/docs/deployment/sonic.md" 2>/dev/null || true
cp "$SOURCE_DIR/SONIC_INTEGRATION_GUIDE.md" "$MODULE_DIR/docs/guides/sonic_integration.md" 2>/dev/null || true
cp "$SOURCE_DIR/README.md" "$MODULE_DIR/docs/guides/mobile_automation.md" 2>/dev/null || true

echo -e "${GREEN}✓ 文档迁移完成${NC}"
echo ""

# ========================================
# 生成迁移报告
# ========================================
echo "📊 生成迁移报告..."

REPORT_FILE="$TARGET_DIR/MIGRATION_REPORT.md"

cat > "$REPORT_FILE" << 'EOF'
# UI Automation → XRun 迁移报告

## 迁移完成时间
EOF

echo "$(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"

cat >> "$REPORT_FILE" << 'EOF'

## 迁移内容

### ✅ 已迁移模块

1. **后端代码** (`modules/mobile_automation/backend/`)
   - FastAPI 应用
   - 设备管理服务
   - Sonic 集成服务
   - iOS 设备服务
   - 执行服务

2. **前端代码** (`modules/mobile_automation/frontend/`)
   - Vue 3 + Element Plus
   - 设备投屏组件
   - 脚本编辑器
   - 用例管理

3. **执行器** (`modules/mobile_automation/executor/`)
   - Midscene.js 执行器
   - Android Interface
   - iOS Interface

4. **Sonic Agent** (`modules/mobile_automation/infra/sonic/`)
   - agent-src: 您修改过的源码
   - docker/sonic-agent: 运行时目录

5. **示例代码** (`modules/mobile_automation/examples/`)
   - Android 示例
   - iOS 示例

6. **文档** (`modules/mobile_automation/docs/`)
   - 部署文档
   - 集成指南

## 下一步操作

### 1. 安装依赖

```bash
# 后端依赖
cd modules/mobile_automation/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install

# 执行器依赖
cd ../executor
npm install
```

### 2. 配置环境变量

编辑 `.Env` 文件，添加以下配置：

```bash
# Sonic Server (云端)
SONIC_SERVER_URL=http://113.249.104.59:3001
SONIC_SERVER_USERNAME=sonic
SONIC_SERVER_PASSWORD=sonic

# Midscene AI
MIDSCENE_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_NAME=doubao-1-5-ui-tars-250428
```

### 3. 启动服务

```bash
# 启动后端
./scripts/start_mobile_backend.sh

# 启动前端
./scripts/start_mobile_frontend.sh
```

### 4. 访问应用

- 移动端前端: http://localhost:5173
- 移动端后端 API: http://localhost:8000/docs

## 注意事项

⚠️ **重要文件位置变更：**

| 原路径 | 新路径 |
|--------|--------|
| `ui_automation/backend/` | `XRun/modules/mobile_automation/backend/` |
| `ui_automation/frontend/` | `XRun/modules/mobile_automation/frontend/` |
| `ui_automation/sonic-agent-src/` | `XRun/modules/mobile_automation/infra/sonic/agent-src/` |
| `ui_automation/sonic-agent/` | `XRun/modules/mobile_automation/infra/docker/sonic-agent/` |

⚠️ **未迁移的文件（已清理）：**

- `midscene_executor/` - 已被 `executor/` 替代
- `sonic-server-v2.7.2/` - 使用云端 Docker 版本
- `docker-compose-zh.yml` - 冗余配置
- 旧日志和报告文件

EOF

echo -e "${GREEN}✓ 迁移报告已生成: $REPORT_FILE${NC}"
echo ""

# ========================================
# 完成
# ========================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ 迁移完成！${NC}"
echo "=========================================="
echo ""
echo "📋 迁移报告: $REPORT_FILE"
echo ""
echo "🚀 下一步操作："
echo "  1. 查看迁移报告: cat $REPORT_FILE"
echo "  2. 安装依赖: ./scripts/install_mobile_deps.sh"
echo "  3. 配置环境变量: vim .Env"
echo "  4. 启动服务: ./scripts/start_mobile_backend.sh"
echo ""
