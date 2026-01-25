# Sonic 投屏集成完整指南

> 本文档记录了将 Sonic 投屏功能集成到 UI 自动化平台的完整方案，包括 Android 和 iOS 两个平台的实现细节、避坑指南以及生产环境部署方案。

## 目录

1. [架构概览](#架构概览)
2. [Android 投屏方案](#android-投屏方案)
3. [iOS 投屏方案](#ios-投屏方案)
4. [避坑指南](#避坑指南)
5. [多设备支持](#多设备支持)
6. [生产环境部署](#生产环境部署)
7. [性能优化](#性能优化)

---

## 架构概览

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue.js)                             │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │  DeviceMirror   │    │   TestCase      │                     │
│  │    Component    │    │    Editor       │                     │
│  └────────┬────────┘    └─────────────────┘                     │
│           │                                                      │
│           │ Vite Proxy (解决 CORS)                               │
└───────────┼─────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    后端服务层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   FastAPI    │  │ Sonic Server │  │  Sonic Agent │            │
│  │   (8000)     │  │   (3000)     │  │    (7777)    │            │
│  └──────────────┘  └──────────────┘  └──────┬───────┘            │
│                                             │                     │
└─────────────────────────────────────────────┼─────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────┐
                    │                         │                     │
            ┌───────▼───────┐         ┌───────▼───────┐            │
            │   Android     │         │     iOS       │            │
            │   minicap     │         │   WDA+MJPEG   │            │
            │  WebSocket    │         │    HTTP       │            │
            └───────────────┘         └───────────────┘            │
```

### 技术栈

| 组件 | 技术 | 说明 |
|-----|------|------|
| 前端 | Vue 3 + Vite | 设备投屏和用例编辑 |
| 后端 | FastAPI | API 服务和设备管理 |
| 投屏服务 | Sonic Server + Agent | 设备注册和管理 |
| Android 投屏 | minicap/scrcpy | WebSocket 二进制流 |
| iOS 投屏 | WDA MJPEG | HTTP 视频流 |
| Android 控制 | Sonic touch 服务 | WebSocket 命令 |
| iOS 控制 | WebDriverAgent | HTTP API |

---

## Android 投屏方案

### 实现原理

Sonic Agent 提供两种 Android 投屏方式：

1. **minicap** (推荐)
   - 原理：通过 minicap 服务获取屏幕截图，压缩后通过 WebSocket 发送
   - 优点：兼容性好，支持大多数 Android 设备
   - 帧率：约 30-60 FPS

2. **scrcpy**
   - 原理：通过 scrcpy-server 获取 H.264 视频流
   - 优点：更高的压缩率和帧率
   - 缺点：部分高版本 Android (15+) 可能有兼容问题

### WebSocket 连接

```javascript
// 投屏 WebSocket URL 格式
const screenUrl = `ws://${agentHost}:${agentPort}/websockets/android/screen/${agentKey}/${udid}/${token}`

// 控制 WebSocket URL 格式
const controlUrl = `ws://${agentHost}:${agentPort}/websockets/android/${agentKey}/${udid}/${token}`
```

### 投屏代码示例

```javascript
// 连接投屏 WebSocket
const screenWs = new WebSocket(screenUrl)

screenWs.onopen = () => {
  // 选择投屏模式
  screenWs.send(JSON.stringify({ type: 'switch', detail: 'minicap' }))
}

screenWs.onmessage = (event) => {
  if (event.data instanceof Blob) {
    // 图像数据 - 创建 Blob URL 显示
    const url = URL.createObjectURL(event.data)
    imgElement.src = url
  } else {
    // JSON 消息（旋转、错误等）
    const msg = JSON.parse(event.data)
    console.log('Sonic 消息:', msg)
  }
}
```

### 控制命令

```javascript
// 连接控制 WebSocket
const controlWs = new WebSocket(controlUrl)

// 等待 touch 服务就绪
controlWs.onmessage = (event) => {
  const msg = JSON.parse(event.data)
  if (msg.msg === 'sas' && msg.isEnable) {
    console.log('Touch 服务已就绪')
  }
}

// 触控命令格式
controlWs.send(JSON.stringify({ type: 'touch', detail: `down ${x} ${y}\n` }))
controlWs.send(JSON.stringify({ type: 'touch', detail: `move ${x} ${y}\n` }))
controlWs.send(JSON.stringify({ type: 'touch', detail: `up\n` }))

// 按键命令
controlWs.send(JSON.stringify({ type: 'keyEvent', detail: 3 }))  // HOME
controlWs.send(JSON.stringify({ type: 'keyEvent', detail: 4 }))  // BACK

// 输入文本
controlWs.send(JSON.stringify({ type: 'text', detail: 'Hello World' }))
```

### 坐标转换（关键！）

```javascript
// 获取设备真实分辨率（从 Sonic API 返回）
const deviceWidth = 1080   // 设备物理像素宽度
const deviceHeight = 1920  // 设备物理像素高度

function getDeviceCoords(clientX, clientY) {
  const rect = screenImg.getBoundingClientRect()
  
  // 从显示尺寸转换到设备物理像素
  const scaleX = deviceWidth / rect.width
  const scaleY = deviceHeight / rect.height
  
  const x = Math.round((clientX - rect.left) * scaleX)
  const y = Math.round((clientY - rect.top) * scaleY)
  
  return { x, y }
}
```

---

## iOS 投屏方案

### 实现原理

由于 iOS 17+ 废弃了 Developer Disk Image，Sonic Agent 无法自动启动 WDA。我们采用以下方案：

1. **手动启动 WDA**：通过 Xcode 运行 WebDriverAgentRunner
2. **端口转发**：使用 iproxy 将 WDA 端口转发到本机
3. **MJPEG 投屏**：WDA 内置 MJPEG 服务器，提供高帧率视频流
4. **HTTP 控制**：通过 WDA REST API 进行触控操作

### 前置条件

```bash
# 1. 安装依赖
brew install libimobiledevice ideviceinstaller

# 2. 在 Xcode 中编译并运行 WebDriverAgentRunner
#    - 打开 WebDriverAgent.xcodeproj
#    - 选择真机目标
#    - Product -> Test 启动 WDA

# 3. 启动端口转发
iproxy 8100:8100 -u <UDID> &  # WDA API
iproxy 9100:9100 -u <UDID> &  # MJPEG 流
```

### MJPEG 投屏

```javascript
// MJPEG 流可以直接作为 img src（需要处理 CORS）
// 通过 Vite 代理解决 CORS 问题
const MJPEG_URL = '/mjpeg'  // 代理到 localhost:9100

// 直接设置 img src
imgElement.src = MJPEG_URL
```

### Vite 代理配置

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/wda': {
        target: 'http://localhost:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wda/, '')
      },
      '/mjpeg': {
        target: 'http://localhost:9100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/mjpeg/, '')
      }
    }
  }
})
```

### WDA 控制 API

```javascript
const WDA_URL = '/wda'  // 通过代理

// 1. 创建 Session（必须）
const sessionRes = await fetch(`${WDA_URL}/session`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ capabilities: {} })
})
const { sessionId } = await sessionRes.json()

// 2. 获取屏幕逻辑尺寸（WDA 使用逻辑点，非像素）
const sizeRes = await fetch(`${WDA_URL}/session/${sessionId}/window/size`)
const { value: { width, height } } = await sizeRes.json()
// iPhone 15: 393x852 (逻辑点) vs 1179x2556 (像素)

// 3. 点击
await fetch(`${WDA_URL}/session/${sessionId}/wda/tap`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ x: 196, y: 426 })  // 逻辑点坐标
})

// 4. 滑动
await fetch(`${WDA_URL}/session/${sessionId}/wda/dragfromtoforduration`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    fromX: 196, fromY: 600,
    toX: 196, toY: 300,
    duration: 0.3  // 秒
  })
})

// 5. Home 键
await fetch(`${WDA_URL}/session/${sessionId}/wda/pressButton`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'home' })
})
```

### 坐标转换（关键！）

```javascript
// WDA 使用逻辑点坐标（如 393x852），而非物理像素
let wdaWidth = 393
let wdaHeight = 852

function getWDACoords(clientX, clientY) {
  const rect = screenImg.getBoundingClientRect()
  
  // 直接从显示尺寸转换到 WDA 逻辑点
  const x = Math.round((clientX - rect.left) / rect.width * wdaWidth)
  const y = Math.round((clientY - rect.top) / rect.height * wdaHeight)
  
  return { x, y }
}
```

---

## 避坑指南

### Android 常见问题

#### 1. 投屏黑屏
```
原因：minicap/scrcpy 服务未正确启动
解决：
- 确保 Sonic Agent 正在运行
- 检查设备 USB 调试已开启
- 在 Sonic 前端选择 minicap 模式（scrcpy 在 Android 15+ 可能不兼容）
```

#### 2. 触控无反应
```
原因：Touch 服务未就绪 或 MIUI 安全限制
解决：
- 等待 WebSocket 返回 { msg: 'sas', isEnable: true }
- MIUI 需要开启「USB 调试(安全设置)」
- 设置 -> 更多设置 -> 开发者选项 -> USB调试(安全设置)
```

#### 3. 坐标不准确
```
原因：使用了图片的 naturalWidth/Height 而非设备真实分辨率
解决：
- 从 Sonic API 获取设备 resolution 字段
- 使用设备真实像素分辨率进行坐标转换
```

#### 4. 滑动不流畅
```
原因：mousemove 事件节流不当 或 浏览器默认拖拽行为
解决：
- 设置 mousemove 节流为 10ms（约 100fps）
- 添加 e.preventDefault() 阻止默认行为
- CSS: user-select: none; -webkit-user-drag: none;
```

### iOS 常见问题

#### 1. WDA 无法自动启动
```
原因：iOS 17+ 废弃了 Developer Disk Image
解决：
- 手动在 Xcode 中启动 WebDriverAgentRunner
- Product -> Test 运行到真机
```

#### 2. CORS 跨域错误
```
错误：Access to fetch at 'http://localhost:9100/' has been blocked by CORS policy
解决：
- 配置 Vite 代理转发请求
- 使用 /mjpeg 代理路径而非直接访问 localhost:9100
```

#### 3. 触控不生效
```
原因：
- 未创建 WDA Session
- 坐标使用了物理像素而非逻辑点
解决：
- 确保先调用 POST /session 创建 Session
- 使用 /window/size 获取的逻辑点尺寸进行坐标转换
- iPhone 通常是 3x 缩放（1179px ÷ 3 = 393pt）
```

#### 4. 投屏卡顿
```
原因：使用截图轮询而非 MJPEG 流
解决：
- 使用 WDA MJPEG 服务（端口 9100）
- 直接将 MJPEG URL 设置为 img src
```

#### 5. 操作延迟
```
原因：等待 WDA API 响应
解决：
- 使用 fire-and-forget 模式，不等待响应
- 缩短滑动 duration（0.3 秒以内）
```

---

## 多设备支持

### 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      Sonic Server (云端)                         │
│                         端口: 3000                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
│ Sonic Agent 1 │     │ Sonic Agent 2 │     │ Sonic Agent 3 │
│  执行机 A      │     │  执行机 B      │     │  执行机 C      │
│  端口: 7777   │     │  端口: 7777   │     │  端口: 7777   │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
   ┌────┴────┐           ┌────┴────┐           ┌────┴────┐
   │ Device1 │           │ Device3 │           │ Device5 │
   │ Device2 │           │ Device4 │           │ Device6 │
   └─────────┘           └─────────┘           └─────────┘
```

### 设备路由

```javascript
// 每个设备包含 agent_host 和 agent_port 信息
const device = {
  udid: 'xxx',
  name: 'iPhone 15',
  platform: 'ios',
  agent_host: '192.168.1.100',  // Agent 所在执行机 IP
  agent_port: 7777,
  resolution: '1179x2556'
}

// 根据设备信息连接对应的 Agent
const screenUrl = `ws://${device.agent_host}:${device.agent_port}/websockets/android/screen/...`
```

### iOS 多设备处理

对于 iOS，需要为每台设备启动独立的 WDA 实例和端口转发：

```bash
# 设备 1
iproxy 8100:8100 -u <UDID1> &
iproxy 9100:9100 -u <UDID1> &

# 设备 2（使用不同端口）
iproxy 8101:8100 -u <UDID2> &
iproxy 9101:9100 -u <UDID2> &
```

前端需要根据设备动态选择端口：

```javascript
// 动态构建 iOS 代理 URL
const wdaPort = 8100 + deviceIndex  // 8100, 8101, 8102...
const mjpegPort = 9100 + deviceIndex

// 或者在后端统一管理端口映射
```

---

## 生产环境部署

### 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        云服务器集群                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Nginx     │  │  FastAPI    │  │    Sonic Server         │  │
│  │  (反向代理)  │  │  (后端API)  │  │  (Docker Compose)       │  │
│  │   :80/443   │  │   :8000     │  │   :3000                 │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
│         │                                                        │
└─────────┼────────────────────────────────────────────────────────┘
          │
          │ 公网
          │
┌─────────┼────────────────────────────────────────────────────────┐
│         │              本地执行机（测试机房）                      │
│  ┌──────▼──────┐                                                 │
│  │ Sonic Agent │ ◄── 连接真实设备                                │
│  │   :7777     │                                                 │
│  └──────┬──────┘                                                 │
│         │                                                        │
│    ┌────┴────┐                                                   │
│    │ Android │  │ iOS (需要 Mac + Xcode)                         │
│    │ Devices │  │ Devices                                        │
│    └─────────┘  └─────────                                       │
└──────────────────────────────────────────────────────────────────┘
```

### Docker Compose 配置 (云端)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # MySQL 数据库
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: sonic_password
      MYSQL_DATABASE: sonic
    volumes:
      - mysql_data:/var/lib/mysql
    restart: always

  # Sonic Server
  sonic-server-eureka:
    image: sonicorg/sonic-server-eureka:v2.7.2
    ports:
      - "9090:9090"
    restart: always

  sonic-server-gateway:
    image: sonicorg/sonic-server-gateway:v2.7.2
    environment:
      - SONIC_EUREKA_HOST=sonic-server-eureka
    ports:
      - "3000:3000"
    depends_on:
      - sonic-server-eureka
    restart: always

  sonic-server-controller:
    image: sonicorg/sonic-server-controller:v2.7.2
    environment:
      - SONIC_EUREKA_HOST=sonic-server-eureka
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_DATABASE=sonic
      - MYSQL_USERNAME=root
      - MYSQL_PASSWORD=sonic_password
    depends_on:
      - mysql
      - sonic-server-eureka
    restart: always

  # FastAPI 后端
  fastapi:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SONIC_SERVER_URL=http://sonic-server-gateway:3000
    restart: always

  # Vue 前端 (Nginx)
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    restart: always

volumes:
  mysql_data:
```

### Nginx 配置

```nginx
# /etc/nginx/conf.d/ui-automation.conf
upstream fastapi {
    server 127.0.0.1:8000;
}

upstream sonic {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/ui-automation/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Sonic Server 代理
    location /sonic/ {
        proxy_pass http://sonic/;
        proxy_set_header Host $host;
    }

    # WebSocket 代理（重要！）
    location /ws/ {
        proxy_pass http://agent_ip:7777/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### Agent 端口映射（NAT 穿透）

如果 Agent 在内网，需要配置端口映射或使用 NAT 穿透工具：

```bash
# 方案 1：路由器端口映射
# 外网:17777 -> 内网 Agent:7777

# 方案 2：使用 frp 内网穿透
# frpc.ini
[sonic-agent]
type = tcp
local_ip = 127.0.0.1
local_port = 7777
remote_port = 17777

# 方案 3：使用 ngrok
ngrok tcp 7777
```

### iOS 生产环境注意事项

1. **WDA 持久运行**
   ```bash
   # 使用 supervisord 或 launchd 保持 WDA 运行
   # /Library/LaunchDaemons/com.wda.plist
   ```

2. **端口映射管理**
   ```python
   # 后端统一管理 iOS 设备的端口映射
   class IOSDeviceManager:
       def __init__(self):
           self.port_pool = list(range(8100, 8200))
           self.device_ports = {}
       
       def allocate_ports(self, udid):
           wda_port = self.port_pool.pop(0)
           mjpeg_port = wda_port + 1000  # 9100, 9101...
           self.device_ports[udid] = (wda_port, mjpeg_port)
           
           # 启动 iproxy
           subprocess.Popen(['iproxy', f'{wda_port}:8100', '-u', udid])
           subprocess.Popen(['iproxy', f'{mjpeg_port}:9100', '-u', udid])
           
           return wda_port, mjpeg_port
   ```

3. **证书管理**
   - WDA 需要有效的开发者证书
   - 生产环境建议使用企业证书
   - 证书过期需要重新签名

---

## 性能优化

### 前端优化

1. **图像渲染优化**
   ```javascript
   // 使用 requestAnimationFrame 控制帧率
   let lastFrameTime = 0
   const targetFPS = 60
   const frameInterval = 1000 / targetFPS
   
   function renderFrame(blob) {
     const now = performance.now()
     if (now - lastFrameTime < frameInterval) return
     lastFrameTime = now
     
     // 使用 Blob URL 而非 base64
     const url = URL.createObjectURL(blob)
     imgElement.src = url
   }
   ```

2. **触控响应优化**
   ```javascript
   // Fire-and-forget 模式，不等待 API 响应
   function sendTouch(cmd) {
     fetch(url, { method: 'POST', body: cmd })
       .catch(() => {})  // 忽略错误，减少延迟
   }
   ```

3. **WebSocket 重连**
   ```javascript
   function connectWithRetry(url, maxRetries = 5) {
     let retries = 0
     
     function connect() {
       const ws = new WebSocket(url)
       
       ws.onclose = () => {
         if (retries < maxRetries) {
           retries++
           setTimeout(connect, 1000 * retries)
         }
       }
       
       return ws
     }
     
     return connect()
   }
   ```

### 后端优化

1. **设备缓存**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100, ttl=30)
   async def get_device_info(udid: str):
       # 缓存设备信息，减少 Sonic API 调用
       return await sonic_service.get_device(udid)
   ```

2. **异步处理**
   ```python
   import asyncio
   
   async def execute_on_multiple_devices(devices, action):
       tasks = [action(device) for device in devices]
       return await asyncio.gather(*tasks)
   ```

### 网络优化

1. **WebSocket 压缩**
   - Sonic Agent 已默认压缩图像数据
   - 可调整 minicap 质量参数

2. **CDN 加速**
   - 静态资源使用 CDN
   - WebSocket 连接需直连，不经过 CDN

---

## 快速启动检查清单

### 本地开发环境

- [ ] Docker 运行 Sonic Server
- [ ] 启动 Sonic Agent (Java 17+)
- [ ] 启动后端 FastAPI
- [ ] 启动前端 Vite
- [ ] Android: USB 调试已开启
- [ ] Android (MIUI): USB 调试(安全设置) 已开启
- [ ] iOS: Xcode 运行 WebDriverAgentRunner
- [ ] iOS: iproxy 端口转发 (8100, 9100)

### 生产环境

- [ ] 云服务器部署 Sonic Server + FastAPI + Nginx
- [ ] 执行机部署 Sonic Agent
- [ ] 网络：Agent 端口可从云端访问
- [ ] iOS: WDA 持久运行配置
- [ ] iOS: 端口映射管理服务
- [ ] 监控：Agent 在线状态检测
- [ ] 日志：集中日志收集

---

## 参考资源

- [Sonic 官方文档](https://soniccloudorg.github.io/)
- [WebDriverAgent GitHub](https://github.com/appium/WebDriverAgent)
- [minicap GitHub](https://github.com/openstf/minicap)
- [scrcpy GitHub](https://github.com/Genymobile/scrcpy)

---

*文档版本: 1.0.0*
*最后更新: 2026-01-12*

