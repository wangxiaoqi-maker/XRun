<template>
  <div class="device-mirror" :class="{ 'is-active': connected }">
    <!-- 顶部控制栏 (连接后显示) -->
    <div v-if="connected && !hideHeader" class="mirror-header">
      <div class="header-left">
        <div class="device-text-group">
          <span class="device-name">{{ selectedDevice?.manufacturer }}</span>
          <span class="device-model">{{ selectedDevice?.model }}</span>
        </div>
        <span class="fps-badge" v-if="selectedDevice?.platform !== 'ios'">{{ fps }} FPS</span>
        <span class="fps-badge" v-else>--</span>
      </div>
      <div class="header-right">
        <el-tag size="small" type="info" effect="plain" class="mode-tag">{{ screenMode }}</el-tag>
        <el-button link type="primary" size="small" @click="toggleScreenMode">切换</el-button>
        <el-button link type="danger" size="small" @click="disconnect">断开</el-button>
      </div>
    </div>

    <!-- 手机外框 -->
    <div class="phone-frame" 
         :class="{ 'phone-frame--connected': connected }">
      <!-- 顶部听筒 -->
      <div class="phone-notch" v-if="!connected"></div>
      
      <!-- 屏幕区域 -->
      <div class="phone-screen" ref="containerRef">
        <!-- 未选择设备 -->
        <div v-if="!selectedDevice" class="screen-placeholder">
          <div class="placeholder-icon">
            <svg viewBox="0 0 24 24" width="64" height="64">
              <path fill="currentColor" d="M7 4v16h10V4H7zM6 2h12a1 1 0 011 1v18a1 1 0 01-1 1H6a1 1 0 01-1-1V3a1 1 0 011-1zm6 15a1 1 0 110 2 1 1 0 010-2z"/>
            </svg>
          </div>
          <el-button type="primary" @click="openDeviceSelector">
            选择设备
          </el-button>
        </div>
        
        <!-- 加载中 -->
        <div v-else-if="loading" class="screen-placeholder">
          <el-icon class="is-loading" :size="48"><Loading /></el-icon>
          <p>正在连接...</p>
          <el-button type="danger" size="small" @click="disconnect" style="margin-top: 10px;">取消 / 重置</el-button>
        </div>
        
        <!-- 连接错误 -->
        <div v-else-if="connectionError" class="screen-placeholder error">
          <el-icon :size="48"><WarningFilled /></el-icon>
          <p>{{ connectionError }}</p>
          <el-button type="primary" size="small" @click="startMirror">重试</el-button>
        </div>
        
        <!-- 投屏画面容器（使用flex布局让导航栏在底部） -->
        <!-- 加载中占位（iOS MJPEG 流加载时显示） -->
        <div v-if="connected && !imageLoaded" class="screen-placeholder">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>画面加载中...</p>
        </div>
        <!-- 投屏画面容器（用于定位叠加层） -->
        <div class="screen-wrapper" ref="screenWrapperRef">
          <img
            v-show="connected && currentFrame && imageLoaded"
            ref="screenImg"
            :src="currentFrame"
            class="mirror-screen"
            @mousedown="handleMouseDown"
            @load="onImageLoad"
            draggable="false"
          />
          
          <!-- 叠加层 slot（用于 ElementOverlay 等） -->
          <slot name="overlay" :device-width="deviceWidth" :device-height="deviceHeight"></slot>
        </div>

      </div>
      
      <!-- 底部 Home 条 -->
      <div class="phone-home-bar" v-if="!connected"></div>
    </div>

    <!-- 调试信息面板已移除 -->


    <!-- 底部操作栏 -->
    <div v-if="connected" class="mirror-footer">
      <div class="integrated-navbar">
        <div class="navbar-btn" @click="doAppSwitch" title="后台">
          <el-icon :size="16"><Menu /></el-icon>
        </div>
        <div class="navbar-btn" @click="doHome" title="主页">
          <el-icon :size="16"><House /></el-icon>
        </div>
        <div class="navbar-btn" @click="doBack" title="返回">
          <el-icon :size="16"><Back /></el-icon>
        </div>
      </div>
    </div>
    
    <!-- 悬浮操作栏已移除，改用底部固定操作栏 -->
    
    <!-- 底部状态栏 (已移至顶部，此处仅保留连接前的选项) -->
    <div class="bottom-bar" v-if="!connected">
      <template v-if="selectedDevice && !loading && !connectionError">
        <!-- 连接前的投屏模式选择 -->
        <!-- 连接前仅显示连接按钮，隐藏模式选择 -->
        <div class="connect-options" style="width: 100%">
          <el-button type="primary" style="width: 100%" @click="startMirror">连接设备</el-button>
        </div>
      </template>
      <!-- 加载中不显示任何操作 -->
      <template v-else-if="loading">
      </template>
    </div>
    
    <!-- 设备选择弹窗 -->
    <el-dialog 
      v-model="showDeviceSelector" 
      title="选择设备" 
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="dialog-header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="请输入查询型号或者设备别名"
          :prefix-icon="Search"
          clearable
          style="width: 300px"
        />
        <el-button @click="refreshDevices" :loading="loadingDevices" icon="Refresh">刷新</el-button>
      </div>

      <el-table
        :data="filteredDevices"
        highlight-current-row
        @current-change="handleCurrentDeviceChange"
        @row-dblclick="quickConnect"
        height="400px"
        style="width: 100%; margin-top: 16px; border-radius: 8px;"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column prop="manufacturer" label="品牌" width="80" />
        <el-table-column prop="model" label="机型名称" width="120" show-overflow-tooltip />
        <el-table-column prop="name" label="设备别名" width="120" show-overflow-tooltip />
        <el-table-column prop="udid" label="序列号" width="140" show-overflow-tooltip />
        <el-table-column prop="os_version" label="系统版本" width="90" />
        <el-table-column prop="resolution" label="分辨率" width="110" show-overflow-tooltip />
        <el-table-column prop="mem" label="内存大小" width="90" />
        <el-table-column prop="remark" label="备注" min-width="100" show-overflow-tooltip />
        <el-table-column label="设备状态" width="90" fixed="right">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'connected' && !row.is_busy" type="success" size="small">在线</el-tag>
            <el-tag v-else-if="row.is_busy" type="warning" size="small">占用中</el-tag>
            <el-tag v-else type="info" size="small">离线</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'connected' && !row.is_busy"
              link 
              type="primary" 
              @click.stop="quickConnect(row)"
            >
              连接
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showDeviceSelector = false">取消</el-button>
        <el-button @click="refreshDevices" :loading="loadingDevices">刷新</el-button>
        <el-button type="primary" @click="confirmDevice" :disabled="!pendingDevice">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Back, House, WarningFilled, Iphone, SwitchButton, Refresh, InfoFilled, Search } from '@element-plus/icons-vue'
import { deviceApi } from '../api'

const props = defineProps({
  recording: { type: Boolean, default: false },
  udid: { type: String, default: '' },
  hideHeader: { type: Boolean, default: false } // 是否隐藏内部头部
})

const emit = defineEmits(['action-recorded', 'screenshot', 'device-connected'])



// 状态
const devices = ref({ android: [], ios: [] })
const searchKeyword = ref('') // 搜索关键词
const selectedDevice = ref(null)
const pendingDevice = ref(null) // 弹窗中暂时选中的设备
const connected = ref(false)
const loading = ref(false)
const loadingDevices = ref(false)
const connectionError = ref('')
const currentFrame = ref('')
const showDeviceSelector = ref(false)
const isConnecting = ref(false)
const controlStatus = ref('disconnected')  // 控制连接状态：disconnected, connecting, ready
const imageLoaded = ref(false)  // 图片是否已加载完成（解决 iOS 白屏问题）

// 调试状态
const debugStatus = ref('INIT')
const debugWsUrl = ref('')
const debugLastMsg = ref('')

const containerRef = ref(null)
const screenImg = ref(null)

// 所有设备（合并 Android 和 iOS，保留原始 platform 字段）
const allDevices = computed(() => [
  ...devices.value.android.map(d => ({ ...d, platform: d.platform || 'android' })),
  ...devices.value.ios.map(d => ({ ...d, platform: d.platform || 'ios' }))
])

// 过滤后的设备列表
const filteredDevices = computed(() => {
  const list = allDevices.value
  if (!searchKeyword.value) return list
  
  const keyword = searchKeyword.value.toLowerCase()
  return list.filter(d => 
    (d.name && d.name.toLowerCase().includes(keyword)) ||
    (d.model && d.model.toLowerCase().includes(keyword)) ||
    (d.udid && d.udid.toLowerCase().includes(keyword)) ||
    (d.manufacturer && d.manufacturer.toLowerCase().includes(keyword))
  )
})

// 设备显示名称：优先使用 制造商 + 型号
const deviceDisplayName = computed(() => {
  const d = selectedDevice.value
  if (!d) return ''
  // 优先显示 制造商 + 型号，如 "Xiaomi 24129PN74C"
  if (d.manufacturer && d.model) {
    return `${d.manufacturer} ${d.model}`
  }
  // 回退到型号或自定义名称
  return d.model || d.name || d.udid
})

// 动态计算设备长宽比，用于消除黑边
const deviceAspectRatio = computed(() => {
  // 优先使用实时获取的分辨率 (WDA/Scrcpy 在连接后会更新)
  if (deviceWidth.value && deviceHeight.value) {
    return `${deviceWidth.value} / ${deviceHeight.value}`
  }
  
  if (selectedDevice.value?.resolution) {
    // resolution 格式如 "1080x2400"
    const parts = selectedDevice.value.resolution.split('x')
    if (parts.length === 2) {
      const w = parseInt(parts[0])
      const h = parseInt(parts[1])
      if (w && h) return `${w} / ${h}`
    }
  }
  // 默认兜底比例
  return '9 / 19.5'
})

// Sonic 配置
const SONIC_AGENT_KEY = 'f63cbbfd-da49-4c86-8ae7-b5820382c768'

let screenWs = null
let controlWs = null
let sonicToken = null
const deviceWidth = ref(1080)
const deviceHeight = ref(1920)
let touchReady = false
let retryCount = 0
// 投屏模式：scrcpy（默认推荐）或 minicap
// 注意：minicap 不支持 Android 15+，尤其是小米设备会触发 Segmentation fault
// Sonic Agent 2.7.2 内置的 scrcpy-server 已升级到 3.1 版本，支持 Android 15
const screenMode = ref('scrcpy') // 'scrcpy' | 'minicap'
const wdaPort = ref(0) // WDA 端口

// FPS 统计（仅 Android 有效，iOS MJPEG 流无法准确统计）
const fps = ref(0)
let frameCount = 0
let lastFpsTime = Date.now()

// 鼠标状态
let isMouseDown = false
let mouseStartX = 0
let mouseStartY = 0
let mouseStartTime = 0
let lastMoveTime = 0

// 心跳定时器
let heartbeatTimer = null

onMounted(async () => {
  await refreshDevices()
  
  // FPS 统计定时器（每秒更新，不输出日志）
  setInterval(() => {
    const now = Date.now()
    const elapsed = (now - lastFpsTime) / 1000
    fps.value = Math.round(frameCount / elapsed)
    frameCount = 0
    lastFpsTime = now
  }, 1000)
  
  // 如果传入了 udid，自动连接
  if (props.udid) {
    const target = allDevices.value.find(d => d.udid === props.udid)
    if (target) {
      if (target.status !== 'connected') {
        ElMessage.warning('设备离线，无法连接')
      } else if (target.is_busy) {
        ElMessage.warning('设备正在被占用')
      } else {
        quickConnect(target)
      }
    }
  }
  
})

onUnmounted(() => {
  disconnect()
  document.removeEventListener('mousemove', onDocumentMouseMove)
  document.removeEventListener('mouseup', onDocumentMouseUp)
})

async function getSonicToken() {
  try {
    const res = await fetch('/sonic/server/api/controller/users/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userName: 'sonic', password: 'sonic' })
    })
    const data = await res.json()
    if (data.code === 2000) {
      sonicToken = data.data
      return true
    }
    return false
  } catch (e) {
    return false
  }
}

// Sonic Server 配置
const SONIC_SERVER_URL = 'http://113.249.104.59:3001'

async function refreshDevices() {
  loadingDevices.value = true
  try {
    // 1. 尝试从 Sonic Server 获取 (如果有配置)
    let serverDevices = []
    try {
      serverDevices = await getDevicesFromSonicServer()
    } catch (e) {}

    let localDevices = { android: [], ios: [] }
    try {
      const res = await deviceApi.list()
      if (res.data) {
        localDevices.android = res.data.android || []
        localDevices.ios = res.data.ios || []
      }
    } catch (e) {}
    
    // 3. 特别尝试获取原生 iOS (tidevice) - 补充本地发现
    try {
        const iosNativeRes = await deviceApi.listIOSNative()
        if (iosNativeRes.data && iosNativeRes.data.devices) {
            // 合并到 localDevices.ios，去重
            const nativeIos = iosNativeRes.data.devices.map(d => ({
                id: d.udid,
                udid: d.udid,
                name: d.name,
                model: d.model,
                platform: 'ios',
                os_version: d.version,
                status: d.status === 'online' ? 'connected' : 'disconnected',
                is_busy: false
            }))
            
            // 简单去重合并
            const existingUdids = new Set(localDevices.ios.map(d => d.udid))
            nativeIos.forEach(d => {
                if (!existingUdids.has(d.udid)) {
                    localDevices.ios.push(d)
                }
            })
        }
    } catch (e) {}

    // 4. 合并结果 (优先使用 Server 的状态信息，因为它有占用状态)
    // 如果 Server 返回了数据，我们以 Server 为主，但也可以补充本地独有的设备
    if (serverDevices.length > 0) {
       devices.value = {
         android: serverDevices.filter(d => d.platform === 'android'),
         ios: serverDevices.filter(d => d.platform === 'ios')
       }
    } else {
       // 如果 Server 没数据，完全使用本地
       devices.value = localDevices
    }
  } catch (e) {
    ElMessage.error('加载设备失败')
  } finally {
    loadingDevices.value = false
  }
}

/**
 * 从 Sonic Server 获取设备列表（包含实时占用状态）
 */
async function getDevicesFromSonicServer() {
  try {
    // 获取 token
    const loginRes = await fetch(`${SONIC_SERVER_URL}/server/api/controller/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userName: 'sonic', password: 'sonic' })
    })
    const loginData = await loginRes.json()
    if (loginData.code !== 2000) return []
    
    const token = loginData.data
    sonicToken = token  // 保存 token 供后续使用
    
    // 获取设备列表
    const devicesRes = await fetch(
      `${SONIC_SERVER_URL}/server/api/controller/devices/list?page=1&pageSize=100`,
      { headers: { 'SonicToken': token } }
    )
    const devicesData = await devicesRes.json()
    if (devicesData.code !== 2000) return []
    
    const deviceList = devicesData.data?.content || []
    
    // 转换为我们的格式
    return deviceList.map(d => ({
      id: String(d.id),
      udid: d.udId,
      name: d.name || d.model,
      model: d.model,
      platform: d.platform === 1 ? 'android' : 'ios',
      os_version: d.version,
      manufacturer: d.manufacturer,
      resolution: d.size,
      // 关键：根据 status 判断设备状态
      status: d.status === 'ONLINE' || d.status === 'DEBUGGING' ? 'connected' : 'disconnected',
      is_busy: d.status === 'DEBUGGING',  // DEBUGGING 表示设备被占用
      user: d.user,  // 当前占用用户
      agent_id: d.agentId,
      // Agent 运行在本地时，使用 localhost（不受本地 IP 变化影响）
      agent_host: d.agentHost || 'localhost',
      agent_port: d.agentPort || 7777,
      cpu: d.cpu || '-',
      mem: d.mem || '-',
      remark: d.remark || d.comment || '-'
    }))
  } catch (e) {
    return []
  }
}

// 打开设备选择器
function openDeviceSelector() {
  showDeviceSelector.value = true
  // 如果当前有选中的设备，回显
  pendingDevice.value = selectedDevice.value
  refreshDevices()
}

function handleCurrentDeviceChange(val) {
  if (val) {
    if (val.status !== 'connected') {
      ElMessage.warning('设备离线，无法连接')
      // 清除表格选中状态可能比较麻烦，el-table 自动处理样式
      // 但我们需要阻止 pendingDevice 更新吗？
      // 为了用户体验，点击离线设备也可以选中查看详情，但不能 confirm
      // 这里我们还是让它选中，但 confirm 时再校验，或者已经在 column button 里 disable 了
    }
    if (val.is_busy) {
      ElMessage.warning('设备正在被占用')
    }
    pendingDevice.value = val
  }
}

function quickConnect(row) {
  pendingDevice.value = row
  confirmDevice()
}

// 兼容旧的 selectDevice 逻辑 (如果还有引用)，但主要是为了 selectDevice 的逻辑检查
function selectDevice(device) {
  // 不再直接使用 clicked div，而是通过 el-table 的 current-change
  // 保留此函数做校验
  if (device.status !== 'connected') {
    return
  }
}

function confirmDevice() {
  if (!pendingDevice.value) return
  
  showDeviceSelector.value = false
  selectedDevice.value = pendingDevice.value
  
  // Android 15+ 设备自动切换到 scrcpy 模式
  if (selectedDevice.value.platform === 'android') {
    const osVersion = parseInt(selectedDevice.value.os_version, 10)
    if (osVersion >= 15 && screenMode.value !== 'scrcpy') {
      screenMode.value = 'scrcpy'
      localStorage.setItem('screenMode', 'scrcpy')
      ElMessage.info('Android 15+ 设备已自动切换到 scrcpy 模式')
    }
  }
  
  // 如果之前已连接，断开并重连新设备
  if (connected.value) {
    disconnect()
    // 稍微延迟等待清理
    setTimeout(() => startMirror(), 500)
  } else {
    startMirror()
  }
}

function disconnect() {
  // 清理心跳
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  
  // 关闭 iOS WebSocket 连接 - 这会触发 Agent 停止 WDA
  if (iosWs) {
    try { 
      // 发送关闭消息给 Agent，确保 WDA 停止
      if (iosWs.readyState === WebSocket.OPEN) {
        iosWs.send(JSON.stringify({ msg: 'close' }))
      }
      iosWs.close() 
    } catch (e) {}
    iosWs = null
  }
  
  // 关闭投屏连接 (Android)
  if (screenWs) {
    try { screenWs.close() } catch (e) {}
    screenWs = null
  }
  
  // 关闭控制连接 (Android) - 这会触发 Agent 释放设备锁
  if (controlWs) {
    try { controlWs.close() } catch (e) {}
    controlWs = null
  }
  
  // 清理状态
  if (currentFrame.value?.startsWith('blob:')) {
    URL.revokeObjectURL(currentFrame.value)
  }
  currentFrame.value = ''
  connected.value = false
  loading.value = false
  connectionError.value = ''
  touchReady = false
  controlStatus.value = 'disconnected'
  selectedDevice.value = null
  retryCount = 0
  wdaPort.value = 0
  imageLoaded.value = false  // 重置图片加载状态
}

/**
 * 🔑 核心连接函数 - 参照 Sonic 官方实现
 * 
 * 官方连接流程：
 * 1. 建立控制 WebSocket（/websockets/android/{key}/{udId}/{token}）
 *    - 这会触发 Agent 的设备锁定和初始化流程
 *    - 控制连接必须保持打开，用于发送触控命令
 * 2. 建立投屏 WebSocket（/websockets/android/screen/{key}/{udId}/{token}）
 *    - 只用于接收视频流
 *    - 发送 switch 命令启动投屏
 * 
 * 关键点：控制连接必须在整个会话期间保持打开！
 */
async function startMirror() {
  if (!selectedDevice.value) return
  if (isConnecting.value) return
  isConnecting.value = true
  
  loading.value = true
  connected.value = false
  connectionError.value = ''
  currentFrame.value = ''
  
  // 解析设备分辨率
  if (selectedDevice.value.resolution) {
    const [w, h] = selectedDevice.value.resolution.split('x').map(Number)
    if (w && h) {
      deviceWidth.value = w
      deviceHeight.value = h
    }
  }
  
  // 获取 Token
  if (!sonicToken) {
    const ok = await getSonicToken()
    if (!ok) {
      connectionError.value = 'Sonic Server 连接失败'
      loading.value = false
      isConnecting.value = false
      return
    }
  }
  
  const { udid, agent_host, agent_port, platform } = selectedDevice.value
  const host = agent_host === 'host.docker.internal' ? 'localhost' : (agent_host || 'localhost')
  const port = agent_port || 7777
  
  // iOS 使用 WDA
  if (platform === 'iOS' || platform === 'ios') {
    startIOSMirror(udid)
    return
  }
  
  // Android: 建立控制和投屏 WebSocket
  const controlUrl = `ws://${host}:${port}/websockets/android/${SONIC_AGENT_KEY}/${udid}/${sonicToken}`
  
  try {
    await openControlSocket(controlUrl)
  } catch (e) {
    connectionError.value = '无法连接设备，请确认设备在线'
    loading.value = false
    isConnecting.value = false
    return
  }
  
  const screenUrl = `ws://${host}:${port}/websockets/android/screen/${SONIC_AGENT_KEY}/${udid}/${sonicToken}`
  openScreenSocket(screenUrl)
}

/**
 * 建立控制 WebSocket 连接
 */
function openControlSocket(url) {
  return new Promise((resolve, reject) => {
    if (controlWs && controlWs.readyState === WebSocket.OPEN) {
      resolve()
      return
    }
    
    if (controlWs) {
      try { controlWs.close() } catch (e) {}
      controlWs = null
    }
    
    controlStatus.value = 'connecting'
    const ws = new WebSocket(url)
    let connectTimeout = null
    let resolved = false
    
    ws.onopen = () => {
      controlWs = ws
      controlStatus.value = 'ready'
      connectTimeout = setTimeout(() => {
        if (!resolved) {
          resolved = true
          resolve()
        }
      }, 6000)
    }
    
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        
        if (msg.msg === 'sas' && msg.isEnable) {
          touchReady = true
          if (!resolved) {
            resolved = true
            clearTimeout(connectTimeout)
            resolve()
          }
        }
        
        if (msg.msg === 'openDriver') {
          if (msg.status === 1 || msg.status === 'success') {
            if (!resolved) {
              resolved = true
              clearTimeout(connectTimeout)
              resolve()
            }
          }
        }
        
        if (msg.msg === 'error') {
          if (!resolved) {
            resolved = true
            clearTimeout(connectTimeout)
            const errorMsg = msg.detail || msg.text || ''
            if (errorMsg.includes('lock') || errorMsg.includes('busy') || errorMsg.includes('占用')) {
              reject(new Error('设备正在被占用，请稍后再试'))
            } else {
              reject(new Error(errorMsg || '设备连接失败'))
            }
          }
        }
      } catch (e) {}
    }
    
    ws.onerror = (e) => {
      controlStatus.value = 'disconnected'
      if (!resolved) {
        resolved = true
        clearTimeout(connectTimeout)
        reject(new Error('控制连接失败'))
      }
    }
    
    ws.onclose = (e) => {
      if (controlWs === ws) {
        controlWs = null
        controlStatus.value = 'disconnected'
        touchReady = false
        
        if (connected.value && selectedDevice.value) {
          setTimeout(() => {
            if (connected.value && selectedDevice.value && !controlWs) {
              reconnectControl()
            }
          }, 2000)
        }
      }
      
      if (!resolved) {
        resolved = true
        clearTimeout(connectTimeout)
        if (e.code === 1000) {
          resolve()
        } else {
          reject(new Error('控制连接异常关闭'))
        }
      }
    }
  })
}

/**
 * 建立投屏 WebSocket 连接
 */
function openScreenSocket(url) {
  // 关闭旧连接
  if (screenWs) {
    try { screenWs.close() } catch (e) {}
    screenWs = null
  }
  
  screenWs = new WebSocket(url)
  
  screenWs.onopen = () => {
    const cmd = { type: 'switch', detail: screenMode.value }
    screenWs.send(JSON.stringify(cmd))
  }
  
  screenWs.onmessage = (event) => {
    if (event.data instanceof Blob) {
      if (!connected.value) {
        connected.value = true
        loading.value = false
        isConnecting.value = false
        retryCount = 0
        emit('device-connected', selectedDevice.value)
      }
      
      if (currentFrame.value) {
        URL.revokeObjectURL(currentFrame.value)
      }
      currentFrame.value = URL.createObjectURL(event.data)
      frameCount++ // Android FPS 统计
    } else {
      try {
        const msg = JSON.parse(event.data)
        if (msg.msg === 'error') {
          handleScreenError()
        }
      } catch (e) {}
    }
  }
  
  screenWs.onerror = () => {
    handleScreenError()
  }
  
  screenWs.onclose = () => {
    if (screenWs) {
      screenWs = null
      if (connected.value) {
        connected.value = false
        connectionError.value = '投屏连接已断开'
      }
    }
  }
}

/**
 * 切换投屏模式（scrcpy / minicap）
 */
function toggleScreenMode() {
  const newMode = screenMode.value === 'scrcpy' ? 'minicap' : 'scrcpy'
  screenMode.value = newMode
  localStorage.setItem('screenMode', newMode)
  
  if (screenWs && screenWs.readyState === WebSocket.OPEN) {
    screenWs.send(JSON.stringify({ type: 'switch', detail: newMode }))
  }
}

/**
 * 在加载中切换投屏模式时，重新连接
 */
function onScreenModeChange(newMode) {
  localStorage.setItem('screenMode', newMode)
  stopMirror()
  setTimeout(() => {
    startMirror()
  }, 500)
}

/**
 * 重新连接控制 WebSocket（投屏保持不变）
 */
async function reconnectControl() {
  if (!selectedDevice.value || controlWs) return
  
  const { udid, agent_host, agent_port } = selectedDevice.value
  const host = agent_host === 'host.docker.internal' ? 'localhost' : (agent_host || 'localhost')
  const port = agent_port || 7777
  const controlUrl = `ws://${host}:${port}/websockets/android/${SONIC_AGENT_KEY}/${udid}/${sonicToken}`
  
  try {
    await openControlSocket(controlUrl)
  } catch (e) {
    // 静默失败
  }
}

/**
 * 处理投屏错误，尝试重连
 */
function handleScreenError() {
  if (retryCount < 3) {
    retryCount++
    
    // 关闭当前投屏连接
    if (screenWs) {
      try { screenWs.close() } catch (e) {}
      screenWs = null
    }
    
    // 等待后重试
    setTimeout(() => {
      if (selectedDevice.value && controlWs && controlWs.readyState === WebSocket.OPEN) {
        const { udid, agent_host, agent_port } = selectedDevice.value
        const host = agent_host === 'host.docker.internal' ? 'localhost' : (agent_host || 'localhost')
        const port = agent_port || 7777
        const screenUrl = `ws://${host}:${port}/websockets/android/screen/${SONIC_AGENT_KEY}/${udid}/${sonicToken}`
        openScreenSocket(screenUrl)
      } else {
        connectionError.value = '连接失败，请重试'
        loading.value = false
        isConnecting.value = false
      }
    }, 1000 * retryCount)
  } else {
    connectionError.value = '连接失败，请稍后重试'
    loading.value = false
    isConnecting.value = false
  }
}

// iOS 投屏 - 使用 Sonic Agent 原生 WebSocket
let iosWs = null
let wdaWidth = 393
let wdaHeight = 852

async function startIOSMirror(udid) {
  // if (isConnecting.value) return  // 注释掉此行，因为 startMirror 已经设置了 true
  isConnecting.value = true
  loading.value = true
  connectionError.value = ''
  
  try {
    debugStatus.value = 'GET_TOKEN'
    if (!sonicToken) {
      if (!await getSonicToken()) {
        debugStatus.value = 'GET_TOKEN_FAIL'
        throw new Error('无法获取 Sonic Token')
      }
    }

    const device = selectedDevice.value
    const host = 'localhost' 
    const port = device.agent_port || 7777
    const wsUrl = `ws://${host}:${port}/websockets/ios/${SONIC_AGENT_KEY}/${udid}/${sonicToken}`
    
    debugWsUrl.value = wsUrl
    debugStatus.value = 'CONNECTING'
    
    // 超时保护
    const connectionTimeout = setTimeout(() => {
        if (loading.value && !connected.value) {
            debugStatus.value = 'TIMEOUT'
            connectionError.value = '连接超时'
            loading.value = false
            isConnecting.value = false
            if(iosWs) iosWs.close()
        }
    }, 40000)

    iosWs = new WebSocket(wsUrl)
    
    iosWs.onopen = () => {
      debugStatus.value = 'WS_OPEN'
    }
    
    iosWs.onmessage = (event) => {
      clearTimeout(connectionTimeout)
      try {
        debugLastMsg.value = event.data.substring(0, 50)
        const msg = JSON.parse(event.data)
        
        switch (msg.msg) {
          case 'openDriver':
            if (msg.status === 'success') {
              debugStatus.value = 'WDA_SUCCESS'
              if (msg.wda) {
                wdaPort.value = msg.wda
              }
              if (msg.width && msg.height) {
                deviceWidth.value = msg.width
                deviceHeight.value = msg.height
                wdaWidth = msg.width
                wdaHeight = msg.height
              }
            } else if (msg.status === 'error') {
              debugStatus.value = 'WDA_ERROR'
              connectionError.value = 'WDA 启动失败'
            }
            break
            
          case 'share':
            if (msg.port > 0) {
              debugStatus.value = 'GOT_SHARE'
              const streamUrl = `http://${host}:${msg.port}`
              currentFrame.value = streamUrl
              connected.value = true
              loading.value = false
              isConnecting.value = false
              touchReady = true
              emit('device-connected', selectedDevice.value)
            } else {
              debugStatus.value = 'INVALID_PORT'
            }
            break
            
          case 'error':
            debugStatus.value = 'AGENT_ERROR'
            connectionError.value = 'Agent 内部错误'
            break
        }
      } catch (e) {}
    }
    
    iosWs.onerror = () => {
      debugStatus.value = 'WS_ERROR'
      connectionError.value = '连接 Agent 失败'
      loading.value = false
      isConnecting.value = false
    }
    
    iosWs.onclose = (e) => {
      debugStatus.value = `WS_CLOSE:${e.code}`
      if (connected.value) {
        connected.value = false
      }
      loading.value = false
      isConnecting.value = false
      iosWs = null
    }

  } catch (e) {
    debugStatus.value = `EXCEPTION:${e.message}`
    connectionError.value = e.message
    loading.value = false
    isConnecting.value = false
  }
}

function stopMirror() {
  // 通用停止逻辑
  if (selectedDevice.value?.platform === 'ios' || selectedDevice.value?.platform === 'iOS') {
    if (iosWs) {
      try { 
        // 发送关闭消息给 Agent，确保 WDA 停止
        if (iosWs.readyState === WebSocket.OPEN) {
          iosWs.send(JSON.stringify({ msg: 'close' }))
        }
        iosWs.close() 
      } catch (e) {}
      iosWs = null
    }
  } else {
    // Android 清理
    if (screenWs) { 
      try { screenWs.close() } catch (e) {}
      screenWs = null 
    }
    if (controlWs) {
      try { controlWs.close() } catch (e) {}
      controlWs = null
    }
  }
  
  if (currentFrame.value?.startsWith('blob:')) {
    URL.revokeObjectURL(currentFrame.value)
  }
  currentFrame.value = ''
  connected.value = false
  loading.value = false
  connectionError.value = ''
  retryCount = 0
  touchReady = false
  imageLoaded.value = false
  imageLoaded.value = false  // 重置图片加载状态
}

/**
 * 图片加载完成事件 - 标记图片已加载，解决白屏问题
 */
function onImageLoad(e) {
  if (!imageLoaded.value) {
    imageLoaded.value = true
  }
}

/**
 * 获取设备坐标 (Android) - 将鼠标点击位置转换为设备屏幕坐标
 */
/**
 * 获取设备坐标 (Android) 
 * 处理 object-fit: contain 的留白偏移，并映射到真实设备坐标
 */
function getDeviceCoords(clientX, clientY) {
  const img = screenImg.value
  if (!img) return null
  
  const rect = img.getBoundingClientRect()
  
  // 图片的自然尺寸（这是流的分辨率，可能是压缩过的，如 360x800）
  const nw = img.naturalWidth
  const nh = img.naturalHeight
  if (!nw || !nh) return null
  
  // ⚠️ 关键修正：不要用流分辨率覆盖 deviceWidth！
  // deviceWidth / deviceHeight 必须代表物理分辨率（例如 1080x1920 或 1080x2400）
  // 暂时如果 deviceWidth 未初始化，才兜底，但默认已经是 1080 了
  
  // 调试分辨率
  // console.log(`📐 getDeviceCoords: img=${nw}x${nh}, device=${deviceWidth}x${deviceHeight}, rawClick=${clientX},${clientY}`)
  
  // 计算实际渲染区域（处理 object-fit: contain 产生的留白）
  // 1. 计算显示比例
  const elementRatio = rect.width / rect.height
  const fluidRatio = nw / nh
  
  let drawWidth, drawHeight, startX, startY
  
  if (fluidRatio > elementRatio) {
    // 图片更宽，上下留白（或刚好）
    drawWidth = rect.width
    drawHeight = rect.width / fluidRatio
    startX = 0
    startY = (rect.height - drawHeight) / 2
  } else {
    // 图片更高，左右留白
    drawHeight = rect.height
    drawWidth = rect.height * fluidRatio
    startX = (rect.width - drawWidth) / 2
    startY = 0
  }
  
  // 2. 计算点击位置相对于 img 元素的坐标
  const relX = clientX - rect.left
  const relY = clientY - rect.top
  
  // 3. 转换到绘制区域坐标（扣除留白）
  const contentX = relX - startX
  const contentY = relY - startY
  
  // 4. 检查是否点在留白处
  if (contentX < 0 || contentX > drawWidth || contentY < 0 || contentY > drawHeight) {
    return null
  }
  
  // 5. 映射到设备真实坐标（物理坐标）
  // 使用 deviceWidth (默认1080) 进行投影
  const x = Math.round((contentX / drawWidth) * deviceWidth.value)
  const y = Math.round((contentY / drawHeight) * deviceHeight.value)
  
  return { x, y }
}

/**
 * 获取 WDA 坐标 (iOS) - 将鼠标点击位置转换为 WDA 坐标
 */
function getWDACoords(clientX, clientY) {
  const img = screenImg.value
  if (!img) return null
  
  const rect = img.getBoundingClientRect()
  const relX = clientX - rect.left
  const relY = clientY - rect.top
  
  if (relX < 0 || relY < 0 || relX > rect.width || relY > rect.height) {
    return null
  }
  
  const x = Math.round((relX / rect.width) * wdaWidth)
  const y = Math.round((relY / rect.height) * wdaHeight)
  return { x, y }
}

// 辅助函数
function isIOSDevice() {
  return selectedDevice.value?.platform === 'ios' || selectedDevice.value?.platform === 'iOS'
}

function isAndroidDevice() {
  return !isIOSDevice()
}

// iOS Sonic 协议触控实现
let iosTapTimer = null  // iOS 快速点击计时器
let iosIsSwiping = false // iOS 是否正在滑动

function sendIOSCommand(cmd) {
  if (!iosWs || iosWs.readyState !== WebSocket.OPEN) {
    return false
  }
  iosWs.send(JSON.stringify(cmd))
  return true
}

/**
 * iOS 点击 - 立即发送，无需等待
 */
function wdaTap(clientX, clientY) {
  if (!selectedDevice.value || !isIOSDevice()) return
  const pt = getWDACoords(clientX, clientY)
  if (!pt) return
  
  sendIOSCommand({
    type: 'debug',
    detail: 'tap',
    point: `${pt.x},${pt.y}`
  })
}

/**
 * iOS 滑动 - 发送滑动命令
 */
function wdaSwipe(startX, startY, endX, endY) {
  if (!selectedDevice.value || !isIOSDevice()) return
  const startPt = getWDACoords(startX, startY)
  const endPt = getWDACoords(endX, endY)
  if (!startPt || !endPt) return
  
  sendIOSCommand({
    type: 'debug',
    detail: 'swipe',
    pointA: `${startPt.x},${startPt.y}`,
    pointB: `${endPt.x},${endPt.y}`
  })
}

/**
 * iOS mousedown 处理 - 快速响应点击
 * 策略：100ms 内无移动则立即发送 tap，提升响应速度
 */
function handleIOSMouseDown(clientX, clientY) {
  if (iosTapTimer) {
    clearTimeout(iosTapTimer)
    iosTapTimer = null
  }
  iosIsSwiping = false
  
  // 100ms 后如果没有移动，立即发送 tap
  iosTapTimer = setTimeout(() => {
    if (!iosIsSwiping && isMouseDown) {
      // 仍然按住且没有移动 = 可能是长按或即将点击
      // 这里不发送，等 mouseup 时再处理
    }
    iosTapTimer = null
  }, 100)
}

/**
 * iOS mousemove 处理 - 标记为滑动
 */
function handleIOSMouseMove(clientX, clientY) {
  const deltaX = clientX - mouseStartX
  const deltaY = clientY - mouseStartY
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  
  // 移动超过 8px 标记为滑动
  if (distance > 8) {
    iosIsSwiping = true
    if (iosTapTimer) {
      clearTimeout(iosTapTimer)
      iosTapTimer = null
    }
  }
}

/**
 * iOS mouseup 处理 - 根据行为发送 tap 或 swipe
 */
function handleIOSMouseUp(startX, startY, endX, endY, duration) {
  if (iosTapTimer) {
    clearTimeout(iosTapTimer)
    iosTapTimer = null
  }
  
  const deltaX = endX - startX
  const deltaY = endY - startY
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  
  // 快速点击判定：移动 < 10px 且时间 < 200ms
  if (distance < 10 && duration < 200) {
    wdaTap(startX, startY)
  } else if (distance >= 10) {
    // 滑动
    wdaSwipe(startX, startY, endX, endY)
  } else {
    // 长按后释放，也发送 tap
    wdaTap(startX, startY)
  }
  
  iosIsSwiping = false
}

function sendControlCommand(cmd) {
  if (!controlWs || controlWs.readyState !== WebSocket.OPEN) {
    if (isIOSDevice()) return false
    return false
  }
  try {
    controlWs.send(JSON.stringify(cmd))
    return true
  } catch (e) {
    return false
  }
}

/**
 * 鼠标按下事件处理 - 记录起始位置，绑定全局事件
 */
/**
 * 发送 Android 底层触控指令
 * 协议格式: down x y / move x y / up
 */
function sendAndroidTouch(action, x, y) {
  if (!connected.value || !isAndroidDevice()) return
  
  if (!touchReady && controlWs?.readyState !== WebSocket.OPEN) {
    reconnectControl()
    return
  }
  
  // 必须加换行符，因为 Agent 是按行读取的
  let cmd = ''
  if (action === 'down' || action === 'move') {
    cmd = `${action} ${Math.round(x)} ${Math.round(y)}\n`
  } else if (action === 'up') {
    cmd = `up\n`
  }
  
  if (cmd) {
    sendControlCommand({
      type: 'touch',
      detail: cmd
    })
  }
}

/**
 * 鼠标按下事件处理
 */
function handleMouseDown(e) {
  if (!connected.value) return
  
  e.preventDefault()
  isMouseDown = true
  mouseStartX = e.clientX
  mouseStartY = e.clientY
  mouseStartTime = Date.now()
  lastMoveTime = Date.now()
  
  document.addEventListener('mousemove', onDocumentMouseMove)
  document.addEventListener('mouseup', onDocumentMouseUp)
  
  if (isAndroidDevice()) {
    // Android: 立即发送 down 事件
    const coords = getDeviceCoords(mouseStartX, mouseStartY)
    if (coords) {
      sendAndroidTouch('down', coords.x, coords.y)
    }
  } else if (isIOSDevice()) {
    // iOS: 初始化触控状态
    handleIOSMouseDown(mouseStartX, mouseStartY)
  }
}

/**
 * 鼠标移动事件处理
 */
function onDocumentMouseMove(e) {
  if (!isMouseDown) return
  
  const clientX = e.clientX
  const clientY = e.clientY
  
  if (isAndroidDevice()) {
    const now = Date.now()
    // Android: 节流 30ms 发送 move 事件
    if (now - lastMoveTime < 30) return
    lastMoveTime = now
    
    const coords = getDeviceCoords(clientX, clientY)
    if (coords) {
      sendAndroidTouch('move', coords.x, coords.y)
    }
  } else if (isIOSDevice()) {
    // iOS: 标记滑动状态（无节流，因为只是标记）
    handleIOSMouseMove(clientX, clientY)
  }
}

/**
 * 鼠标释放事件处理
 */
function onDocumentMouseUp(e) {
  if (!isMouseDown) return
  
  isMouseDown = false
  document.removeEventListener('mousemove', onDocumentMouseMove)
  document.removeEventListener('mouseup', onDocumentMouseUp)
  
  const endX = e.clientX
  const endY = e.clientY
  const duration = Date.now() - mouseStartTime
  
  if (isIOSDevice()) {
    // iOS: 使用优化后的处理函数
    handleIOSMouseUp(mouseStartX, mouseStartY, endX, endY, duration)
  } else {
    // Android: 发送 up 事件
    sendAndroidTouch('up', 0, 0)
  }
}


async function doBack() {
  if (isIOSDevice()) {
    // iOS 没有物理返回键，模拟左侧边缘右滑
    // 模拟从 (0, center) -> (center, center)
    const y = Math.round(wdaHeight / 2)
    const toX = Math.round(wdaWidth * 0.5)
    
    sendIOSCommand({
      type: 'debug',
      detail: 'swipe',
      pointA: `0,${y}`,
      pointB: `${toX},${y}`
    })
  } else {
    if (!sendControlCommand({ type: 'keyEvent', detail: 4 })) {
      ElMessage.warning('返回键发送失败')
    }
  }
}

async function doHome() {
  if (isIOSDevice()) {
    // 协议: {"type": "debug", "detail": "keyEvent", "key": "home"}
    sendIOSCommand({
      type: 'debug',
      detail: 'keyEvent',
      key: 'home'
    })
  } else {
    if (!sendControlCommand({ type: 'keyEvent', detail: 3 })) {
      ElMessage.warning('Home 键发送失败')
    }
  }
}

async function doAppSwitch() {
  if (isIOSDevice()) {
    ElMessage.info('iOS 暂不支持后台调度操作')
    // 可考虑模拟从底部上滑停顿，但较复杂
  } else {
    if (!sendControlCommand({ type: 'keyEvent', detail: 187 })) {
      ElMessage.warning('切换后台键发送失败')
    }
  }
}



defineExpose({
  selectedDevice,
  fps,
  screenMode,
  toggleScreenMode,
  disconnect,
  startMirror,
  doHome,
  doBack,
  doAppSwitch,
  refreshDevices,
  connected,
  wdaPort,
  deviceWidth,
  deviceHeight
})
</script>

<style lang="scss" scoped>
// 容器 - 未连接时居中显示手机框，连接后铺满
.device-mirror {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center; /* 垂直居中 */
  height: 100%;
  width: 100%;
  padding: 20px; /* 添加 padding 让手机框有呼吸空间 */
  background: transparent;
  position: relative;
  box-sizing: border-box;
  
  &.is-active {
    padding: 0; /* 连接后移除 padding */
    justify-content: flex-start; /* 连接后从顶部开始 */
    align-items: stretch; /* 连接后横向拉伸 */
    min-height: 0;
    overflow: hidden;
  }
}

// 顶部控制栏
.mirror-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 100%; /* 跟随手机宽度 */
  margin-bottom: 8px;
  padding: 0 4px;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-text-group {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.device-name {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.device-model {
  font-size: 13px;
  color: #303133;
  font-weight: 600;
}

.fps-badge {
  background: rgba(0, 0, 0, 0.6);
  color: #67c23a;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  font-family: 'Monaco', 'Consolas', monospace;
}

.mode-tag {
  text-transform: uppercase;
  font-size: 10px;
}

// 简洁手机外框样式
.phone-frame {
  position: relative;
  width: 220px;
  background: #fff;
  border-radius: 24px;
  border: 2px solid #e0e0e0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
  
  &--connected {
    width: 100%;
    flex: 1 1 0%;
    max-width: 100%;
    max-height: 100%;
    min-height: 0;
    border-radius: 0;
    border: none;
    background: transparent;
    box-shadow: none;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
}

// 底部操作栏 - Flex 布局，紧贴投屏画面
.mirror-footer {
  position: relative;
  flex-shrink: 0;
  flex-grow: 0; /* 不扩展 */
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 36px; /* 固定高度 */
  background: rgba(255, 255, 255, 0.98);
  border-top: 1px solid #e8e8e8;
  padding: 0 16px;
  margin: 0; /* 确保无间距 */
}

// 集成导航栏（嵌入屏幕底部）- 优雅简约设计
// 集成导航栏（嵌入屏幕底部）- 优雅简约设计
.integrated-navbar {
  display: flex;
  align-items: center;
  justify-content: space-around;
  gap: 4px; /* 减少间距 */
  background: #ffffff;
  padding: 0 4px; /* 去除上下 padding */
  border-top: none; /* 移除额外边框 */
  position: relative;
  width: 100%; /* 确保填满 footer */
}

.navbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px; /* 更宽的按钮触控区 */
  height: 32px; /* 更高 */
  color: #64748b;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  border-radius: 16px; /* 增加圆角 (胶囊形) */
  
  &:hover {
    color: #007aff;
    background: rgba(0, 122, 255, 0.06);
    transform: translateY(-1px);
  }
  
  &:active {
    background: rgba(0, 122, 255, 0.12);
    transform: translateY(0) scale(0.96);
  }
  
  .el-icon {
    font-size: 16px;
    font-weight: 300;
  }
}

// 旧的 nav-pill 样式（已废弃）
.nav-pill {
  display: flex;
  align-items: center;
  gap: 32px; /* Spaced out buttons */
  padding: 0 20px;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #f1f5f9;
    color: #3b82f6;
    transform: translateY(-1px);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

// 移除了 .top-info-bar 相关样式

// 顶部装饰（隐藏）
.phone-notch {
  display: none;
}

.phone-screen {
  width: 100%;
  aspect-ratio: 9 / 19.5;
  max-height: 480px;
  background: #f5f5f5;
  border-radius: 22px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  
  .phone-frame--connected & {
    width: 100%;
    height: 100%;
    aspect-ratio: unset;
    max-height: 100%;
    min-height: 0;
    border-radius: 0;
    background: transparent;
    flex: 1 1 0%;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
}

// 底部装饰（隐藏）
.phone-home-bar {
  display: none;
}

.screen-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #8e8e93;
  text-align: center;
  padding: 20px;
  width: 100%;
  flex: 1;
  
  .placeholder-icon {
    color: #c7c7cc;
  }
  
  p {
    margin: 0;
    font-size: 13px;
    color: #8e8e93;
  }
  
  .el-button {
    border-radius: 18px;
    padding: 8px 24px;
  }
  
  &.error {
    color: #ff3b30;
    p { color: #ff3b30; }
  }
}

// 投屏画面容器（用于叠加层定位）
.screen-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mirror-screen {
  display: block;
  max-width: 100%;
  max-height: 100%;
  width: 100%;
  height: 100%; /* 填满父容器高度 */
  object-fit: cover; /* 填满容器，避免留白 */
  cursor: pointer;
  user-select: none;
  -webkit-user-drag: none;
  touch-action: none;
}

// 悬浮操作栏
.floating-toolbar {
  position: absolute;
  right: -50px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  opacity: 0;
  transition: opacity 0.2s;
  
  .el-button {
    margin: 0 !important;
  }
}

.device-mirror:hover .floating-toolbar {
  opacity: 1;
}

// 底部状态栏 - 绝对定位在底部，不占用 flex 空间
.bottom-bar {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: auto;
  max-width: 260px;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.device-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.device-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
  
  .mode-tag {
    color: #909399;
  }
}

.connect-options {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-radio-button__inner {
    display: flex;
    align-items: center;
  }
}

// 设备列表弹窗高级样式
:deep(.el-dialog) {
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden; /* 确保圆角不被直角子元素遮挡 */
  
  .el-dialog__header {
    padding: 20px 24px 0;
    margin-right: 0;
  }
  
  .el-dialog__body {
    padding: 20px 24px;
  }
  
  .el-dialog__footer {
    padding: 16px 24px 24px;
    background: #f9fafe; /* 底部浅色背景区分 */
  }
}

.dialog-header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px; /* 增加舒适间距 */
}

// 表格美化
:deep(.el-table) {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: #f8f9fb;
  --el-table-row-hover-bg-color: #f5f7fa;
  
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  
  th.el-table__cell {
    font-weight: 600;
    color: #303133;
    background: #f8f9fb;
    height: 48px;
  }
  
  .el-table__row {
    transition: all 0.2s;
    cursor: pointer;
    
    &:hover {
      transform: scale(1.002); /* 极微小的放大反馈 */
      z-index: 1;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* 悬浮阴影 */
      background-color: #fff !important; /* 保持白色背景突出 */
    }
  }
}
</style>




