# 📱 UI 自动化平台

基于 **FastAPI + Vue 3 + Midscene AI** 的 iOS/Android UI 自动化测试平台。

## ✨ 功能特性

- 🎯 **组件化用例编辑** - 拖拽式操作，可视化编辑测试步骤
- 📱 **双平台支持** - 同时支持 iOS 和 Android 设备
- 🤖 **AI 智能执行** - 基于 Midscene AI 的智能元素定位
- 📋 **YAML 用例存储** - 用例以 YAML 格式存储，易于维护
- ⚙️ **大模型可配置** - 支持豆包、智谱、OpenAI 等多种 AI 服务
- 📊 **执行报告** - 自动生成可视化测试报告

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目后，运行安装脚本
./scripts/install.sh
```

### 2. 启动服务

```bash
# 同时启动前后端
./scripts/start-all.sh

# 或者分别启动
./scripts/start-backend.sh  # 后端 :8000
./scripts/start-frontend.sh # 前端 :3000
```

### 3. 配置 AI 模型

1. 访问 http://localhost:3000
2. 进入「AI 配置」页面
3. 添加大模型配置（推荐豆包 UI-TARS）

### 4. 连接设备

**Android：**
```bash
adb devices  # 确保设备已连接
```

**iOS：**
```bash
# 安装 tidevice
pip install tidevice

# 查看设备
tidevice list
```

## 📁 项目结构

```
ui_automation/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── cases.py    # 用例管理
│   │   │   ├── devices.py  # 设备管理
│   │   │   ├── execution.py # 用例执行
│   │   │   └── ai_config.py # AI 配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 数据模式
│   │   └── main.py         # 应用入口
│   └── requirements.txt
│
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── CasesView.vue      # 用例列表
│   │   │   ├── CaseEditorView.vue # 用例编辑器
│   │   │   ├── ExecutionsView.vue # 执行记录
│   │   │   ├── DevicesView.vue    # 设备管理
│   │   │   └── SettingsView.vue   # AI 配置
│   │   ├── api/            # API 调用
│   │   └── router/         # 路由配置
│   └── package.json
│
├── executor/                # Midscene 执行器
│   ├── src/
│   │   ├── android_interface.js
│   │   ├── ios_interface.js
│   │   └── index.js
│   └── package.json
│
└── scripts/                 # 启动脚本
    ├── install.sh
    ├── start-all.sh
    ├── start-backend.sh
    └── start-frontend.sh
```

## 📝 用例格式

用例以 YAML 格式存储：

```yaml
name: 登录测试
platform: android
steps:
  - type: launch
    description: 启动应用
    package: com.example.app
    
  - type: aiTap
    description: 点击登录按钮
    prompt: 点击登录按钮
    
  - type: aiInput
    description: 输入用户名
    prompt: 用户名输入框
    text: testuser
    
  - type: aiInput
    description: 输入密码
    prompt: 密码输入框
    text: "123456"
    
  - type: aiTap
    description: 提交登录
    prompt: 确认登录按钮
    
  - type: aiAssert
    description: 验证登录成功
    prompt: 显示了首页或个人中心
```

## 🎨 支持的操作类型

### AI 智能操作

| 类型 | 说明 | 参数 |
|------|------|------|
| `aiTap` | AI 智能点击 | `prompt`: 元素描述 |
| `aiInput` | AI 智能输入 | `prompt`: 输入框描述, `text`: 输入内容 |
| `aiSwipe` | AI 智能滑动 | `prompt`: 区域描述, `direction`: 方向 |
| `aiAssert` | AI 断言验证 | `prompt`: 验证条件 |
| `aiWait` | AI 等待元素 | `prompt`: 元素描述, `timeout`: 超时(ms) |
| `aiQuery` | AI 查询 | `prompt`: 查询内容 |

### 基础操作

| 类型 | 说明 | 参数 |
|------|------|------|
| `tap` | 坐标点击 | `x`, `y` |
| `swipe` | 坐标滑动 | `startX/Y`, `endX/Y`, `duration` |
| `input` | 文本输入 | `text` |

### 控制操作

| 类型 | 说明 | 参数 |
|------|------|------|
| `back` | 返回键 | - |
| `home` | Home 键 | - |
| `launch` | 启动应用 | Android: `package`, iOS: `bundleId` |
| `sleep` | 等待 | `duration`(ms) |
| `screenshot` | 截图 | - |

## ⚙️ AI 模型配置

支持多种大模型服务：

### 豆包 UI-TARS（推荐）

```
API 地址: https://ark.cn-beijing.volces.com/api/v3
模型名称: doubao-1-5-ui-tars-250428
模型系列: vlm-ui-tars-doubao-1.5
```

### 智谱 GLM-4V

```
API 地址: https://open.bigmodel.cn/api/paas/v4
模型名称: glm-4v-plus
```

### OpenAI GPT-4V

```
API 地址: https://api.openai.com/v1
模型名称: gpt-4-vision-preview
```

## 🔧 开发指南

### 添加新的操作类型

1. 在 `executor/src/index.js` 的 `executeStep` 函数中添加处理逻辑
2. 在前端 `CaseEditorView.vue` 的组件定义中添加新类型
3. 更新后端 `schemas/test_case.py` 的 `StepType` 枚举

### 自定义设备接口

实现 `AndroidInterface` 或 `IOSInterface` 接口：

```javascript
class CustomInterface {
  async size() { ... }
  async screenshotBase64() { ... }
  async tap(x, y) { ... }
  async swipe(startX, startY, endX, endY, duration) { ... }
  async input(text) { ... }
}
```

## 📄 许可证

MIT License








