# XRun 项目结构文档

> XRun - AI 驱动的自动化测试平台
> 
> 支持 UI 自动化、API 测试、Web 自动化的一站式测试平台

---

## 目录结构概览

```
XRun/
├── backend/                    # 后端服务 (FastAPI + Python)
│   ├── apps/                   # 业务应用模块
│   │   └── ui_automation/      # UI 自动化核心模块
│   ├── llm/                    # 大模型客户端
│   ├── scripts/                # 数据库迁移脚本
│   ├── main.py                 # 后端入口文件
│   └── requirements.txt        # Python 依赖
├── frontend/                   # 前端应用 (Vue 3 + Element Plus)
│   ├── src/                    # 源代码
│   │   ├── api/                # API 接口封装
│   │   ├── components/         # 公共组件
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── styles/             # 全局样式
│   │   └── views/              # 页面视图
│   ├── package.json            # 前端依赖
│   └── vite.config.js          # Vite 构建配置
├── docs/                       # 项目文档
├── scripts/                    # 部署/启动脚本
└── infra/                      # 基础设施 (Sonic Agent)
```

---

## 一、后端 (Backend)

### 1.1 入口文件

| 文件 | 说明 |
|-----|------|
| `main.py` | **后端入口**，FastAPI 应用初始化、路由注册、生命周期管理（数据库初始化、iOS 设备监听服务启动等） |
| `requirements.txt` | Python 主要依赖列表 |
| `requirements_ui_automation.txt` | UI 自动化模块专用依赖 |

---

### 1.2 apps/ui_automation/ - UI 自动化核心模块

#### 1.2.1 根目录配置

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `config.py` | **应用配置**，包含数据库 URL、Sonic 配置、AI 模型配置、文件存储路径等 |
| `database.py` | **数据库配置**，SQLAlchemy 异步引擎、连接池配置（支持 MySQL/SQLite）、会话工厂 |

---

#### 1.2.2 api/ - API 路由层

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `auth.py` | **认证 API**：用户登录、注册、获取当前用户、修改密码、用户管理（管理员） |
| `project.py` | **项目管理 API**：项目 CRUD、项目成员管理、权限控制 |
| `app.py` | **应用管理 API**：App 应用 CRUD、关联项目 |
| `devices.py` | **设备管理 API**：设备列表、设备控制（点击/滑动/输入）、截图、WebSocket 投屏、iOS/Android 设备操作 |
| `cases.py` | **用例管理 API**：测试用例 CRUD、YAML 验证、从步骤创建用例 |
| `execution.py` | **用例执行 API**：执行用例、查询执行记录、WebSocket 日志流 |
| `ai_config.py` | **AI 配置 API**：AI 模型配置 CRUD、激活配置、测试连接 |
| `llm_config.py` | **LLM 配置 API**：大模型供应商管理、模型管理、用量统计 |

---

#### 1.2.3 models/ - 数据模型层 (SQLAlchemy ORM)

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化，导出所有模型 |
| `user.py` | **用户模型**：id、username、email、password_hash、role（admin/member）、avatar、is_active |
| `project.py` | **项目模型**：Project（项目）、ProjectMember（项目成员关联，含角色） |
| `app.py` | **应用模型**：App 应用，关联项目，包含包名、平台、图标、版本等信息 |
| `test_case.py` | **测试用例模型**：用例名称、描述、YAML 内容、平台、状态、关联项目和应用 |
| `execution.py` | **执行记录模型**：执行状态、开始/结束时间、设备信息、日志、结果 |
| `ai_config.py` | **AI 配置模型**：模型名称、Base URL、API Key、是否激活 |
| `llm_config.py` | **LLM 配置模型**：LLMProvider（供应商）、LLMModel（模型）、LLMUsageLog（用量日志） |

---

#### 1.2.4 schemas/ - Pydantic 数据校验

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `device.py` | 设备相关 Schema：DeviceInfo、DeviceAction、ScreenshotResponse |
| `test_case.py` | 用例相关 Schema：TestCaseCreate、TestCaseUpdate、TestCaseResponse |
| `execution.py` | 执行相关 Schema：ExecutionCreate、ExecutionResponse、ExecutionLog |
| `ai_config.py` | AI 配置 Schema：AIConfigCreate、AIConfigUpdate、AIConfigResponse |

---

#### 1.2.5 services/ - 业务服务层

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `auth_service.py` | **认证服务**：密码加密/验证、JWT 生成/解析、管理员初始化、用户认证 |
| `ios_device_service.py` | **iOS 设备服务**：使用 tidevice 管理 iOS 设备，WDA 启动、设备监听、截图、控制 |
| `ios_scheme_service.py` | **iOS Scheme 服务**：URL Scheme 跳转功能 |
| `sonic_service.py` | **Sonic 服务**：与 Sonic Server 通信，获取设备列表、设备控制、调试会话 |
| `sonic_agent_service.py` | **Sonic Agent 服务**：与本地 Sonic Agent 通信，WebSocket 代理、设备操作 |

---

#### 1.2.6 knowledge/ - AI 知识库模块

##### api/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 导出路由：`router`（页面分析）、`exploration_router`（知识图谱探索） |
| `page_analysis.py` | **页面分析 API**：AI 分析页面截图、保存到知识库、语义搜索元素、页面/元素 CRUD、统计信息 |
| `exploration.py` | **知识图谱探索 API**：开始/结束探索会话、记录页面跳转、获取 App 图谱、路径查找 |

##### models/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 导出所有模型、知识库 Base 类 |
| `base.py` | 知识库 Base 基类，带 `created_at`、`updated_at` 自动时间戳 |
| `enums.py` | 枚举定义：ElementType（元素类型）、ActionType（动作类型） |
| `app_info.py` | **AppInfo 模型**：应用信息，包含 app_id、名称、包名等 |
| `page_analysis.py` | **PageAnalysis 模型**：页面分析结果，包含页面标题、截图 URL、关联应用/项目 |
| `page_element.py` | **PageElement 模型**：页面元素，包含元素名称、类型、坐标、描述、是否导航元素、切图 URL |
| `page_transition.py` | **PageTransition 模型**：页面跳转关系，记录从哪个页面通过哪个元素跳转到哪个页面 |

##### repositories/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 导出所有仓库类 |
| `base.py` | **基础仓库类**：通用 CRUD 操作（create、get、update、delete、list） |
| `page_repository.py` | **页面仓库**：PageAnalysis 的数据库操作 |
| `element_repository.py` | **元素仓库**：PageElement 的数据库操作 |
| `app_repository.py` | **应用仓库**：AppInfo 的数据库操作 |

##### schemas/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `page_analysis.py` | 页面分析相关 Schema：AnalyzePageRequest、AnalyzePageResponse、PageElementSchema |

##### services/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `page_analyzer_service.py` | **页面分析服务**：调用 AI 模型分析页面截图，解析元素信息，生成分析结果 |
| `knowledge_service.py` | **知识库服务**：保存分析结果到数据库、管理页面和元素 |
| `embedding_service.py` | **向量嵌入服务**：文本向量化、语义相似度计算 |
| `vector_service.py` | **向量检索服务**：向量数据库操作（存储、检索） |
| `exploration_service.py` | **知识图谱探索服务**：管理探索会话、记录页面跳转、构建导航图 |
| `minio_service.py` | **MinIO 服务**：对象存储，存储截图和元素切图 |
| `crop_service.py` | **图片裁剪服务**：根据坐标裁剪元素图片 |
| `cache_service.py` | **缓存服务**：内存缓存，优化 API 响应速度 |

##### utils/

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `timezone.py` | **时区工具**：UTC 转北京时间，统一时间处理 |

---

### 1.3 llm/ - 大模型客户端

| 文件 | 说明 |
|-----|------|
| `__init__.py` | 模块初始化 |
| `client.py` | **LLM 客户端**：统一的大模型调用接口，支持 OpenAI 兼容 API，带用量记录 |

---

### 1.4 scripts/ - 数据库迁移脚本

| 文件 | 说明 |
|-----|------|
| `migrate_sqlite_to_mysql.py` | SQLite 迁移到 MySQL 的脚本 |
| `migrate_to_cloud.py` | 本地数据迁移到云端数据库的脚本 |

---

## 二、前端 (Frontend)

### 2.1 根目录配置

| 文件 | 说明 |
|-----|------|
| `index.html` | 入口 HTML 文件 |
| `package.json` | 前端依赖配置（Vue 3、Element Plus、Axios、Pinia 等） |
| `vite.config.js` | Vite 构建配置（代理、别名等） |

---

### 2.2 src/ - 源代码

#### 2.2.1 入口文件

| 文件 | 说明 |
|-----|------|
| `main.js` | **前端入口**：创建 Vue 应用、注册插件（Pinia、Router、Element Plus）、注册全局图标 |
| `App.vue` | **根组件**：整体布局（侧边栏导航 + 顶部标签页 + 内容区），动态 keep-alive 缓存管理 |

---

#### 2.2.2 api/ - API 接口封装

| 文件 | 说明 |
|-----|------|
| `index.js` | **统一 API 封装**：Axios 实例配置、请求/响应拦截器、各模块 API 导出 |

**包含的 API 模块**：
- `authApi` - 认证（登录、注册、用户管理）
- `projectApi` - 项目管理
- `appApi` - 应用管理
- `deviceApi` - 设备管理（Android/iOS、截图、控制、投屏）
- `caseApi` - 用例管理
- `executionApi` - 用例执行
- `aiConfigApi` - AI 配置
- `knowledgeApi` - AI 知识库（页面分析、元素搜索）
- `explorationApi` - 知识图谱探索
- `llmApi` - LLM 供应商/模型管理、用量统计
- `systemApi` - 系统健康检查

---

#### 2.2.3 router/ - 路由配置

| 文件 | 说明 |
|-----|------|
| `index.js` | **Vue Router 配置**：路由表定义、路由守卫（认证检查、页面标题设置） |

**路由结构**：
```
/login              - 登录页
/register           - 注册页
/dashboard          - 数据看板
/ui/apps            - 应用管理
/ui/mirror          - 真机调试
/ui/scripts         - 脚本管理
/ui/scripts/new     - 新建脚本
/ui/scripts/:id/edit - 编辑脚本
/ui/knowledge       - 页面知识库
/ui/knowledge/new   - 新增页面分析
/ui/knowledge/:id   - 页面详情
/ui/tasks           - 任务管理
/ui/reports         - 测试报告
/project/manage     - 项目管理
/llm/providers      - LLM 供应商配置
/llm/usage          - LLM 用量统计
/settings           - 系统设置
```

---

#### 2.2.4 stores/ - Pinia 状态管理

| 文件 | 说明 |
|-----|------|
| `user.js` | **用户状态**：当前登录用户信息、登录状态、登录/登出方法 |
| `project.js` | **项目状态**：当前选中项目、项目列表、切换项目方法 |

---

#### 2.2.5 styles/ - 全局样式

| 文件 | 说明 |
|-----|------|
| `global.scss` | **全局样式**：CSS 变量定义（主题色、字体、间距）、通用样式类、Element Plus 样式覆盖 |

---

#### 2.2.6 components/ - 公共组件

| 文件 | 说明 |
|-----|------|
| `DeviceMirror.vue` | **设备投屏组件**：支持 iOS/Android 设备实时画面显示、触控操作（点击、滑动）、截图 |
| `AITeachingPanel.vue` | **AI 教学面板**：页面分析配置、AI 模型选择、分析结果展示、元素列表、保存到知识库 |
| `ElementOverlay.vue` | **元素覆盖层**：在设备投屏上绘制元素边框，高亮显示识别到的 UI 元素 |
| `SmartStepInput.vue` | **智能步骤输入**：用例步骤的智能输入组件，支持动作类型联想、参数输入 |
| `demo.vue` | **样式 Demo**：脚本管理页面的样式参考组件 |

---

#### 2.2.7 views/ - 页面视图

##### 根目录视图

| 文件 | 说明 |
|-----|------|
| `LoginView.vue` | **登录页**：用户登录表单，JWT 认证 |
| `RegisterView.vue` | **注册页**：用户注册表单 |
| `DashboardView.vue` | **数据看板**：平台概览、统计数据展示 |
| `ProjectManageView.vue` | **项目管理**：项目 CRUD、成员管理、权限分配 |
| `SettingsView.vue` | **系统设置**：全局配置 |
| `PlaceholderView.vue` | **占位页面**：待开发功能的占位 |
| `DemoView.vue` | **样式预览**：用于调试和预览组件样式 |

##### views/app/ - UI 自动化视图

| 文件 | 说明 |
|-----|------|
| `MirrorView.vue` | **真机调试**：设备列表、设备连接、实时投屏、设备控制、AI 页面分析入口 |
| `ScriptsView.vue` | **脚本管理**：脚本列表、目录树管理、筛选搜索、脚本 CRUD |
| `ScriptEditorView.vue` | **脚本编辑器**：用例步骤编辑、设备投屏、AI 分析、步骤拖拽排序、智能步骤输入 |
| `TasksView.vue` | **任务管理**：执行任务列表、任务状态、执行进度、结果统计 |
| `ReportView.vue` | **测试报告**：执行报告展示、历史记录 |

##### views/ui/ - UI 知识库视图

| 文件 | 说明 |
|-----|------|
| `AppManageView.vue` | **应用管理**：App 应用 CRUD、应用卡片展示、关联项目 |
| `PageKnowledgeView.vue` | **页面知识库**：已分析页面列表、卡片展示、统计数据、新增分析入口 |
| `PageAnalysisView.vue` | **页面分析**：设备投屏、AI 分析配置、分析结果展示、保存到知识库 |
| `PageDetailView.vue` | **页面详情**：页面信息编辑、元素列表、元素编辑/删除、元素切图查看 |

##### views/llm/ - LLM 配置视图

| 文件 | 说明 |
|-----|------|
| `ProvidersView.vue` | **模型供应商**：LLM 供应商 CRUD、模型管理、API Key 配置 |
| `UsageView.vue` | **用量统计**：Token 使用量、费用统计、趋势图表 |

---

#### 2.2.8 assets/ - 静态资源

| 文件 | 说明 |
|-----|------|
| `logo.svg` | 平台 Logo |
| `icon_android.svg` | Android 图标 |
| `icon_apple.svg` | iOS (Apple) 图标 |
| `android_placeholder.svg` | Android 设备占位图 |
| `iphone_placeholder.svg` | iPhone 设备占位图 |
| `pad_placeholder.svg` | iPad 设备占位图 |
| `phone_placeholder.svg` | 通用手机占位图 |
| `phone_placeholder_color.svg` | 彩色手机占位图 |

---

## 三、核心功能模块说明

### 3.1 用户认证与权限

- **JWT 认证**：登录后返回 Token，前端存储到 localStorage
- **角色**：admin（管理员）、member（普通成员）
- **项目权限**：项目级别的成员管理和权限控制

### 3.2 设备管理

- **Sonic 集成**：通过 Sonic Server 管理 Android 设备
- **iOS 原生支持**：使用 tidevice + WebDriverAgent 管理 iOS 设备
- **实时投屏**：WebSocket 推送设备画面
- **设备控制**：点击、滑动、输入、Home、返回等操作

### 3.3 AI 页面分析

- **视觉模型**：调用 AI 模型（如 GPT-4V、Qwen-VL）分析页面截图
- **元素识别**：提取页面上的 UI 元素（按钮、输入框、文本等）
- **知识库存储**：分析结果存入数据库，支持语义搜索
- **元素切图**：自动裁剪元素图片，存储到 MinIO

### 3.4 测试用例管理

- **YAML 格式**：用例以 YAML 格式存储，支持 Midscene.js 执行
- **步骤编辑**：可视化步骤编辑器，支持拖拽排序
- **智能输入**：动作类型联想，参数自动补全
- **关联应用/项目**：用例与应用、项目关联

### 3.5 知识图谱探索

- **页面跳转记录**：记录从 A 页面点击某元素跳转到 B 页面
- **导航图构建**：构建 App 的页面导航图
- **路径查找**：查找从 A 页面到 B 页面的操作路径

---

## 四、技术栈

### 后端
- **框架**：FastAPI (Python 3.10+)
- **ORM**：SQLAlchemy 2.0 (异步)
- **数据库**：MySQL / SQLite
- **认证**：JWT (PyJWT)
- **设备管理**：tidevice (iOS)、Sonic Agent (Android)
- **对象存储**：MinIO
- **AI**：OpenAI 兼容 API

### 前端
- **框架**：Vue 3 (Composition API)
- **UI 库**：Element Plus
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **HTTP**：Axios
- **构建**：Vite
- **样式**：SCSS

---

## 五、快速启动

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python main.py
# 访问 http://localhost:8000/docs 查看 API 文档
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 环境变量配置

在项目根目录创建 `.Env` 文件：

```env
# 数据库
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/xrun

# Sonic 配置
SONIC_SERVER_URL=http://your-sonic-server:3000
SONIC_SECRET_KEY=your-secret-key

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key

# AI 模型配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

---

## 六、目录说明总结

| 目录 | 说明 |
|-----|------|
| `backend/` | 后端 FastAPI 服务 |
| `backend/apps/ui_automation/` | UI 自动化核心模块 |
| `backend/apps/ui_automation/api/` | API 路由层 |
| `backend/apps/ui_automation/models/` | 数据模型 (ORM) |
| `backend/apps/ui_automation/schemas/` | 数据校验 (Pydantic) |
| `backend/apps/ui_automation/services/` | 业务服务层 |
| `backend/apps/ui_automation/knowledge/` | AI 知识库模块 |
| `backend/llm/` | 大模型客户端 |
| `frontend/` | 前端 Vue 应用 |
| `frontend/src/api/` | API 接口封装 |
| `frontend/src/components/` | 公共组件 |
| `frontend/src/router/` | 路由配置 |
| `frontend/src/stores/` | 状态管理 |
| `frontend/src/views/` | 页面视图 |
| `docs/` | 项目文档 |
| `scripts/` | 部署/启动脚本 |

---

*文档生成时间：2026-01-30*
