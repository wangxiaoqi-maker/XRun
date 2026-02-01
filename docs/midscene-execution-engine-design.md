# Midscene 用例执行引擎架构设计

> 版本：v1.0  
> 更新时间：2025-01-30  
> 作者：XRun Team

---

## 一、概述

### 1.1 背景

基于 [Midscene.js](https://midscenejs.com/) 构建企业级 UI 自动化测试平台，实现：
- 统一的用例管理与编排
- 元素知识库复用
- 灵活的变量与流程控制
- 可视化执行与报告

### 1.2 核心目标

| 目标 | 描述 |
|------|------|
| **用例复用** | 用例之间支持引用关系，避免重复编写 |
| **元素复用** | 引用元素知识库，统一管理定位策略 |
| **变量传递** | 支持全局/用例/步骤级变量，参数化执行 |
| **流程控制** | 支持条件分支、循环、异常处理 |
| **报告集成** | 使用 Midscene 原生 HTML 报告，平台记录执行历史 |

### 1.3 技术选型

- **用例格式**：YAML（可读性强，支持注释）
- **执行引擎**：Midscene.js（iOS/Android/Web）
- **代码生成**：YAML → TypeScript
- **报告**：Midscene 原生 HTML 报告
- **存储**：MySQL + MinIO + Redis

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用例管理层 (Case Management)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Test Suite  │  │ Test Case   │  │ Test Step   │  │  Variable  │ │
│  │  测试套件    │  │  测试用例    │  │  测试步骤    │  │   变量池   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         用例解析层 (Case Parser)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ YAML Parser │  │ Ref Resolver│  │ Var Resolver│  │ Element    │ │
│  │ YAML 解析器  │  │  引用解析器  │  │  变量解析器  │  │ Resolver   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        代码生成层 (Code Generator)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ TS Template │  │ Action Map  │  │ Flow Control│  │ Assert Gen │ │
│  │  TS 模板    │  │  动作映射    │  │  流程控制    │  │  断言生成  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        执行引擎层 (Execution Engine)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Midscene    │  │ Device Mgr  │  │ Runner      │  │ Result     │ │
│  │  Adapter    │  │  设备管理    │  │  执行器      │  │ Collector  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         基础设施层 (Infrastructure)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │ Element KB  │  │ MinIO       │  │ MySQL       │  │ Redis      │ │
│  │  元素知识库  │  │  文件存储    │  │  数据存储    │  │  任务队列  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、用例数据模型

### 3.1 层次结构

```
TestSuite (测试套件)
    │
    ├── TestCase (测试用例) ──引用──► TestCase (可复用用例)
    │       │
    │       ├── Step (测试步骤)
    │       │     │
    │       │     ├── Action (原子动作)
    │       │     ├── Element Reference (元素引用)
    │       │     ├── Assertion (断言)
    │       │     └── Flow Control (流程控制)
    │       │
    │       └── Step ...
    │
    └── TestCase ...
```

### 3.2 TestSuite（测试套件）

```yaml
TestSuite:
  id: string              # 唯一标识
  name: string            # 套件名称
  description: string     # 描述
  app_id: string          # 关联应用
  project_id: string      # 关联项目
  
  # 用例列表（按执行顺序）
  cases: 
    - case_id: string
      enabled: boolean    # 是否启用
  
  # 套件级变量
  variables:
    env: "test"
    base_url: "https://api.example.com"
  
  # 前置/后置
  setup:
    - action: launch
      params:
        target: com.example.app
  teardown:
    - action: screenshot
      params:
        name: final_state
```

### 3.3 TestCase（测试用例）

```yaml
TestCase:
  id: string              # 唯一标识
  name: string            # 用例名称
  description: string     # 描述
  tags: string[]          # 标签
  priority: P0|P1|P2|P3   # 优先级
  
  # ===== 输入变量定义 =====
  input_variables:
    - name: phone
      type: string
      required: true
      description: 登录手机号
    - name: password
      type: string
      default: "123456"
      description: 登录密码
  
  # ===== 引用其他用例 =====
  refs:
    - case_id: case_login_001
      alias: login          # 引用别名
      params:               # 参数传递
        phone: ${phone}
      condition: ${!is_logged_in}  # 条件执行
  
  # ===== 用例步骤 =====
  steps:
    - id: step_1
      name: 步骤名称
      # ... 步骤定义
  
  # ===== 输出变量 =====
  output_variables:
    - login_status
    - user_info
```

### 3.4 Step（测试步骤）

```yaml
Step:
  id: string              # 步骤ID
  name: string            # 步骤名称
  description: string     # 描述
  
  # ===== 动作定义 =====
  action:
    type: ActionType      # 动作类型
    params: object        # 动作参数
  
  # ===== 元素引用 =====
  element_ref: ${element.btn_login}  # 引用元素库
  
  # ===== 断言 =====
  expect:
    type: AssertType
    params: object
  
  # ===== 执行控制 =====
  timeout: 10000          # 超时时间(ms)
  retry: 3                # 重试次数
  retry_interval: 1000    # 重试间隔(ms)
  on_fail: stop|continue|skip_rest  # 失败策略
  
  # ===== 条件执行 =====
  condition: ${var > 0}   # 满足条件才执行
  
  # ===== 变量输出 =====
  output_var: result      # 将结果存入变量
```

---

## 四、动作类型（Action Types）

### 4.1 基础交互动作

| 动作类型 | 描述 | 参数 |
|----------|------|------|
| `tap` | 点击元素 | `element_ref` |
| `double_tap` | 双击元素 | `element_ref` |
| `long_press` | 长按元素 | `element_ref`, `duration` |
| `input` | 输入文本 | `text`, `mode: replace\|append\|clear` |
| `clear_input` | 清空输入框 | `element_ref` |
| `scroll` | 滚动 | `direction: up\|down\|left\|right`, `distance` |
| `drag_drop` | 拖拽 | `from_element`, `to_element` |
| `keyboard_press` | 按键 | `key: enter\|back\|home` |

### 4.2 系统操作动作

| 动作类型 | 描述 | 参数 |
|----------|------|------|
| `launch` | 启动应用/URL | `target: bundleId\|url\|scheme` |
| `home` | 返回主屏 | - |
| `back` | 返回上一页 | - |
| `app_switcher` | 多任务切换 | - |
| `screenshot` | 截图 | `name` |

### 4.3 AI 驱动动作

| 动作类型 | 描述 | 参数 |
|----------|------|------|
| `ai_act` | AI 自然语言操作 | `prompt` |
| `ai_query` | AI 查询页面信息 | `prompt`, `output_var` |
| `ai_assert` | AI 断言 | `prompt` |

### 4.4 流程控制动作

| 动作类型 | 描述 | 参数 |
|----------|------|------|
| `wait` | 等待条件满足 | `condition`, `timeout` |
| `sleep` | 固定等待 | `duration` |
| `ref_case` | 引用执行其他用例 | `case_id`, `params` |
| `set_var` | 设置变量 | `name`, `value` |

---

## 五、流程控制

### 5.1 条件分支（if-else）

```yaml
steps:
  - id: step_check_login
    name: 检查登录状态
    action:
      type: ai_query
      params:
        prompt: 当前是否已登录？返回 {isLoggedIn: boolean}
    output_var: login_status

  - id: step_login
    name: 执行登录
    condition: ${!login_status.isLoggedIn}  # 条件：未登录时执行
    action:
      type: ref_case
      params:
        case_id: case_login_001
        params:
          phone: ${phone}

  - id: step_skip_login
    name: 跳过登录
    condition: ${login_status.isLoggedIn}   # 条件：已登录时执行
    action:
      type: log
      params:
        message: 用户已登录，跳过登录步骤
```

### 5.2 条件分支（switch-case）

```yaml
steps:
  - id: step_get_user_type
    name: 获取用户类型
    action:
      type: ai_query
      params:
        prompt: 返回当前用户类型 {userType: 'vip'|'normal'|'guest'}
    output_var: user_info

  - id: step_vip_flow
    name: VIP用户流程
    condition: ${user_info.userType == 'vip'}
    steps:  # 嵌套步骤
      - id: sub_1
        action:
          type: ai_act
          params:
            prompt: 点击VIP专属入口
      - id: sub_2
        action:
          type: ai_assert
          params:
            prompt: 显示VIP特权页面

  - id: step_normal_flow
    name: 普通用户流程
    condition: ${user_info.userType == 'normal'}
    steps:
      - id: sub_1
        action:
          type: ai_act
          params:
            prompt: 点击普通用户入口

  - id: step_guest_flow
    name: 游客流程
    condition: ${user_info.userType == 'guest'}
    action:
      type: ai_act
      params:
        prompt: 引导用户注册
```

### 5.3 循环（loop）

```yaml
steps:
  - id: step_loop_items
    name: 遍历商品列表
    loop:
      type: forEach
      items: ${product_list}      # 遍历的数组
      item_var: product           # 当前项变量名
      index_var: idx              # 索引变量名
      max_iterations: 10          # 最大迭代次数（防止死循环）
    steps:
      - id: loop_step_1
        action:
          type: ai_act
          params:
            prompt: 点击第 ${idx + 1} 个商品「${product.name}」
      - id: loop_step_2
        action:
          type: ai_assert
          params:
            prompt: 进入商品详情页，显示价格 ${product.price}
      - id: loop_step_3
        action:
          type: back
```

### 5.4 循环（while）

```yaml
steps:
  - id: step_scroll_until_found
    name: 滚动直到找到目标
    loop:
      type: while
      condition: ${!found_target}
      max_iterations: 20
    steps:
      - id: scroll_step
        action:
          type: scroll
          params:
            direction: down
            distance: 300
      - id: check_step
        action:
          type: ai_query
          params:
            prompt: 页面是否包含「立即购买」按钮？返回 {found: boolean}
        output_var: check_result
      - id: update_flag
        action:
          type: set_var
          params:
            name: found_target
            value: ${check_result.found}
```

### 5.5 异常处理（try-catch）

```yaml
steps:
  - id: step_with_error_handling
    name: 带异常处理的步骤
    try:
      - id: try_step_1
        action:
          type: tap
        element_ref: ${element.btn_submit}
        timeout: 5000
      - id: try_step_2
        action:
          type: ai_assert
          params:
            prompt: 显示提交成功提示
    catch:
      - id: catch_step_1
        action:
          type: screenshot
          params:
            name: error_screenshot
      - id: catch_step_2
        action:
          type: log
          params:
            level: error
            message: 提交失败，${error.message}
    finally:
      - id: finally_step
        action:
          type: ai_act
          params:
            prompt: 关闭所有弹窗
```

### 5.6 失败策略

```yaml
steps:
  - id: step_critical
    name: 关键步骤
    on_fail: stop          # 失败后停止整个用例
    action:
      type: tap
    element_ref: ${element.btn_login}

  - id: step_optional
    name: 可选步骤
    on_fail: continue      # 失败后继续执行
    action:
      type: ai_act
      params:
        prompt: 关闭广告弹窗（如果有的话）

  - id: step_with_retry
    name: 带重试的步骤
    retry: 3               # 重试3次
    retry_interval: 2000   # 每次间隔2秒
    on_fail: skip_rest     # 重试失败后跳过剩余步骤
    action:
      type: ai_act
      params:
        prompt: 等待页面加载完成
```

---

## 六、变量系统

### 6.1 变量作用域

```
┌─────────────────────────────────────────────┐
│ Global Variables (全局变量)                  │
│   ${global.env}, ${global.base_url}         │
├─────────────────────────────────────────────┤
│ Suite Variables (套件变量)                   │
│   ${suite.timeout}, ${suite.device}         │
├─────────────────────────────────────────────┤
│ Case Variables (用例变量)                    │
│   ${case.phone}, ${case.password}           │
├─────────────────────────────────────────────┤
│ Step Variables (步骤变量)                    │
│   ${step.result}, ${step.element}           │
└─────────────────────────────────────────────┘
```

### 6.2 变量引用语法

```yaml
# 基础变量
${var_name}                      # 当前作用域
${global.var_name}               # 全局变量
${env.VAR_NAME}                  # 环境变量
${case.var_name}                 # 用例变量
${step.var_name}                 # 步骤输出

# 元素库引用
${element.element_id}            # 元素对象
${element.element_id.locator}    # 元素 Midscene 定位器
${element.element_id.name}       # 元素名称
${element.element_id.bbox}       # 元素坐标

# 内置函数
${random.uuid}                   # 随机 UUID
${random.number(1, 100)}         # 随机数
${random.string(8)}              # 随机字符串
${datetime.now}                  # 当前时间戳
${datetime.format('YYYY-MM-DD')} # 格式化时间
${datetime.add(1, 'day')}        # 时间计算

# 表达式
${price * quantity}              # 数学运算
${name.toUpperCase()}            # 字符串方法
${list.length}                   # 数组长度
${obj.key}                       # 对象属性
${condition ? 'yes' : 'no'}      # 三元表达式
```

### 6.3 变量传递示例

```yaml
# case_main.yaml
id: case_main
name: 主流程

input_variables:
  - name: user_phone
    type: string
    required: true

steps:
  # 调用登录用例，传递变量
  - id: step_login
    action:
      type: ref_case
      params:
        case_id: case_login
        params:
          phone: ${user_phone}      # 传入参数
          password: ${global.default_pwd}
    output_var: login_result        # 接收返回值

  # 使用登录用例的返回值
  - id: step_check
    condition: ${login_result.success}
    action:
      type: log
      params:
        message: 登录成功，用户ID: ${login_result.user_id}
```

---

## 七、元素库集成

### 7.1 元素引用方式

```yaml
steps:
  # 方式1：直接引用元素ID
  - id: step_1
    action:
      type: tap
    element_ref: ${element.btn_login}

  # 方式2：使用元素的 Midscene 定位器
  - id: step_2
    action:
      type: ai_act
      params:
        prompt: 点击 ${element.btn_login.locator}

  # 方式3：动态查找元素
  - id: step_3
    action:
      type: tap
    element_query:
      page_name: 首页
      element_name: 登录按钮

  # 方式4：AI 自动定位（不依赖元素库）
  - id: step_4
    action:
      type: ai_act
      params:
        prompt: 点击页面上的「登录」按钮
```

### 7.2 元素解析流程

```
用例 YAML
    │
    ▼
┌─────────────────┐
│ Element Resolver │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 1. 解析 ${element.xxx} 引用                  │
│ 2. 查询元素知识库 (kb_page_element)          │
│ 3. 获取 midscene_locator / bbox / crop_url  │
│ 4. 生成 Midscene 可识别的定位描述            │
└─────────────────────────────────────────────┘
         │
         ▼
生成 TypeScript 代码
```

---

## 八、断言系统

### 8.1 断言类型

```yaml
# 页面断言
expect:
  type: page_appear
  params:
    page: 登录页
    timeout: 5000

# 元素断言
expect:
  type: element_visible
  params:
    element_ref: ${element.btn_submit}

expect:
  type: element_text
  params:
    element_ref: ${element.label_balance}
    text: "100.00"
    match: contains  # exact | contains | regex

# Toast/提示断言
expect:
  type: toast
  params:
    text: 操作成功
    timeout: 3000

# AI 断言（推荐）
expect:
  type: ai_assert
  params:
    prompt: |
      验证以下条件：
      1. 页面显示「支付成功」
      2. 金额显示为 ${amount} 元
      3. 没有错误提示

# 数据断言
expect:
  type: data_assert
  params:
    expression: ${result.code == 0}
    message: 接口返回码应为0
```

---

## 九、执行与报告

### 9.1 执行流程

```
┌─────────────┐
│ 用例 YAML   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ 1. YAML 解析                     │
│    - 语法校验                    │
│    - 引用展开（递归）            │
│    - 变量解析                    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 2. TypeScript 代码生成           │
│    - 动作映射                    │
│    - 流程控制代码                │
│    - 断言代码                    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 3. Midscene 执行                 │
│    - 设备连接                    │
│    - 逐步执行                    │
│    - 截图收集                    │
│    - 生成 Midscene HTML 报告     │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ 4. 结果收集                      │
│    - 执行状态                    │
│    - 步骤结果                    │
│    - 报告路径                    │
│    - 存储到数据库                │
└─────────────────────────────────┘
```

### 9.2 报告策略

| 报告类型 | 来源 | 用途 |
|----------|------|------|
| **Midscene HTML 报告** | Midscene 自动生成 | 详细的执行过程、截图、AI 分析 |
| **执行记录** | XRun 平台存储 | 历史记录、统计分析、趋势图 |

```yaml
# Midscene 报告配置
midscene_options:
  generateReport: true
  reportFileName: "case_${case_id}_${timestamp}"
  reportDir: "/reports/midscene/"

# 平台执行记录
execution_record:
  - 执行ID、用例ID、套件ID
  - 执行状态（passed/failed/error）
  - 开始/结束时间、耗时
  - 步骤结果摘要
  - Midscene 报告路径（MinIO URL）
  - 错误信息、截图
  - 设备信息、变量快照
```

### 9.3 执行记录展示

```
┌────────────────────────────────────────────────────────────────┐
│ 执行记录列表                                      [筛选] [导出] │
├────────────────────────────────────────────────────────────────┤
│ #ID    用例名称      状态    耗时    执行时间      操作        │
├────────────────────────────────────────────────────────────────┤
│ 001    翼支付登录    ✅成功  12.5s   01-30 14:30   [报告][重跑] │
│ 002    转账流程      ❌失败   8.2s   01-30 14:32   [报告][重跑] │
│ 003    查询余额      ✅成功   5.1s   01-30 14:35   [报告][重跑] │
└────────────────────────────────────────────────────────────────┘

点击 [报告] → 打开 Midscene 生成的 HTML 报告（新窗口）
点击 [重跑] → 使用相同参数重新执行
```

---

## 十、数据库设计

### 10.1 核心表结构

```sql
-- 测试套件
CREATE TABLE test_suites (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    app_id VARCHAR(36),
    project_id VARCHAR(36) NOT NULL,
    variables JSON COMMENT '套件级变量',
    setup_yaml TEXT COMMENT '前置步骤YAML',
    teardown_yaml TEXT COMMENT '后置步骤YAML',
    status ENUM('draft', 'active', 'archived') DEFAULT 'draft',
    created_by VARCHAR(36),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_project (project_id),
    INDEX idx_app (app_id)
) COMMENT '测试套件';

-- 测试用例
CREATE TABLE test_cases (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    app_id VARCHAR(36),
    project_id VARCHAR(36) NOT NULL,
    suite_id VARCHAR(36),
    tags JSON COMMENT '标签数组',
    priority ENUM('P0', 'P1', 'P2', 'P3') DEFAULT 'P2',
    
    -- 核心：YAML 内容
    case_yaml TEXT NOT NULL COMMENT '用例YAML定义',
    
    -- 变量定义
    input_variables JSON COMMENT '输入变量定义',
    output_variables JSON COMMENT '输出变量名',
    
    -- 元数据
    is_reusable BOOLEAN DEFAULT FALSE COMMENT '是否可被引用',
    version INT DEFAULT 1,
    status ENUM('draft', 'active', 'deprecated') DEFAULT 'draft',
    
    -- 统计
    last_run_at DATETIME,
    last_run_status VARCHAR(20),
    run_count INT DEFAULT 0,
    pass_count INT DEFAULT 0,
    
    created_by VARCHAR(36),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_project (project_id),
    INDEX idx_suite (suite_id),
    INDEX idx_status (status),
    FULLTEXT INDEX idx_name (name, description)
) COMMENT '测试用例';

-- 用例引用关系
CREATE TABLE case_references (
    id VARCHAR(36) PRIMARY KEY,
    source_case_id VARCHAR(36) NOT NULL COMMENT '调用方用例',
    target_case_id VARCHAR(36) NOT NULL COMMENT '被引用用例',
    alias VARCHAR(100) COMMENT '引用别名',
    params JSON COMMENT '参数映射',
    execution_order INT DEFAULT 0 COMMENT '执行顺序',
    condition_expr VARCHAR(500) COMMENT '条件表达式',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_ref (source_case_id, target_case_id, alias),
    INDEX idx_source (source_case_id),
    INDEX idx_target (target_case_id)
) COMMENT '用例引用关系';

-- 执行记录
CREATE TABLE execution_records (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(36) NOT NULL,
    suite_id VARCHAR(36),
    run_id VARCHAR(36) COMMENT '批次ID（套件执行）',
    device_id VARCHAR(100),
    
    -- 执行状态
    status ENUM('pending', 'running', 'passed', 'failed', 'skipped', 'error') DEFAULT 'pending',
    
    -- 执行结果
    result_summary JSON COMMENT '结果摘要',
    step_results JSON COMMENT '步骤结果详情',
    error_message TEXT,
    error_step_id VARCHAR(50),
    
    -- 报告
    midscene_report_url VARCHAR(500) COMMENT 'Midscene HTML报告URL',
    screenshots JSON COMMENT '关键截图URL列表',
    
    -- 时间统计
    started_at DATETIME,
    finished_at DATETIME,
    duration_ms INT COMMENT '执行耗时(毫秒)',
    
    -- 环境快照
    variables_snapshot JSON COMMENT '变量快照',
    device_info JSON COMMENT '设备信息',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_case (case_id),
    INDEX idx_suite (suite_id),
    INDEX idx_run (run_id),
    INDEX idx_status (status),
    INDEX idx_time (started_at DESC)
) COMMENT '执行记录';

-- 全局变量
CREATE TABLE global_variables (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    var_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    is_secret BOOLEAN DEFAULT FALSE COMMENT '是否敏感数据',
    description VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_var (project_id, name),
    INDEX idx_project (project_id)
) COMMENT '全局变量';
```

---

## 十一、模块结构

```
backend/apps/ui_automation/
├── execution/                    # 执行引擎模块
│   ├── __init__.py
│   │
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── test_suite.py         # 测试套件
│   │   ├── test_case.py          # 测试用例
│   │   ├── case_reference.py     # 用例引用
│   │   ├── execution_record.py   # 执行记录
│   │   └── global_variable.py    # 全局变量
│   │
│   ├── schemas/                  # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── case_schema.py
│   │   ├── execution_schema.py
│   │   └── variable_schema.py
│   │
│   ├── parsers/                  # 解析器
│   │   ├── __init__.py
│   │   ├── yaml_parser.py        # YAML 语法解析
│   │   ├── ref_resolver.py       # 用例引用解析（递归展开）
│   │   ├── var_resolver.py       # 变量解析
│   │   ├── element_resolver.py   # 元素库解析
│   │   └── flow_parser.py        # 流程控制解析
│   │
│   ├── generators/               # 代码生成器
│   │   ├── __init__.py
│   │   ├── ts_generator.py       # TypeScript 代码生成
│   │   ├── action_mapping.py     # 动作类型映射
│   │   └── templates/            # Jinja2 模板
│   │       ├── case.ts.j2
│   │       ├── step.ts.j2
│   │       ├── action.ts.j2
│   │       └── flow_control.ts.j2
│   │
│   ├── runners/                  # 执行器
│   │   ├── __init__.py
│   │   ├── midscene_adapter.py   # Midscene 适配器
│   │   ├── device_manager.py     # 设备管理
│   │   ├── case_runner.py        # 用例执行器
│   │   ├── suite_runner.py       # 套件执行器
│   │   └── result_collector.py   # 结果收集
│   │
│   ├── services/                 # 业务服务
│   │   ├── __init__.py
│   │   ├── case_service.py       # 用例 CRUD
│   │   ├── suite_service.py      # 套件管理
│   │   ├── execution_service.py  # 执行调度
│   │   ├── variable_service.py   # 变量管理
│   │   └── report_service.py     # 报告管理
│   │
│   └── api/                      # API 路由
│       ├── __init__.py
│       ├── cases.py              # /api/cases
│       ├── suites.py             # /api/suites
│       ├── executions.py         # /api/executions
│       └── variables.py          # /api/variables
│
├── knowledge/                    # 已有的知识库模块
│   └── ...
│
└── midscene/                     # Midscene 封装层
    ├── __init__.py
    ├── client.py                 # Midscene 客户端
    ├── ios_adapter.py            # iOS 设备适配
    ├── android_adapter.py        # Android 设备适配
    └── web_adapter.py            # Web 适配
```

---

## 十二、完整用例示例

### 12.1 登录用例（可复用）

```yaml
# cases/common/login.yaml
id: case_common_login
name: 通用登录流程
description: 翼支付手机号验证码登录，可被其他用例引用
is_reusable: true
tags: [登录, 通用, P0]

input_variables:
  - name: phone
    type: string
    required: true
    description: 登录手机号
  - name: verify_code
    type: string
    default: "123456"
    description: 验证码（测试环境固定）

output_variables:
  - success
  - user_id
  - error_message

steps:
  - id: launch_app
    name: 启动翼支付
    action:
      type: launch
      params:
        target: com.chinatelecom.bestpayclient
    timeout: 15000
    expect:
      type: ai_assert
      params:
        prompt: 应用启动成功，显示首页或登录页

  - id: check_login_status
    name: 检查是否已登录
    action:
      type: ai_query
      params:
        prompt: |
          检查当前页面状态，返回：
          {
            isLoggedIn: boolean,
            currentPage: '首页' | '登录页' | '其他'
          }
    output_var: status

  - id: skip_if_logged
    name: 已登录则跳过
    condition: ${status.isLoggedIn}
    action:
      type: set_var
      params:
        name: success
        value: true

  - id: goto_login
    name: 进入登录页
    condition: ${!status.isLoggedIn && status.currentPage != '登录页'}
    action:
      type: ai_act
      params:
        prompt: 点击「登录」或「我的」进入登录页面

  - id: input_phone
    name: 输入手机号
    condition: ${!status.isLoggedIn}
    action:
      type: input
      params:
        text: ${phone}
        mode: replace
    element_ref: ${element.input_phone}

  - id: get_code
    name: 获取验证码
    condition: ${!status.isLoggedIn}
    action:
      type: tap
    element_ref: ${element.btn_get_code}
    expect:
      type: toast
      params:
        text: 验证码
        match: contains

  - id: input_code
    name: 输入验证码
    condition: ${!status.isLoggedIn}
    action:
      type: input
      params:
        text: ${verify_code}
    element_ref: ${element.input_verify_code}

  - id: submit_login
    name: 点击登录
    condition: ${!status.isLoggedIn}
    action:
      type: tap
    element_ref: ${element.btn_submit_login}
    timeout: 10000

  - id: verify_login
    name: 验证登录结果
    action:
      type: ai_query
      params:
        prompt: |
          验证登录是否成功，返回：
          {
            success: boolean,
            userId: string | null,
            errorMessage: string | null
          }
    output_var: login_result

  - id: set_output
    name: 设置输出变量
    action:
      type: set_var
      params:
        name: success
        value: ${login_result.success}
```

### 12.2 转账用例（引用登录）

```yaml
# cases/transfer/basic_transfer.yaml
id: case_transfer_basic
name: 基础转账流程
description: 登录后执行转账操作
tags: [转账, P0, 冒烟]
priority: P0

input_variables:
  - name: phone
    type: string
    required: true
  - name: payee_account
    type: string
    required: true
    description: 收款账号
  - name: payee_name
    type: string
    required: true
    description: 收款人姓名
  - name: amount
    type: number
    required: true
    description: 转账金额

# 引用登录用例
refs:
  - case_id: case_common_login
    alias: login
    params:
      phone: ${phone}
    condition: ${!global.is_logged_in}

steps:
  - id: enter_transfer
    name: 进入转账页面
    action:
      type: ai_act
      params:
        prompt: 在首页找到并点击「转账」功能入口
    expect:
      type: page_appear
      params:
        page: 转账页

  - id: input_account
    name: 输入收款账号
    action:
      type: input
      params:
        text: ${payee_account}
    element_ref: ${element.input_payee_account}

  - id: input_amount
    name: 输入转账金额
    action:
      type: input
      params:
        text: ${amount}
    element_ref: ${element.input_transfer_amount}

  - id: confirm_transfer
    name: 确认转账信息
    action:
      type: ai_assert
      params:
        prompt: |
          确认页面显示正确的转账信息：
          - 收款人包含「${payee_name}」
          - 金额显示「${amount}」

  - id: submit_transfer
    name: 提交转账
    action:
      type: tap
    element_ref: ${element.btn_confirm_transfer}

  - id: handle_password
    name: 输入支付密码
    try:
      - id: wait_password_dialog
        action:
          type: wait
          params:
            condition: element_visible
            element_ref: ${element.dialog_password}
            timeout: 5000
      - id: input_password
        action:
          type: input
          params:
            text: ${global.pay_password}
        element_ref: ${element.input_pay_password}
    catch:
      - id: log_no_password
        action:
          type: log
          params:
            message: 未出现密码弹窗，可能是免密支付

  - id: verify_result
    name: 验证转账结果
    action:
      type: ai_assert
      params:
        prompt: 页面显示「转账成功」或「交易完成」
    timeout: 15000
```

---

## 十三、实现路线图

| 阶段 | 里程碑 | 任务 | 优先级 |
|------|--------|------|--------|
| **Phase 1** | 基础框架 | 数据模型 + 数据库表 | P0 |
| | | YAML 解析器（基本结构） | P0 |
| | | 元素库引用解析器 | P0 |
| | | 用例 CRUD API | P0 |
| **Phase 2** | 变量与引用 | 变量系统实现 | P1 |
| | | 用例引用解析（递归） | P1 |
| | | 流程控制（条件/循环） | P1 |
| **Phase 3** | 代码生成 | TypeScript 模板 | P1 |
| | | 动作映射器 | P1 |
| | | 断言生成器 | P1 |
| **Phase 4** | 执行引擎 | Midscene 适配器 | P2 |
| | | 设备管理 | P2 |
| | | 执行调度 | P2 |
| **Phase 5** | 报告集成 | Midscene 报告存储 | P2 |
| | | 执行记录管理 | P2 |
| | | 历史统计 | P2 |
| **Phase 6** | 前端界面 | 用例编辑器 | P3 |
| | | 执行控制台 | P3 |
| | | 报告查看器 | P3 |

---

## 十四、前端交互设计

### 14.1 智能步骤输入组件

采用类似 IDE 命令面板的交互方式，单一输入框实现所有功能：

```
┌─────────────────────────────────────────────────────────────────┐
│ 输入动作（如：点击、输入、滑动、ai_tap...）                       │
│                                     [ai_tap] [ai_input] [ai_act]│
└─────────────────────────────────────────────────────────────────┘
                            ↓ 输入 "点击" 或 "ai"
┌─────────────────────────────────────────────────────────────────┐
│ 选择动作                              ↑↓ 导航 · Enter 选择      │
├─────────────────────────────────────────────────────────────────┤
│ 🤖 AI 智能操作                                                  │
│   👆 AI 点击      智能定位并点击元素              ai_tap        │
│   ⌨️ AI 输入      智能定位输入框并输入文本        ai_input      │
│   🔍 AI 查询      查询页面信息并返回结构化数据    ai_query      │
│   ✅ AI 断言      用自然语言验证页面状态          ai_assert     │
│   🤖 AI 自由操作  用自然语言描述任意操作          ai_act        │
├─────────────────────────────────────────────────────────────────┤
│ ⚙️ 系统操作                                                     │
│   🚀 启动应用    启动 App / 打开 URL             launch        │
│   🏠 返回主屏    按 Home 键返回主屏幕            home          │
└─────────────────────────────────────────────────────────────────┘
```

选中动作后，自动生成标签 + 提示词输入区：

```
┌─────────────────────────────────────────────────────────────────┐
│ [👆 AI 点击 ×] [首页顶部的登录按钮________________] [✓]          │
└─────────────────────────────────────────────────────────────────┘
```

### 14.2 Midscene 动作映射

| 动作 ID | 名称 | 分类 | Midscene 命令 |
|---------|------|------|---------------|
| `ai_tap` | AI 点击 | AI | `aiAct('点击 xxx')` |
| `ai_double_tap` | AI 双击 | AI | `aiAct('双击 xxx')` |
| `ai_long_press` | AI 长按 | AI | `aiAct('长按 xxx')` |
| `ai_input` | AI 输入 | AI | `aiAct('在 xxx 输入 yyy')` |
| `ai_scroll` | AI 滑动 | AI | `aiAct('向下滑动')` |
| `ai_drag` | AI 拖拽 | AI | `aiAct('将 xxx 拖到 yyy')` |
| `ai_act` | AI 自由操作 | AI | `aiAct('xxx')` |
| `ai_query` | AI 查询 | AI | `aiQuery('xxx')` |
| `ai_assert` | AI 断言 | AI | `aiAssert('xxx')` |
| `launch` | 启动应用 | 系统 | `launch('bundleId')` |
| `home` | 返回主屏 | 系统 | `home()` |
| `back` | 返回上一页 | 系统 | `aiAct('点击返回')` |
| `app_switcher` | 多任务 | 系统 | `appSwitcher()` |
| `screenshot` | 截图 | 系统 | `screenshot('name')` |
| `keyboard_press` | 按键 | 系统 | `keyboardPress('enter')` |
| `wait` | 等待条件 | 等待 | `aiWaitFor('xxx')` |
| `sleep` | 固定等待 | 等待 | `sleep(ms)` |
| `if` | 条件分支 | 流程 | 代码生成 |
| `loop` | 循环 | 流程 | 代码生成 |
| `ref_case` | 引用用例 | 流程 | 函数调用 |
| `set_var` | 设置变量 | 流程 | 变量赋值 |

### 14.3 组件文件

- `frontend/src/components/SmartStepInput.vue` - 智能步骤输入组件
- `frontend/src/components/demo.vue` - 演示页面

---

## 十五、参考资料

- [Midscene.js 官方文档](https://midscenejs.com/)
- [Midscene iOS API 参考](https://midscenejs.com/zh/ios-api-reference.html)
- [Midscene YAML 工作流](https://midscenejs.com/zh/automate-with-scripts-in-yaml.html)
