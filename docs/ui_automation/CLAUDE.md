# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Android/iOS UI 自动化测试平台，基于 Midscene AI 和 FastAPI 构建。支持实时投屏、录制回放、智能用例执行，集成 Sonic 云真机平台。

**核心技术栈:**
- 后端: FastAPI + SQLAlchemy + WebSocket
- 前端: Vue 3 + Element Plus + Vite
- 执行引擎: Midscene.js (AI-powered UI automation)
- 投屏: scrcpy
- AI 模型: 豆包 UI-TARS / 智谱 GLM-4V / OpenAI GPT-4V
- 集成: Sonic 云真机平台

## Architecture

### Three-Tier Structure

```
Frontend (Vue 3)
    ↓ WebSocket + REST API
Backend (FastAPI)
    ↓ ADB/WDA + Node.js subprocess
Execution Layer (Midscene.js + scrcpy)
```

### Key Components

**Backend (`backend/app/`):**
- `api/` - REST/WebSocket endpoints (devices, cases, execution, ai_config)
- `services/` - Business logic:
  - `sonic_service.py` - Sonic cloud platform integration
  - `sonic_agent_service.py` - Sonic agent management
  - `ios_device_service.py` - iOS device lifecycle management via WDA
  - `ios_scheme_service.py` - iOS deep link URL scheme handling
- `models/` - SQLAlchemy ORM models (test_case, execution, ai_config, database)
- `schemas/` - Pydantic validation schemas

**Frontend (`frontend/src/`):**
- Vue 3 SPA with Element Plus UI components
- Real-time device mirroring via WebSocket
- Test case editor with Monaco Editor
- Execution monitoring with live logs

**Execution Engines:**
- `executor/` - Generic test executor (Node.js)
- `midscene_executor/` - Midscene AI executor
- `midscene_run/` - Midscene runtime environment

**Sonic Integration:**
- `sonic-agent/` - Sonic agent Docker container
- `sonic-server-v2.7.2/` - Sonic server instance
- Multiple deployment configs (docker-compose.yml, sonic-agent-compose.yml)

## Common Commands

### Development

```bash
# Start backend (FastAPI on port 8000)
./scripts/start-backend.sh

# Start frontend dev server (Vite on port 5173)
./scripts/start-frontend.sh

# Start both backend + frontend
./scripts/start-all.sh

# Restart all services (backend + frontend + cleanup)
./scripts/restart_all.sh

# Start Sonic agent
./scripts/start-agent.sh
```

### Backend

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server manually
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run on specific port
uvicorn app.main:app --port 8080
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Midscene Demo Scripts

```bash
# Root level Midscene demos (require dependencies from root package.json)
npm run demo          # Generic Android demo
npm run demo:wechat   # WeChat automation demo
npm run demo:browser  # Browser automation demo
npm run doubao        # Test Doubao UI-TARS model
npm run ios           # iOS automation demo
npm run test-demo     # Doubao integration test
```

### Device Management

```bash
# List connected devices
adb devices

# For Xiaomi devices, enable USB debugging security settings:
# 设置 -> 更多设置 -> 开发者选项 -> USB 调试（安全设置）

# iOS device check (requires pymobiledevice3)
tidevice list
```

### Sonic Platform

```bash
# Start Sonic server (requires .env configuration)
docker-compose up -d

# Stop Sonic server
docker-compose down

# View Sonic logs
docker-compose logs -f

# Access Sonic web UI
open http://localhost:3000
```

## Test Case Structure

Test cases are defined in JSON/YAML format with AI-powered or coordinate-based steps:

**Step Types:**
- `ai_tap` - AI smart click using natural language prompt
- `tap` - Coordinate-based click (x, y)
- `swipe` - Swipe gesture (start_x/y, end_x/y, duration)
- `input` - Text input (supports ai_prompt for element location)
- `assert` - AI verification assertion
- `wait` - Wait for element to appear
- `sleep` - Fixed time delay
- `back` - Device back button
- `home` - Device home button
- `launch` - Launch app by package name

**Example:**
```json
{
  "name": "登录测试",
  "steps": [
    {
      "type": "ai_tap",
      "ai_prompt": "点击登录按钮",
      "description": "点击登录入口"
    },
    {
      "type": "input",
      "ai_prompt": "用户名输入框",
      "params": { "text": "testuser" }
    },
    {
      "type": "assert",
      "ai_prompt": "显示了首页或个人中心"
    }
  ]
}
```

## Configuration

### Environment Variables

Backend configuration in `backend/.env`:
```env
# AI Model Configuration
MIDSCENE_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_NAME=doubao-1-5-ui-tars-250428
MIDSCENE_MODEL_FAMILY=vlm-ui-tars-doubao-1.5

# Or use OpenAI-compatible API
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://your-api-endpoint/v1
```

Sonic configuration in root `.env`:
```env
SONIC_SERVER_HOST=192.168.1.1
SONIC_SERVER_PORT=3000
MYSQL_HOST=192.168.1.1
MYSQL_DATABASE=sonic
```

### Database

- SQLite by default (stored in `backend/data/`)
- SQLAlchemy ORM with async support (aiosqlite)
- Auto-initialized on startup via `init_db()` in `app.main:lifespan`

## API Endpoints

**Devices:** `/api/devices`
- GET `/` - List all devices
- GET `/{id}` - Get device details
- POST `/{id}/screenshot` - Capture screenshot
- POST `/{id}/tap` - Tap screen
- POST `/{id}/swipe` - Swipe gesture
- WS `/{id}/mirror` - Real-time mirroring

**Cases:** `/api/cases`
- GET `/` - List test cases
- POST `/` - Create test case
- GET `/{id}` - Get case details
- PUT `/{id}` - Update test case
- DELETE `/{id}` - Delete test case

**Execution:** `/api/execution`
- POST `/run` - Execute test case
- GET `/{id}` - Get execution status
- WS `/{id}/logs` - Real-time execution logs
- POST `/batch` - Batch execution

**AI Config:** `/api/ai-config`
- Manage AI model configurations

## Development Workflow

### Adding New Step Types

1. Define step schema in `backend/app/schemas/test_case.py`
2. Implement step handler in executor (e.g., `executor/src/executor.js`)
3. If using Midscene AI, update `midscene_executor/src/executor.js`
4. Add UI support in frontend step editor

### iOS Device Integration

- iOS devices managed by `ios_device_service.py`
- Auto-discovery on startup (background task, non-blocking)
- Uses WebDriverAgent (WDA) for device control
- Deep link support via `ios_scheme_service.py`

### Sonic Integration Notes

- Sonic agent runs in Docker container (`sonic-agent/`)
- Backend service (`sonic_service.py`) communicates with Sonic API
- Agent service (`sonic_agent_service.py`) manages agent lifecycle
- Supports both Android and iOS device management

## File Structure

```
ui_automation/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routers
│   │   ├── core/              # Core config
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business services
│   ├── requirements.txt
│   └── venv/
│
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.js
│
├── executor/                   # Generic executor
│   └── src/
│
├── midscene_executor/          # Midscene AI executor
│   └── src/
│
├── sonic-agent/                # Sonic agent container
├── sonic-server-v2.7.2/        # Sonic server
│
├── scripts/                    # Startup scripts
│   ├── start-backend.sh
│   ├── start-frontend.sh
│   ├── start-all.sh
│   ├── restart_all.sh
│   └── start-agent.sh
│
├── docker-compose.yml          # Sonic server compose
├── sonic-agent-compose.yml     # Sonic agent compose
├── package.json                # Root Midscene demos
└── .env                        # Sonic configuration
```

## Key Dependencies

**Backend:**
- fastapi==0.115.0
- uvicorn[standard]==0.32.0
- sqlalchemy==2.0.36
- aiosqlite==0.20.0
- pydantic==2.10.0
- aiohttp==3.11.0
- websockets==12.0

**Frontend:**
- vue@^3.4.0
- element-plus@^2.5.0
- axios@^1.6.0
- monaco-editor@^0.45.0
- vite@^5.0.0

**Execution:**
- @midscene/android@^1.0.2
- @midscene/ios@^1.0.2
- @midscene/core@^1.0.0

## Troubleshooting

**Backend won't start:**
- Check Python 3.8+ is installed
- Ensure virtual environment is activated
- Verify all dependencies installed: `pip install -r backend/requirements.txt`

**iOS device not detected:**
- Ensure WebDriverAgent (WDA) is installed on device
- Check iOS service logs in backend startup output
- Service runs as background task - device may take time to appear

**Midscene execution fails:**
- Verify AI model API key in `backend/.env`
- Check model endpoint is accessible
- Review execution logs via WebSocket endpoint

**Sonic integration issues:**
- Verify MySQL is running and accessible
- Check Sonic server environment variables in `.env`
- Ensure Docker containers are running: `docker-compose ps`

## Documentation

- `README.md` - Quick start guide
- `IMPLEMENTATION_GUIDE.md` - Detailed architecture and implementation strategy
- `MAC_DEPLOYMENT.md` - macOS deployment guide
- `SERVER_DEPLOYMENT.md` - Server deployment guide
- `SONIC_INTEGRATION_GUIDE.md` - Sonic platform integration
- `SONIC_SETUP.md` - Sonic setup instructions
- `UI_TARS_DEPLOYMENT.md` - UI-TARS model deployment
- `README_PLATFORM.md` - Platform architecture overview
