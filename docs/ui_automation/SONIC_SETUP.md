# Sonic 集成部署指南

本平台集成了 [Sonic](https://github.com/SonicCloudOrg/sonic-server) 云真机平台，提供：
- 🤖 Android + iOS 双平台支持
- 📱 高性能实时投屏 (30+ FPS)
- 🎮 远程设备控制
- 📊 设备管理

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│                    UI 自动化平台                         │
│              (FastAPI + Vue + Midscene)                 │
├─────────────────────────────────────────────────────────┤
│                         ↓ API                           │
│                    Sonic Server                          │
│                   (设备管理中心)                          │
├─────────────────────────────────────────────────────────┤
│         ↓                              ↓                │
│    Sonic Agent                    Sonic Agent            │
│    (机器 A)                        (机器 B)              │
│  ┌─────────────┐               ┌─────────────┐          │
│  │ Android x2  │               │  iOS x3     │          │
│  │ iOS x1      │               │  Android x1 │          │
│  └─────────────┘               └─────────────┘          │
└─────────────────────────────────────────────────────────┘
```

## 快速部署

### 1. 启动 Sonic Server

```bash
# 使用 Docker Compose
docker-compose up -d sonic-server

# 等待启动完成（约 1-2 分钟）
docker-compose logs -f sonic-server
```

访问 Sonic 控制台：http://localhost:8094

默认账号：`admin` / `sonic123456`

### 2. 部署 Sonic Agent

> ⚠️ Agent 必须在有设备连接的机器上运行，不能在 Docker 中

#### macOS / Linux

```bash
# 1. 下载 Agent
# https://github.com/SonicCloudOrg/sonic-agent/releases

# 2. 解压
unzip sonic-agent-v2.6.5-macos.zip
cd sonic-agent

# 3. 配置 config.properties
cat > config.properties << EOF
sonic.server.url=http://localhost:8094
sonic.agent.key=<从 Sonic Server 获取>
sonic.agent.port=7912
EOF

# 4. 启动
./agent.sh
```

#### 获取 Agent Key

1. 登录 Sonic 控制台
2. 点击 设备中心 → Agent中心
3. 点击 新增 Agent
4. 复制生成的 Agent Key

### 3. iOS 设备配置

iOS 需要额外配置 WebDriverAgent：

```bash
# 1. 安装 tidevice
pip install tidevice

# 2. 编译 WebDriverAgent
# 打开 Xcode，编译 WebDriverAgent 到设备

# 3. 启动 WDA 代理
tidevice wdaproxy -B com.facebook.WebDriverAgentRunner.xctrunner

# 4. 验证
curl http://localhost:8100/status
```

### 4. Android 设备配置

```bash
# 1. 确保 adb 可用
adb devices

# 2. 开启开发者选项
# - 设置 → 关于手机 → 连续点击版本号 7 次
# - 设置 → 开发者选项 → 打开 USB 调试

# 3. MIUI 设备需要额外开启
# - 开发者选项 → USB 调试（安全设置）→ 打开
```

## 配置说明

### 环境变量

在 `backend/.env` 中配置：

```bash
# Sonic 配置
SONIC_SERVER_URL=http://localhost:8094
SONIC_SECRET_KEY=sonic123456
SONIC_ENABLED=true

# 如果不使用 Sonic，设为 false 将使用本地 adb/tidevice
SONIC_ENABLED=false
```

### 切换本地模式

如果没有部署 Sonic，可以切换到本地模式：

```bash
# backend/.env
SONIC_ENABLED=false
```

本地模式使用 adb (Android) 和 tidevice (iOS) 直接控制设备。

## 功能对比

| 功能 | Sonic 模式 | 本地模式 |
|-----|-----------|---------|
| Android 投屏 | ✅ 30+ FPS | ⚠️ 5-10 FPS |
| iOS 投屏 | ✅ 30+ FPS | ⚠️ 5-10 FPS |
| 多设备管理 | ✅ | ✅ |
| 分布式部署 | ✅ | ❌ |
| 设备占用/释放 | ✅ | ❌ |
| 设备详情 | ✅ | ⚠️ 基础信息 |

## 常见问题

### Q: Agent 无法连接 Server

```bash
# 1. 检查网络
curl http://localhost:8094/api/controller/agents/list

# 2. 检查 Agent Key 是否正确
cat config.properties

# 3. 检查防火墙
```

### Q: iOS 设备无法投屏

```bash
# 1. 确保 WDA 运行正常
curl http://localhost:8100/status

# 2. 重新启动 WDA
tidevice wdaproxy -B com.facebook.WebDriverAgentRunner.xctrunner
```

### Q: Android 设备无法控制

```bash
# 检查 USB 调试权限
adb shell input tap 100 100

# 如果报错 SecurityException，需要开启安全设置
# MIUI: 开发者选项 → USB 调试（安全设置）
```

## 推荐配置

### 开发环境

```yaml
# 单机部署
- 1 x Sonic Server (Docker)
- 1 x Sonic Agent (本机)
- 设备通过 USB 连接本机
```

### 生产环境

```yaml
# 分布式部署
- 1 x Sonic Server (云服务器)
- N x Sonic Agent (设备机)
- 设备通过 USB 连接各 Agent 机器
```

## 相关链接

- [Sonic 官方文档](https://sonic-cloud.cn/)
- [Sonic GitHub](https://github.com/SonicCloudOrg/sonic-server)
- [WebDriverAgent](https://github.com/appium/WebDriverAgent)
- [tidevice](https://github.com/alibaba/taobao-iphone-device)

