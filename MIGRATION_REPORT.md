# UI Automation → XRun 迁移报告

## 迁移完成时间
2026-01-25 16:50:01

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

