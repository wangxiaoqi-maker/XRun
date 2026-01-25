# Sonic 服务器部署指南

> 本文档详细说明如何将 Sonic 及 UI 自动化平台部署到云服务器，以及本地执行机的配置方法。

## 目录

1. [部署架构](#部署架构)
2. [服务器端部署](#服务器端部署)
3. [执行机部署](#执行机部署)
4. [网络配置](#网络配置)
5. [平台代码改动](#平台代码改动)
6. [iOS 特殊处理](#ios-特殊处理)
7. [运维监控](#运维监控)

---

## 部署架构

### 整体架构

```
                          ┌─────────────────────────────────────────────┐
                          │            云服务器 (公网 IP)                 │
                          │                                             │
                          │  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
                          │  │  Nginx  │  │ FastAPI │  │Sonic Server │ │
                          │  │  :80    │  │  :8000  │  │   :3000     │ │
                          │  └────┬────┘  └─────────┘  └──────┬──────┘ │
                          │       │                           │        │
                          └───────┼───────────────────────────┼────────┘
                                  │                           │
                    ┌─────────────┼───────────────────────────┼─────────────┐
                    │             │       公网 / VPN          │             │
                    │             │                           │             │
          ┌─────────▼─────────┐   │             ┌─────────────▼─────────────┐
          │    执行机 A        │   │             │       执行机 B            │
          │  (Mac - iOS)      │   │             │    (Windows/Linux)       │
          │                   │   │             │                          │
          │  ┌─────────────┐  │   │             │  ┌─────────────┐         │
          │  │Sonic Agent  │  │   │             │  │Sonic Agent  │         │
          │  │   :7777     │◄─┼───┘             │  │   :7777     │         │
          │  └──────┬──────┘  │                 │  └──────┬──────┘         │
          │         │         │                 │         │                │
          │    ┌────┴────┐    │                 │    ┌────┴────┐           │
          │    │ iPhone  │    │                 │    │ Android │           │
          │    │ iPad    │    │                 │    │ Devices │           │
          │    └─────────┘    │                 │    └─────────┘           │
          └───────────────────┘                 └──────────────────────────┘
```

### 组件说明

| 组件 | 部署位置 | 端口 | 说明 |
|-----|---------|------|------|
| Nginx | 云服务器 | 80/443 | 反向代理，SSL 终止 |
| FastAPI | 云服务器 | 8000 | 平台后端 API |
| Sonic Server | 云服务器 | 3000 | 设备管理中心 |
| Sonic Agent | 执行机 | 7777 | 连接真实设备 |
| WDA | Mac 执行机 | 8100/9100 | iOS 控制（仅 iOS） |

---

## 服务器端部署

### 1. 服务器要求

```
- 操作系统: Ubuntu 20.04+ / CentOS 7+
- CPU: 2核+
- 内存: 4GB+
- 硬盘: 50GB+
- 网络: 公网 IP，开放端口 80, 443, 3000, 8000
```

### 2. 安装 Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证
docker --version
docker-compose --version
```

### 3. 创建部署目录

```bash
mkdir -p /opt/ui-automation
cd /opt/ui-automation
```

### 4. Docker Compose 配置

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  # ============ Sonic Server 组件 ============
  
  # MySQL 数据库
  sonic-mysql:
    image: mysql:8.0
    container_name: sonic-mysql
    environment:
      MYSQL_ROOT_PASSWORD: sonic_password_2024
      MYSQL_DATABASE: sonic
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    restart: always
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Eureka 服务注册中心
  sonic-server-eureka:
    image: sonicorg/sonic-server-eureka:v2.7.2
    container_name: sonic-server-eureka
    environment:
      - SONIC_EUREKA_USERNAME=sonic
      - SONIC_EUREKA_PASSWORD=sonic
      - SONIC_EUREKA_PORT=9090
    ports:
      - "9090:9090"
    restart: always

  # Gateway 网关
  sonic-server-gateway:
    image: sonicorg/sonic-server-gateway:v2.7.2
    container_name: sonic-server-gateway
    environment:
      - SONIC_EUREKA_USERNAME=sonic
      - SONIC_EUREKA_PASSWORD=sonic
      - SONIC_EUREKA_HOST=sonic-server-eureka
      - SONIC_EUREKA_PORT=9090
    ports:
      - "3000:3000"
    depends_on:
      - sonic-server-eureka
    restart: always

  # Controller 控制器
  sonic-server-controller:
    image: sonicorg/sonic-server-controller:v2.7.2
    container_name: sonic-server-controller
    environment:
      - SONIC_EUREKA_USERNAME=sonic
      - SONIC_EUREKA_PASSWORD=sonic
      - SONIC_EUREKA_HOST=sonic-server-eureka
      - SONIC_EUREKA_PORT=9090
      - MYSQL_HOST=sonic-mysql
      - MYSQL_PORT=3306
      - MYSQL_DATABASE=sonic
      - MYSQL_USERNAME=root
      - MYSQL_PASSWORD=sonic_password_2024
      - SECRET_KEY=sonic_secret_key_2024
      - EXPIRE_DAY=14
    depends_on:
      sonic-mysql:
        condition: service_healthy
      sonic-server-eureka:
        condition: service_started
    restart: always

  # Folder 文件服务
  sonic-server-folder:
    image: sonicorg/sonic-server-folder:v2.7.2
    container_name: sonic-server-folder
    environment:
      - SONIC_EUREKA_USERNAME=sonic
      - SONIC_EUREKA_PASSWORD=sonic
      - SONIC_EUREKA_HOST=sonic-server-eureka
      - SONIC_EUREKA_PORT=9090
    volumes:
      - sonic_files:/keepFiles
    depends_on:
      - sonic-server-eureka
    restart: always

  # Transport 消息服务
  sonic-server-transport:
    image: sonicorg/sonic-server-transport:v2.7.2
    container_name: sonic-server-transport
    environment:
      - SONIC_EUREKA_USERNAME=sonic
      - SONIC_EUREKA_PASSWORD=sonic
      - SONIC_EUREKA_HOST=sonic-server-eureka
      - SONIC_EUREKA_PORT=9090
    depends_on:
      - sonic-server-eureka
    restart: always

  # ============ 平台后端 ============
  
  fastapi:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ui-automation-api
    environment:
      - SONIC_SERVER_URL=http://sonic-server-gateway:3000
      - SONIC_USERNAME=sonic
      - SONIC_PASSWORD=sonic
      - DATABASE_URL=sqlite:///./data/app.db
    volumes:
      - api_data:/app/data
    ports:
      - "8000:8000"
    depends_on:
      - sonic-server-gateway
    restart: always

  # ============ 前端 ============
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: ui-automation-web
    ports:
      - "80:80"
    depends_on:
      - fastapi
    restart: always

volumes:
  mysql_data:
  sonic_files:
  api_data:
```

### 5. 创建后端 Dockerfile

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6. 创建前端 Dockerfile

创建 `frontend/Dockerfile`：

```dockerfile
# 构建阶段
FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 7. 创建前端 Nginx 配置

创建 `frontend/nginx.conf`：

```nginx
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://fastapi:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Sonic Server 代理
    location /sonic/ {
        proxy_pass http://sonic-server-gateway:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 代理 - 动态路由到 Agent
    # 格式: /agent-ws/{agent_host}/{agent_port}/...
    location ~ ^/agent-ws/([^/]+)/([^/]+)/(.*)$ {
        resolver 8.8.8.8 valid=30s;
        set $agent_host $1;
        set $agent_port $2;
        set $path $3;
        
        proxy_pass http://$agent_host:$agent_port/$path;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # iOS WDA 代理 - 动态路由
    # 格式: /wda/{agent_host}/{wda_port}/...
    location ~ ^/wda/([^/]+)/([^/]+)/(.*)$ {
        resolver 8.8.8.8 valid=30s;
        set $agent_host $1;
        set $wda_port $2;
        set $path $3;
        
        proxy_pass http://$agent_host:$wda_port/$path;
        proxy_set_header Host $host;
    }

    # iOS MJPEG 代理 - 动态路由
    location ~ ^/mjpeg/([^/]+)/([^/]+)$ {
        resolver 8.8.8.8 valid=30s;
        set $agent_host $1;
        set $mjpeg_port $2;
        
        proxy_pass http://$agent_host:$mjpeg_port/;
        proxy_set_header Host $host;
        proxy_buffering off;
    }

    # 健康检查
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

### 8. 启动服务

```bash
cd /opt/ui-automation

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查服务状态
docker-compose ps
```

### 9. 初始化配置

```bash
# 等待服务完全启动（约 2-3 分钟）
sleep 180

# 访问 Sonic 前端，创建管理员账号
# http://YOUR_SERVER_IP:3000
# 默认账号: sonic / sonic

# 在 Sonic 后台配置：
# 1. 系统管理 -> 全局参数
# 2. 添加 Agent Key（记下这个 Key，执行机需要用）
```

---

## 执行机部署

### 1. 执行机要求

| 系统 | 用途 | 要求 |
|-----|------|------|
| macOS | iOS + Android | Xcode, Java 17+, ADB |
| Windows | Android | Java 17+, ADB |
| Linux | Android | Java 17+, ADB |

### 2. 下载 Sonic Agent

```bash
# 创建目录
mkdir -p ~/sonic-agent
cd ~/sonic-agent

# 下载对应版本（以 v2.7.2 为例）
# macOS ARM64
wget https://github.com/SonicCloudOrg/sonic-agent/releases/download/v2.7.2/sonic-agent-v2.7.2-macosx-arm64.zip
unzip sonic-agent-v2.7.2-macosx-arm64.zip

# macOS x64
wget https://github.com/SonicCloudOrg/sonic-agent/releases/download/v2.7.2/sonic-agent-v2.7.2-macosx-x64.zip

# Windows
wget https://github.com/SonicCloudOrg/sonic-agent/releases/download/v2.7.2/sonic-agent-v2.7.2-windows-x64.zip

# Linux
wget https://github.com/SonicCloudOrg/sonic-agent/releases/download/v2.7.2/sonic-agent-v2.7.2-linux-x64.zip
```

### 3. 配置 Agent

编辑 `config/application-sonic-agent.yml`：

```yaml
sonic:
  agent:
    # Sonic Server 地址（云服务器地址）
    host: YOUR_SERVER_IP
    port: 3000
    # Agent Key（从 Sonic 后台获取）
    key: YOUR_AGENT_KEY
    # Agent 监听端口
    local-port: 7777
    # Agent 名称（标识不同执行机）
    name: "执行机-北京-01"
  
  # iOS 配置（仅 macOS 执行机需要）
  ios:
    wda-bundle-id: com.facebook.WebDriverAgentRunner.xctrunner
    wda-local-port: 8100
```

### 4. 启动 Agent

**macOS / Linux:**

```bash
cd ~/sonic-agent

# 设置 Java 环境（如果需要）
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home

# 启动
$JAVA_HOME/bin/java -Dfile.encoding=utf-8 -jar sonic-agent-*.jar

# 或后台运行
nohup $JAVA_HOME/bin/java -Dfile.encoding=utf-8 -jar sonic-agent-*.jar > agent.log 2>&1 &
```

**Windows:**

```batch
cd C:\sonic-agent

# 启动
java -Dfile.encoding=utf-8 -jar sonic-agent-windows-x64.jar
```

### 5. 使用 systemd 管理（Linux/macOS）

创建 `/etc/systemd/system/sonic-agent.service`：

```ini
[Unit]
Description=Sonic Agent
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/home/your_user/sonic-agent
Environment="JAVA_HOME=/usr/lib/jvm/java-17"
ExecStart=/usr/lib/jvm/java-17/bin/java -Dfile.encoding=utf-8 -jar sonic-agent-linux-x64.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sonic-agent
sudo systemctl start sonic-agent
sudo systemctl status sonic-agent
```

---

## 网络配置

### 方案 1：公网 IP（推荐）

如果执行机有公网 IP，直接在路由器/防火墙开放端口：

```
端口 7777 (TCP) - Sonic Agent
端口 8100 (TCP) - iOS WDA (如果有 iOS 设备)
端口 9100 (TCP) - iOS MJPEG (如果有 iOS 设备)
```

### 方案 2：内网穿透 (frp)

**服务端 (frps.ini)** - 部署在云服务器：

```ini
[common]
bind_port = 7000
token = your_secret_token
```

**客户端 (frpc.ini)** - 部署在执行机：

```ini
[common]
server_addr = YOUR_SERVER_IP
server_port = 7000
token = your_secret_token

[sonic-agent]
type = tcp
local_ip = 127.0.0.1
local_port = 7777
remote_port = 17777

[ios-wda]
type = tcp
local_ip = 127.0.0.1
local_port = 8100
remote_port = 18100

[ios-mjpeg]
type = tcp
local_ip = 127.0.0.1
local_port = 9100
remote_port = 19100
```

启动：

```bash
# 服务端
./frps -c frps.ini

# 客户端
./frpc -c frpc.ini
```

### 方案 3：VPN

使用 WireGuard / OpenVPN 建立私有网络，所有服务通过 VPN 内网 IP 通信。

---

## 平台代码改动

### 1. 后端改动

#### 更新 Sonic 服务配置

```python
# backend/app/services/sonic_service.py

import os

class SonicService:
    def __init__(self):
        # 从环境变量读取配置
        self.server_url = os.getenv('SONIC_SERVER_URL', 'http://localhost:3000')
        self.username = os.getenv('SONIC_USERNAME', 'sonic')
        self.password = os.getenv('SONIC_PASSWORD', 'sonic')
```

#### 添加设备代理信息

```python
# backend/app/api/devices.py

@router.get("/")
async def list_devices():
    devices = await sonic_service.get_devices()
    
    # 为每个设备添加代理 URL
    for device in devices:
        agent_host = device.get('agent_host')
        agent_port = device.get('agent_port', 7777)
        udid = device.get('udid')
        
        # Android WebSocket URL（通过 Nginx 代理）
        if device.get('platform') == 'android':
            device['screen_ws_url'] = f"/agent-ws/{agent_host}/{agent_port}/websockets/android/screen/..."
            device['control_ws_url'] = f"/agent-ws/{agent_host}/{agent_port}/websockets/android/..."
        
        # iOS WDA URL（通过 Nginx 代理）
        elif device.get('platform') == 'ios':
            wda_port = device.get('wda_port', 8100)
            mjpeg_port = device.get('mjpeg_port', 9100)
            device['wda_url'] = f"/wda/{agent_host}/{wda_port}"
            device['mjpeg_url'] = f"/mjpeg/{agent_host}/{mjpeg_port}"
    
    return devices
```

### 2. 前端改动

#### 更新 DeviceMirror.vue

```javascript
// frontend/src/components/DeviceMirror.vue

// 不再硬编码 localhost，从设备信息获取
async function startMirror() {
  const device = selectedDevice.value
  
  if (device.platform === 'android') {
    // 使用设备返回的 WebSocket URL
    const screenUrl = device.screen_ws_url
    const controlUrl = device.control_ws_url
    
    screenWs = new WebSocket(`ws://${window.location.host}${screenUrl}`)
    controlWs = new WebSocket(`ws://${window.location.host}${controlUrl}`)
  } 
  else if (device.platform === 'ios') {
    // 使用设备返回的 WDA/MJPEG URL
    WDA_URL = device.wda_url
    MJPEG_URL = device.mjpeg_url
    
    // MJPEG 流
    currentFrame.value = MJPEG_URL
  }
}
```

#### 更新 Vite 配置（开发环境）

```javascript
// frontend/vite.config.js

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/sonic': {
        target: process.env.VITE_SONIC_URL || 'http://localhost:3000',
        changeOrigin: true
      },
      // 开发时代理到本地 Agent
      '/agent-ws': {
        target: 'ws://localhost:7777',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/agent-ws\/[^/]+\/[^/]+/, '')
      },
      '/wda': {
        target: 'http://localhost:8100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/wda\/[^/]+\/[^/]+/, '')
      },
      '/mjpeg': {
        target: 'http://localhost:9100',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/mjpeg\/[^/]+\/[^/]+/, '')
      }
    }
  }
})
```

#### 添加环境变量

创建 `frontend/.env.production`：

```bash
# 生产环境 API 地址（使用相对路径，由 Nginx 代理）
VITE_API_URL=/api
VITE_SONIC_URL=/sonic
```

### 3. 完整的设备连接流程（生产环境）

```
1. 用户打开平台 (https://your-domain.com)
2. 前端请求 /api/devices 获取设备列表
3. 后端从 Sonic Server 获取设备信息，附加代理 URL
4. 用户选择设备
5. 前端根据设备类型：
   - Android: 连接 /agent-ws/{host}/{port}/websockets/...
   - iOS: 加载 /mjpeg/{host}/{port} 并调用 /wda/{host}/{port}/...
6. Nginx 根据 URL 动态代理到对应的 Agent
```

---

## iOS 特殊处理

### 1. WDA 持久化运行

在 Mac 执行机上创建 LaunchAgent：

```xml
<!-- ~/Library/LaunchAgents/com.wda.runner.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wda.runner</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/WebDriverAgent && xcodebuild -project WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner -destination 'id=YOUR_DEVICE_UDID' test</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/wda.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/wda.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.wda.runner.plist
```

### 2. 多 iOS 设备端口管理

创建端口管理脚本 `manage_ios_ports.sh`：

```bash
#!/bin/bash

# iOS 设备端口管理脚本
# 自动为每台 iOS 设备分配端口

BASE_WDA_PORT=8100
BASE_MJPEG_PORT=9100

# 获取所有 iOS 设备
DEVICES=$(idevice_id -l)

PORT_OFFSET=0
for UDID in $DEVICES; do
    WDA_PORT=$((BASE_WDA_PORT + PORT_OFFSET))
    MJPEG_PORT=$((BASE_MJPEG_PORT + PORT_OFFSET))
    
    echo "设备: $UDID"
    echo "  WDA 端口: $WDA_PORT"
    echo "  MJPEG 端口: $MJPEG_PORT"
    
    # 启动端口转发
    pkill -f "iproxy $WDA_PORT" 2>/dev/null
    pkill -f "iproxy $MJPEG_PORT" 2>/dev/null
    
    iproxy $WDA_PORT:8100 -u $UDID &
    iproxy $MJPEG_PORT:9100 -u $UDID &
    
    # 保存端口映射到文件（供后端读取）
    echo "$UDID,$WDA_PORT,$MJPEG_PORT" >> /tmp/ios_ports.csv
    
    PORT_OFFSET=$((PORT_OFFSET + 1))
done
```

### 3. 后端读取 iOS 端口映射

```python
# backend/app/services/ios_port_service.py

import csv

class IOSPortService:
    def __init__(self):
        self.port_file = '/tmp/ios_ports.csv'
    
    def get_device_ports(self, udid: str) -> dict:
        try:
            with open(self.port_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] == udid:
                        return {
                            'wda_port': int(row[1]),
                            'mjpeg_port': int(row[2])
                        }
        except FileNotFoundError:
            pass
        
        # 默认端口
        return {'wda_port': 8100, 'mjpeg_port': 9100}
```

---

## 运维监控

### 1. 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

# 检查 Sonic Server
if curl -s http://localhost:3000/server/api/controller/users/login -X POST \
   -H "Content-Type: application/json" \
   -d '{"userName":"sonic","password":"sonic"}' | grep -q "2000"; then
    echo "✓ Sonic Server 正常"
else
    echo "✗ Sonic Server 异常"
    # 发送告警
fi

# 检查 FastAPI
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo "✓ FastAPI 正常"
else
    echo "✗ FastAPI 异常"
fi

# 检查 Agent 数量
AGENT_COUNT=$(curl -s "http://localhost:3000/server/api/controller/agents" \
    -H "SonicToken: YOUR_TOKEN" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))")
echo "在线 Agent 数量: $AGENT_COUNT"
```

### 2. 日志收集

```yaml
# docker-compose.yml 添加日志配置
services:
  fastapi:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

### 3. Prometheus 监控（可选）

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ui-automation'
    static_configs:
      - targets: ['localhost:8000']
```

---

## 部署检查清单

### 服务器端

- [ ] Docker 和 Docker Compose 已安装
- [ ] docker-compose.yml 配置正确
- [ ] 防火墙开放端口 80, 443, 3000
- [ ] 服务全部启动成功 (`docker-compose ps`)
- [ ] Sonic 后台可访问，Agent Key 已生成

### 执行机

- [ ] Java 17+ 已安装
- [ ] ADB 已配置（Android）
- [ ] Xcode 和 WDA 已配置（iOS）
- [ ] Sonic Agent 配置正确
- [ ] Agent 已连接到 Server（在 Sonic 后台可见）
- [ ] 设备已连接并在线

### 网络

- [ ] Agent 端口可从服务器访问
- [ ] WebSocket 代理配置正确
- [ ] iOS WDA/MJPEG 端口可访问（如有 iOS 设备）

### 平台

- [ ] 前端可访问
- [ ] 设备列表正常显示
- [ ] 投屏功能正常
- [ ] 触控功能正常

---

*文档版本: 1.0.0*
*最后更新: 2026-01-13*

