# XRun Midscene Executor

基于 Midscene.js 的 TypeScript 测试执行器。

## 目录结构

```
midscene-executor/
├── package.json        # 项目配置
├── vitest.config.ts    # Vitest 配置
├── tsconfig.json       # TypeScript 配置
├── tests/
│   ├── android/        # Android 平台测试文件
│   └── ios/            # iOS 平台测试文件
└── reports/            # 测试报告输出
```

## 使用说明

### 安装依赖

```bash
npm install
```

### 运行测试

```bash
# 运行所有测试
npm test

# 运行 Android 测试
npm run test:android

# 运行 iOS 测试
npm run test:ios

# 监听模式
npm run test:watch
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DEVICE_ID | 设备 ID | 第一个连接的设备 |
| WDA_HOST | WDA 主机（iOS） | localhost |
| WDA_PORT | WDA 端口（iOS） | 8100 |
| MIDSCENE_MODEL_NAME | AI 模型名称 | - |
| MIDSCENE_MODEL_BASE_URL | API 地址 | - |
| MIDSCENE_MODEL_API_KEY | API Key | - |
| AI_CONTEXT | AI 上下文提示 | - |
| CACHE_ID | 缓存 ID | - |
| VAR_XXX | 用例变量 | - |

## 工作流程

1. 后端编译用例 JSON → TypeScript 测试文件
2. 测试文件写入 `tests/android/` 或 `tests/ios/` 目录
3. 后端调用 `npm test` 执行测试
4. 读取 `reports/results.json` 获取结果
5. Midscene 自动生成 HTML 报告

## 注意事项

- 测试文件由后端自动生成，请勿手动修改
- 确保设备已连接且 ADB/WDA 服务正常
- 首次运行需要配置 Midscene 模型
