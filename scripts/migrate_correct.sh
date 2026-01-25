#!/bin/bash
# ========================================
# UI Automation → XRun 正确迁移方案
#
# 架构说明：
# - XRun 只有一个 FastAPI 后端
# - XRun 只有一个 Vue 3 前端
# - ui_automation 的前端就是 XRun 的前端
# - ui_automation 的后端作为 FastAPI 的一个 app 模块
# ========================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "  UI Automation → XRun 迁移脚本 v2.0"
echo "=========================================="
echo ""

# 配置路径
SOURCE_DIR="/Users/wangxiaoqi/Documents/翼支付工作文件/AI相关/ui_automation"
TARGET_DIR="/Users/wangxiaoqi/Documents/AI相关/github_ai/XRun"

# 检查目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ 错误: 源目录不存在${NC}"
    exit 1
fi

if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}❌ 错误: 目标目录不存在${NC}"
    exit 1
fi

echo -e "${BLUE}📋 迁移架构：${NC}"
echo "  • 前端: ui_automation/frontend → XRun/frontend (Vue 3 统一前端)"
echo "  • 后端: ui_automation/backend  → XRun/backend/apps/ui_automation (FastAPI 模块)"
echo "  • 执行器: executor → XRun/executors/midscene"
echo "  • Sonic: sonic-agent-src → XRun/infra/sonic/agent-src"
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
# 第一步：创建 XRun 目录结构
# ========================================
echo "📁 步骤 1/6: 创建 XRun 目录结构..."

mkdir -p "$TARGET_DIR"/backend/{apps,core,database,utils}
mkdir -p "$TARGET_DIR"/backend/apps/ui_automation
mkdir -p "$TARGET_DIR"/executors/midscene
mkdir -p "$TARGET_DIR"/infra/{sonic,docker}
mkdir -p "$TARGET_DIR"/data/{logs,reports,screenshots,recordings}
mkdir -p "$TARGET_DIR"/docs/{deployment,guides,api}
mkdir -p "$TARGET_DIR"/scripts
mkdir -p "$TARGET_DIR"/tests

echo -e "${GREEN}✓ 目录创建完成${NC}"
echo ""

# ========================================
# 第二步：迁移前端（整体迁移）
# ========================================
echo "🎨 步骤 2/6: 迁移前端代码（整体迁移，作为 XRun 唯一前端）..."

if [ -d "$TARGET_DIR/frontend" ]; then
    echo -e "${YELLOW}⚠️  frontend/ 目录已存在，备份为 frontend.bak${NC}"
    mv "$TARGET_DIR/frontend" "$TARGET_DIR/frontend.bak"
fi

# 完整复制前端（排除 node_modules）
rsync -av --exclude='node_modules' --exclude='dist' --exclude='.DS_Store' \
    "$SOURCE_DIR/frontend/" "$TARGET_DIR/frontend/"

echo -e "${GREEN}✓ 前端代码迁移完成（Vue 3 统一前端）${NC}"
echo ""

# ========================================
# 第三步：迁移后端（作为 FastAPI app）
# ========================================
echo "📦 步骤 3/6: 迁移后端代码（作为 FastAPI app 模块）..."

# 复制后端 app 目录到 backend/apps/ui_automation
rsync -av --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='data' \
    "$SOURCE_DIR/backend/app/" "$TARGET_DIR/backend/apps/ui_automation/"

# 复制 requirements.txt（后续需要合并）
cp "$SOURCE_DIR/backend/requirements.txt" "$TARGET_DIR/backend/requirements_ui_automation.txt"

echo -e "${GREEN}✓ 后端代码迁移完成${NC}"
echo ""

# ========================================
# 第四步：迁移执行器
# ========================================
echo "⚙️  步骤 4/6: 迁移 Midscene 执行器..."

rsync -av --exclude='node_modules' \
    "$SOURCE_DIR/executor/" "$TARGET_DIR/executors/midscene/"

echo -e "${GREEN}✓ 执行器迁移完成${NC}"
echo ""

# ========================================
# 第五步：迁移 Sonic Agent（重要！）
# ========================================
echo "🔧 步骤 5/6: 迁移 Sonic Agent（您修改过的源码）..."

# 复制 sonic-agent-src（您的修改）
echo "  → 复制 sonic-agent-src（源码）..."
rsync -av --exclude='.git' --exclude='target' \
    "$SOURCE_DIR/sonic-agent-src/" "$TARGET_DIR/infra/sonic/agent-src/"

# 复制 sonic-agent 运行时
echo "  → 复制 sonic-agent（运行时）..."
rsync -av --exclude='logs' --exclude='test-output' --exclude='*.log' \
    "$SOURCE_DIR/sonic-agent/" "$TARGET_DIR/infra/sonic/agent/"

echo -e "${GREEN}✓ Sonic Agent 迁移完成${NC}"
echo ""

# ========================================
# 第六步：迁移其他资源
# ========================================
echo "📚 步骤 6/6: 迁移文档和示例..."

# 迁移文档
mkdir -p "$TARGET_DIR/docs/ui_automation"
cp "$SOURCE_DIR"/*.md "$TARGET_DIR/docs/ui_automation/" 2>/dev/null || true

# 迁移示例代码
mkdir -p "$TARGET_DIR/examples/ui_automation/{android,ios}"
cp "$SOURCE_DIR/demo-doubao.js" "$TARGET_DIR/examples/ui_automation/android/" 2>/dev/null || true
cp "$SOURCE_DIR/demo-ios.js" "$TARGET_DIR/examples/ui_automation/ios/" 2>/dev/null || true

# 迁移脚本
cp "$SOURCE_DIR/scripts"/*.sh "$TARGET_DIR/scripts/" 2>/dev/null || true

echo -e "${GREEN}✓ 文档和示例迁移完成${NC}"
echo ""

# ========================================
# 创建 FastAPI 主文件
# ========================================
echo "🔨 创建 FastAPI 主文件..."

cat > "$TARGET_DIR/backend/main.py" << 'FASTAPI_MAIN'
"""
XRun - AI 驱动的自动化测试平台
FastAPI 后端主文件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

# 导入各个模块的路由
from apps.ui_automation.api import devices, cases, execution, ai_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    print("🚀 XRun 后端服务启动中...")

    # 初始化数据库
    from apps.ui_automation.database import init_db
    await init_db()

    # 创建必要目录
    os.makedirs("../data/screenshots", exist_ok=True)
    os.makedirs("../data/reports", exist_ok=True)
    os.makedirs("../data/logs", exist_ok=True)

    print("✅ XRun 后端服务启动成功")

    yield

    # 关闭时
    print("👋 XRun 后端服务关闭")

app = FastAPI(
    title="XRun - AI 驱动的自动化测试平台",
    description="支持 UI 自动化、API 测试、Web 自动化的一站式测试平台",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由 - UI 自动化模块
app.include_router(devices.router, prefix="/api/devices", tags=["设备管理"])
app.include_router(cases.router, prefix="/api/cases", tags=["用例管理"])
app.include_router(execution.router, prefix="/api/execution", tags=["用例执行"])
app.include_router(ai_config.router, prefix="/api/ai-config", tags=["AI配置"])

# 静态文件
os.makedirs("../data", exist_ok=True)
app.mount("/data", StaticFiles(directory="../data"), name="data")

@app.get("/")
async def root():
    return {
        "name": "XRun - AI 驱动的自动化测试平台",
        "version": "2.0.0",
        "modules": ["UI 自动化", "API 测试", "Web 自动化"],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
FASTAPI_MAIN

echo -e "${GREEN}✓ FastAPI 主文件创建完成${NC}"
echo ""

# ========================================
# 创建 requirements.txt
# ========================================
echo "📦 创建 requirements.txt..."

cat > "$TARGET_DIR/backend/requirements.txt" << 'REQUIREMENTS'
# FastAPI 核心
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12

# 数据库
sqlalchemy==2.0.36
aiosqlite==0.20.0

# 数据验证
pydantic==2.10.0
pydantic-settings==2.6.0

# YAML 处理
pyyaml==6.0.2

# 异步
aiohttp==3.11.0
aiofiles==24.1.0

# HTTP 客户端
httpx==0.27.0
websockets==12.0

# 工具
python-dotenv==1.0.1
loguru==0.7.3
greenlet==3.1.1

# AI 相关（根据需要添加）
# openai>=1.0.0
# anthropic>=0.8.0
REQUIREMENTS

echo -e "${GREEN}✓ requirements.txt 创建完成${NC}"
echo ""

# ========================================
# 更新 .gitignore
# ========================================
echo "📝 更新 .gitignore..."

cat >> "$TARGET_DIR/.gitignore" << 'GITIGNORE'

# ========================================
# XRun 项目特定忽略
# ========================================

# 运行时数据
data/logs/
data/reports/
data/screenshots/
data/recordings/

# Python
backend/venv/
backend/__pycache__/
backend/**/__pycache__/
backend/**/*.pyc
backend/**/*.pyo
backend/**/*.db

# Node.js
frontend/node_modules/
frontend/dist/
executors/*/node_modules/
examples/*/node_modules/

# Sonic
infra/sonic/agent/logs/
infra/sonic/agent/test-output/
infra/sonic/agent/*.log

# IDE
.idea/
.vscode/
*.swp
*.swo

# 备份
*.bak
.cleanup_backup/

# 临时文件
*.tmp
.DS_Store
GITIGNORE

echo -e "${GREEN}✓ .gitignore 更新完成${NC}"
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

## ✅ 迁移架构

### 🎯 XRun 项目结构

```
XRun/
├── backend/                      # FastAPI 后端（统一后端）
│   ├── apps/
│   │   └── ui_automation/       # UI 自动化模块（来自 ui_automation/backend/app）
│   │       ├── api/             # REST API
│   │       ├── services/        # Sonic/iOS/执行服务
│   │       ├── models/          # 数据模型
│   │       └── schemas/         # Pydantic schemas
│   ├── core/                    # 核心配置
│   ├── database/                # 数据库
│   ├── main.py                  # FastAPI 主文件
│   └── requirements.txt         # 依赖
│
├── frontend/                     # Vue 3 前端（统一前端，来自 ui_automation/frontend）
│   ├── src/
│   │   ├── views/               # 所有页面
│   │   │   ├── Dashboard/       # 数据看板
│   │   │   ├── app/             # UI 自动化页面（设备、脚本、任务等）
│   │   │   └── ui/              # 其他 UI 页面
│   │   ├── components/          # DeviceMirror 等组件
│   │   ├── api/                 # API 层
│   │   └── router/              # 路由
│   ├── package.json
│   └── vite.config.js
│
├── executors/
│   └── midscene/                # Midscene 执行器
│       ├── src/
│       │   ├── android_interface.js
│       │   ├── ios_interface.js
│       │   └── index.js
│       └── package.json
│
├── infra/
│   └── sonic/
│       ├── agent-src/           # 您修改过的 Sonic Agent 源码（重要！）
│       └── agent/               # Sonic Agent 运行时
│
├── data/                        # 运行时数据（gitignore）
│   ├── logs/
│   ├── reports/
│   └── screenshots/
│
├── docs/                        # 文档
│   └── ui_automation/           # UI 自动化相关文档
│
├── examples/                    # 示例代码
│   └── ui_automation/
│       ├── android/
│       └── ios/
│
└── scripts/                     # 工具脚本
```

## 🎯 关键变更

### 1. **前端架构**
- ✅ `ui_automation/frontend/` → `XRun/frontend/`
- ✅ 这是 XRun 的**唯一前端**，使用 Vue 3
- ✅ 包含所有功能模块的页面（UI 自动化、API 测试、Web 自动化等）

### 2. **后端架构**
- ✅ `ui_automation/backend/app/` → `XRun/backend/apps/ui_automation/`
- ✅ 作为 FastAPI 的一个**应用模块**
- ✅ XRun 只有一个 FastAPI 后端，所有模块共享

### 3. **Sonic Agent**
- ✅ 源码保留：`infra/sonic/agent-src/`（您的修改版本）
- ✅ 运行时：`infra/sonic/agent/`
- ⚠️ Sonic Server 使用云端部署：http://113.249.104.59:3001

## 🚀 下一步操作

### 1. 安装依赖

```bash
# 后端依赖
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install

# 执行器依赖
cd ../executors/midscene
npm install
```

### 2. 配置环境变量

编辑 `.Env` 文件，添加：

```bash
# ========================================
# XRun 配置
# ========================================

# Sonic Server（云端）
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
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（新终端）
cd frontend
npm run dev
```

### 4. 访问应用

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/docs

## ⚠️ 注意事项

### 导入路径调整

由于后端目录结构变化，需要调整导入路径：

```python
# 原路径（ui_automation）
from app.api import devices
from app.services import sonic_service

# 新路径（XRun）
from apps.ui_automation.api import devices
from apps.ui_automation.services import sonic_service
```

### 前端 API 调用

前端 API 基础路径保持不变（`/api`），但现在由 XRun 统一后端处理。

## ✅ 迁移完成检查

- [ ] 后端依赖安装成功
- [ ] 前端依赖安装成功
- [ ] 执行器依赖安装成功
- [ ] 环境变量配置完成
- [ ] 后端启动成功（访问 /docs）
- [ ] 前端启动成功（访问 /）
- [ ] 设备列表可以加载
- [ ] 投屏功能正常
- [ ] Sonic Agent 可以连接

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
echo -e "${BLUE}📊 迁移总结：${NC}"
echo "  ✓ 前端：Vue 3 统一前端（来自 ui_automation/frontend）"
echo "  ✓ 后端：FastAPI 模块（backend/apps/ui_automation）"
echo "  ✓ 执行器：Midscene（executors/midscene）"
echo "  ✓ Sonic Agent：源码已保留（infra/sonic/agent-src）"
echo ""
echo "📋 迁移报告: $REPORT_FILE"
echo ""
echo "🚀 下一步："
echo "  1. 查看报告: cat MIGRATION_REPORT.md"
echo "  2. 安装依赖: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "  3. 启动后端: uvicorn main:app --reload"
echo "  4. 启动前端: cd frontend && npm install && npm run dev"
echo ""
