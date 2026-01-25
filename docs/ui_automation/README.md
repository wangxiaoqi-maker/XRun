# 📱 Android UI 自动化平台

基于 **Midscene AI** 和 **FastAPI** 构建的 Android UI 自动化测试平台。

## ✨ 功能特性

- 📺 **投屏功能** - 实时显示手机屏幕（基于 scrcpy）
- 🎬 **录制用例** - 记录用户操作，自动生成测试脚本
- ▶️ **回放用例** - 使用 Midscene AI 智能执行测试
- 📋 **用例管理** - 创建、编辑、组织测试用例
- 📊 **报告生成** - 自动生成可视化测试报告

## 🏗️ 技术栈

- **后端**: FastAPI + SQLAlchemy + WebSocket
- **执行引擎**: Midscene.js (AI UI 自动化)
- **投屏**: scrcpy
- **AI 模型**: 豆包 UI-TARS / 智谱 GLM-4V / OpenAI GPT-4V

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装系统依赖
# macOS
brew install android-platform-tools scrcpy

# Linux
sudo apt install android-tools-adb scrcpy

# 安装项目依赖
./scripts/install-deps.sh
```

### 2. 配置环境

```bash
# 复制配置文件
cp backend/.env.example backend/.env

# 编辑配置文件，添加 AI 模型 API Key
vim backend/.env
```

**豆包配置示例：**
```env
MIDSCENE_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MIDSCENE_MODEL_API_KEY=your-api-key
MIDSCENE_MODEL_NAME=doubao-1-5-ui-tars-250428
MIDSCENE_MODEL_FAMILY=vlm-ui-tars-doubao-1.5
```

### 3. 连接设备

```bash
# 确保设备已连接
adb devices

# 如果是小米设备，需要开启额外权限
# 设置 -> 更多设置 -> 开发者选项 -> USB 调试（安全设置）
```

### 4. 启动服务

```bash
# 启动后端
./scripts/start-backend.sh

# 访问 API 文档
open http://localhost:8000/docs
```

## 📖 API 接口

### 设备管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/devices` | 获取所有设备 |
| GET | `/api/devices/{id}` | 获取设备详情 |
| POST | `/api/devices/{id}/screenshot` | 截取屏幕 |
| POST | `/api/devices/{id}/tap` | 点击屏幕 |
| POST | `/api/devices/{id}/swipe` | 滑动屏幕 |
| WS | `/api/devices/{id}/mirror` | 投屏 WebSocket |

### 用例管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/cases` | 获取所有用例 |
| POST | `/api/cases` | 创建用例 |
| GET | `/api/cases/{id}` | 获取用例详情 |
| PUT | `/api/cases/{id}` | 更新用例 |
| DELETE | `/api/cases/{id}` | 删除用例 |

### 录制

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/recording/{device_id}/start` | 开始录制 |
| POST | `/api/recording/{device_id}/stop` | 停止录制 |
| GET | `/api/recording/{device_id}/status` | 获取录制状态 |
| WS | `/api/recording/{device_id}/events` | 实时事件流 |

### 执行

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/execution/run` | 执行用例 |
| GET | `/api/execution/{id}` | 获取执行状态 |
| WS | `/api/execution/{id}/logs` | 实时日志流 |
| POST | `/api/execution/batch` | 批量执行 |

## 📝 用例格式

```json
{
  "name": "登录测试",
  "description": "测试用户登录功能",
  "steps": [
    {
      "type": "ai_tap",
      "ai_prompt": "点击登录按钮",
      "description": "点击登录入口"
    },
    {
      "type": "input",
      "ai_prompt": "用户名输入框",
      "params": { "text": "testuser" },
      "description": "输入用户名"
    },
    {
      "type": "input",
      "ai_prompt": "密码输入框",
      "params": { "text": "123456" },
      "description": "输入密码"
    },
    {
      "type": "ai_tap",
      "ai_prompt": "确认登录按钮",
      "description": "提交登录"
    },
    {
      "type": "assert",
      "ai_prompt": "显示了首页或个人中心",
      "description": "验证登录成功"
    }
  ],
  "tags": ["login", "smoke"]
}
```

## 🎨 步骤类型

| 类型 | 描述 | 参数 |
|------|------|------|
| `ai_tap` | AI 智能点击 | `ai_prompt`: 描述要点击的元素 |
| `tap` | 坐标点击 | `params.x`, `params.y` |
| `swipe` | 滑动 | `params.start_x/y`, `params.end_x/y` |
| `input` | 输入文本 | `ai_prompt`, `params.text` |
| `assert` | 断言验证 | `ai_prompt`: 验证条件 |
| `wait` | 等待元素 | `ai_prompt`, `params.timeout` |
| `back` | 返回键 | - |
| `home` | Home 键 | - |
| `launch` | 启动应用 | `params.package`, `params.activity` |
| `sleep` | 等待时间 | `params.duration` |

## 📁 项目结构

```
ui_automation/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 数据模式
│   │   └── services/       # 业务服务
│   ├── requirements.txt
│   └── Dockerfile
│
├── midscene_executor/       # Midscene 执行器
│   ├── src/
│   │   ├── android_interface.js
│   │   └── executor.js
│   └── package.json
│
├── scripts/                 # 启动脚本
│   ├── start-backend.sh
│   └── install-deps.sh
│
├── docker-compose.yml
├── PLATFORM_DESIGN.md       # 详细设计文档
└── README.md
```

## 🔧 开发指南

### 添加新的步骤类型

1. 在 `AndroidInterface` 中添加方法
2. 在 `executor.js` 的 `executeStep` 中添加处理
3. 更新 `MidsceneService._generate_script` 生成脚本

### 自定义 AI 模型

支持任何 OpenAI 兼容的 API，配置方式：

```env
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://your-api-endpoint/v1
MIDSCENE_MODEL_NAME=your-model-name
```

## 📄 许可证

MIT License

## 🙏 致谢

- [Midscene.js](https://midscenejs.com/) - AI UI 自动化框架
- [scrcpy](https://github.com/Genymobile/scrcpy) - Android 投屏
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
