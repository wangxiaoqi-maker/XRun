<template>
  <div class="mirror-page">
    <!-- View 1: Device List (Management) -->
    <div v-if="currentView === 'list'" class="device-list-view">
      <!-- Filter Bar -->
      <div class="filter-bar">
        <div class="filter-group">
          <span class="label">机型品牌:</span>
          <div class="tags">
            <el-tag 
              v-for="brand in brands" 
              :key="brand" 
              :effect="filterBrand === brand ? 'dark' : 'plain'"
              @click="filterBrand = filterBrand === brand ? '' : brand"
              class="filter-tag"
            >
              {{ brand }}
            </el-tag>
          </div>
        </div>
        <div class="search-box">
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索设备型号/序列号" 
            :prefix-icon="Search"
            clearable 
          />
          <el-button @click="refreshDevices" :loading="loading" icon="Refresh" circle />
        </div>
      </div>

      <!-- Device Grid -->
      <div class="device-grid" v-loading="loading">
        <div 
          v-for="device in filteredDevices" 
          :key="device.udid" 
          class="device-card"
          @click="startDebug(device)"
        >
          <!-- Status Badge -->
          <div class="status-badge" :class="getStatusClass(device)">
            {{ getStatusText(device) }}
          </div>

          <div class="card-body">
            <!-- Left: Image -->
            <div class="device-img" :class="{ 'is-pad': isPad(device) }">
              <img 
                v-show="!imgErrors[device.udid]" 
                :src="getDeviceImage(device)" 
                @error="handleImgError(device.udid)" 
                alt="Phone" 
              />
              <el-icon v-if="imgErrors[device.udid]" :size="48" class="placeholder-icon">
                <Iphone v-if="device.platform === 'ios'" />
                <Platform v-else />
              </el-icon>
            </div>
            
            <!-- Right: Info -->
            <div class="device-details">
              <div class="header">
                <!-- OS Icon Logic -->
                <el-icon v-if="isHarmony(device)" class="platform-icon harmony"><img src="/src/assets/logo.svg" style="width:16px;height:16px;filter:grayscale(1)"/></el-icon>
                <el-icon v-else-if="device.platform === 'ios'" class="platform-icon ios"><img :src="iconApple" style="width:16px;height:16px"/></el-icon>
                <el-icon v-else class="platform-icon android"><img :src="iconAndroid" style="width:16px;height:16px;object-fit:contain"/></el-icon>
                
                <span class="model" :title="device.model">{{ getDeviceName(device) }}</span>
              </div>
              
              <div class="info-row">
                <span class="label">型号:</span>
                <span class="value">{{ device.model }}</span>
              </div>
              
              <div class="info-row" v-if="device.market_time">
                <span class="label">上市:</span>
                <span class="value">{{ device.market_time }}</span>
              </div>
              
              <div class="info-row">
                <span class="label">别名:</span>
                <span class="value">{{ device.name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">分辨率:</span>
                <span class="value">{{ device.resolution }}</span>
              </div>
              <div class="info-row">
                <span class="label">序列号:</span>
                <span class="value" :title="device.udid">{{ formatUdid(device.udid) }}</span>
              </div>
              <div class="info-row">
                <span class="label">制造商:</span>
                <span class="value">{{ device.manufacturer }}</span>
              </div>
            </div>
          </div>
          
          <div class="card-footer">
            <el-button 
              type="primary" 
              size="small" 
              round 
              v-if="device.status === 'online' && !device.is_busy"
            >
              立即调试
            </el-button>
            <el-button type="info" size="small" round disabled v-else>{{ getActionText(device) }}</el-button>
          </div>
        </div>
        
        <el-empty v-if="filteredDevices.length === 0" description="暂无符合条件的设备" style="width: 100%" />
      </div>
    </div>

    <!-- View 2: Debugging Dashboard -->
    <div v-else class="debug-view">
      <!-- Header -->
      <header class="debug-header">
        <div class="left">
          <el-button @click="stopDebug" icon="Back" circle />
          <div class="device-title">
            <span class="name">{{ currentDevice.manufacturer }} {{ currentDevice.model }}</span>
            <el-tag size="small" type="success" effect="dark">调试中</el-tag>
          </div>
        </div>
        <div class="center">
          <span class="timer">{{ debugDuration }}</span>
        </div>
        <div class="right">
          <el-button type="danger" @click="stopDebug">结束调试</el-button>
        </div>
      </header>

      <!-- Main Content Split -->
      <div class="debug-content">
        <!-- Left: Mirror (Reusing Component) -->
        <div class="mirror-panel">
          <DeviceMirror 
            :udid="currentDevice.udid" 
            :recording="false"
          />
        </div>

        <!-- Right: Tools -->
        <div class="tools-panel">
          <el-tabs v-model="activeTool" class="tools-tabs">
            <el-tab-pane label="应用列表" name="apps">
              <div class="tool-content">
                <div class="toolbar">
                  <el-upload
                    action="#"
                    :auto-upload="false"
                    :show-file-list="false"
                  >
                    <el-button type="primary" icon="Upload">安装应用</el-button>
                  </el-upload>
                  <el-button icon="Refresh" @click="refreshApps" :loading="appsLoading">刷新列表</el-button>
                </div>
                <el-table :data="appList" height="100%" stripe style="width: 100%" v-loading="appsLoading">
                  <el-table-column prop="name" label="应用名/包名" show-overflow-tooltip />
                  <el-table-column prop="version" label="版本" width="100" />
                  <el-table-column label="操作" width="100">
                    <template #default="scope">
                      <el-button 
                        link 
                        type="danger" 
                        @click="uninstallApp(scope.row)"
                      >
                        卸载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="Logcat" name="logcat">
              <div class="tool-content logcat-content">
                <div class="log-controls">
                  <el-select v-model="logLevel" size="small" style="width: 100px">
                    <el-option label="Verbose" value="V" />
                    <el-option label="Debug" value="D" />
                    <el-option label="Info" value="I" />
                    <el-option label="Warn" value="W" />
                    <el-option label="Error" value="E" />
                  </el-select>
                  <el-input placeholder="过滤日志..." size="small" style="width: 200px" prefix-icon="Search" />
                  <div class="spacer"></div>
                  <el-button size="small" icon="Delete" circle @click="clearLogs" />
                  <el-button size="small" type="danger" icon="VideoPause" circle @click="toggleLogcat" >
                    {{ isLogcatRunning ? '停止' : '开始' }}
                  </el-button>
                </div>
                <div class="log-viewer" ref="logViewer">
                  <div v-for="(log, index) in filteredLogs" :key="index" class="log-line">{{ log }}</div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="终端" name="terminal">
              <div class="tool-content terminal-content">
                <div class="term-window" ref="termWindow">
                  <div v-for="(line, i) in termLines" :key="i" class="term-line">{{ line }}</div>
                </div>
                <div class="term-input-row">
                  <span class="prompt">$</span>
                  <input 
                    v-model="termInput" 
                    @keyup.enter="sendShellCommand"
                    placeholder="输入命令..." 
                    class="term-input"
                  />
                </div>
              </div>
            </el-tab-pane>
            
             <el-tab-pane label="文件互传" name="files">
              <div class="tool-content">
                 <el-empty description="文件管理功能开发中" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 定义组件名称，用于 keep-alive 缓存控制
defineOptions({ name: 'MirrorView' })

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Search, Refresh, Platform, Iphone, Back, Monitor, Upload, Delete, VideoPause } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DeviceMirror from '@/components/DeviceMirror.vue'
import { deviceApi } from '@/api'

// State
const currentView = ref('list') // 'list' | 'debug'
const loading = ref(false)
const devices = ref([])
const searchKeyword = ref('')
const filterBrand = ref('')
const currentDevice = ref(null)

// Debug State
// Debug State
const activeTool = ref('apps')
const debugTimer = ref(null)
const debugSeconds = ref(0)
const appList = ref([])
const appsLoading = ref(false)
const logLevel = ref('D')
const logList = ref([])
const isLogcatRunning = ref(false)
let logws = null
const termLines = ref(['Welcome to Web Shell'])
const termInput = ref('')
let shellws = null

// Brands Calculation
const brands = computed(() => {
  const s = new Set(devices.value.map(d => d.manufacturer).filter(Boolean))
  return Array.from(s)
})

// Filtered Devices
const filteredDevices = computed(() => {
  let list = devices.value
  
  if (filterBrand.value) {
    list = list.filter(d => d.manufacturer === filterBrand.value)
  }
  
  if (searchKeyword.value) {
    const k = searchKeyword.value.toLowerCase()
    list = list.filter(d => 
      (d.model && d.model.toLowerCase().includes(k)) || 
      (d.udid && d.udid.toLowerCase().includes(k))
    )
  }
  
  return list
})

const debugDuration = computed(() => {
  const h = Math.floor(debugSeconds.value / 3600).toString().padStart(2, '0')
  const m = Math.floor((debugSeconds.value % 3600) / 60).toString().padStart(2, '0')
  const s = (debugSeconds.value % 60).toString().padStart(2, '0')
  return `${h} : ${m} : ${s}`
})

import iphonePlaceholder from '@/assets/iphone_placeholder.svg'
import androidPlaceholder from '@/assets/android_placeholder.svg'
import padPlaceholder from '@/assets/pad_placeholder.svg'
import iconApple from '@/assets/icon_apple.svg'
import iconAndroid from '@/assets/icon_android.svg'

const imgErrors = ref({})

// Methods
async function refreshDevices() {
  loading.value = true
  try {
    const res = await deviceApi.list()
    // Flatten structure
    const android = (res.data.android || []).map(d => ({ ...d, platform: 'android', status: d.status === 'connected' ? 'online' : 'offline' }))
    const ios = (res.data.ios || []).map(d => ({ ...d, platform: 'ios', status: d.status === 'connected' ? 'online' : 'offline' }))
    devices.value = [...android, ...ios]
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function startDebug(device) {
  if (device.status !== 'online') return
  if (device.is_busy) return
  
  currentDevice.value = device
  currentView.value = 'debug'
  startTimer()
}

function stopDebug() {
  currentView.value = 'list'
  currentDevice.value = null
  stopTimer()
}

function startTimer() {
  debugSeconds.value = 0
  debugTimer.value = setInterval(() => {
    debugSeconds.value++
  }, 1000)
}

function stopTimer() {
  if (debugTimer.value) clearInterval(debugTimer.value)
}

function getStatusClass(device) {
  if (device.is_busy) return 'busy'
  if (device.status === 'online') return 'online'
  return 'offline'
}

function getStatusText(device) {
  if (device.is_busy) return '设备占用中'
  if (device.status === 'online') return '在线'
  return '离线'
}

function getActionText(device) {
   if (device.status === 'online' && device.is_busy) return '占用中'
   if (device.status === 'online') return '立即调试'
   return '离线'
}

function getDeviceName(device) {
  // Priority: Manufacturer + Model -> Name (Alias) -> Model -> UDID
  if (device.manufacturer && device.model) {
    return `${device.manufacturer} ${device.model}`
  }
  if (device.name) return device.name
  return device.model || device.udid || 'Unknown Device'
}

function getDeviceImage(device) {
  if (device.platform === 'ios') return iphonePlaceholder
  if (isPad(device)) return padPlaceholder
  return androidPlaceholder
}

function isPad(device) {
  if (!device.model) return false
  const model = device.model.toLowerCase()
  return model.includes('pad') || model.includes('tablet')
}

function isHarmony(device) {
  // Simple heuristic for HarmonyOS context (Huawei/Honor)
  if (!device.manufacturer) return false
  const m = device.manufacturer.toLowerCase()
  return m.includes('huawei') || m.includes('honor')
}

function formatUdid(udid) {
  if (!udid) return '-'
  return udid.length > 8 ? udid.substring(0, 8) + '...' : udid
}

function handleImgError(udid) {
  imgErrors.value[udid] = true
}


// Tools Implementation

// 1. App List
async function refreshApps() {
  if (!currentDevice.value) return
  appsLoading.value = true
  appList.value = []
  
  const ws = deviceApi.connectAgentTerminal(currentDevice.value.udid)
  
  ws.onopen = () => {
    ws.send(JSON.stringify({ type: 'appList' }))
  }
  
  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      if (msg.msg === 'appListDetail' && msg.detail) {
        // detail format: { appName: "List", appList: [ { package: "...", name: "..." } ... ] }
        const rawList = msg.detail.appList || []
        appList.value = rawList.map(app => ({
          name: app.name || app.package,
          package: app.package,
          version: app.version || 'Unknown',
          isSystem: app.isSystem
        })).filter(app => !app.isSystem) 
        
        ws.close()
        appsLoading.value = false
      }
    } catch (err) {
      console.error(err)
    }
  }
  
  ws.onerror = () => {
    appsLoading.value = false
    ElMessage.error('连接失败')
  }
}

async function uninstallApp(row) {
  try {
    const ws = deviceApi.connectAgentGeneral(currentDevice.value.udid)
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: 'uninstallApp', detail: row.package }))
    }
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.msg === 'uninstallFinish') {
           if (msg.detail === 'success') {
              ElMessage.success('卸载成功')
              refreshApps()
           } else {
              ElMessage.error('卸载失败')
           }
           ws.close()
        }
      } catch (err) { console.error(err) }
    }
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

// 2. Logcat
const filteredLogs = computed(() => {
  if (!searchKeyword.value) return logList.value.slice(-500)
  return logList.value.filter(l => l.includes(searchKeyword.value)).slice(-500)
})

function toggleLogcat() {
  if (isLogcatRunning.value) {
    if (logws) {
      logws.send(JSON.stringify({ type: 'stopLogcat' }))
      logws.close()
    }
    isLogcatRunning.value = false
  } else {
    logList.value = []
    logws = deviceApi.connectAgentTerminal(currentDevice.value.udid)
    
    logws.onopen = () => {
      logws.send(JSON.stringify({ 
        type: 'logcat', 
        level: logLevel.value, 
        filter: '' 
      }))
    }
    
    logws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.msg === 'logcatResp') {
          logList.value.push(msg.detail)
          if (logList.value.length > 2000) logList.value.shift()
        }
      } catch (err) {}
    }
    isLogcatRunning.value = true
  }
}

function clearLogs() {
  logList.value = []
}

// 3. Shell
function initShell() {
  if (shellws) return
  shellws = deviceApi.connectAgentTerminal(currentDevice.value.udid)
  shellws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data)
      if (msg.msg === 'terminal') {
         termLines.value.push(`Connected to ${msg.user || 'Socket'}`)
      } else if (msg.msg === 'terResp') {
         termLines.value.push(msg.detail)
      }
    } catch (err) {
       termLines.value.push(e.data)
    }
  }
}

function sendShellCommand() {
  if (!shellws || !termInput.value) return
  const cmd = termInput.value
  termLines.value.push(`$ ${cmd}`)
  
  shellws.send(JSON.stringify({
    type: 'command',
    detail: cmd
  }))
  
  termInput.value = ''
}

// Watchers
watch(activeTool, (val) => {
   if (val === 'apps' && appList.value.length === 0) refreshApps()
   if (val === 'terminal') initShell()
})

onMounted(() => {
  refreshDevices()
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style lang="scss" scoped>
.mirror-page {
  /* height: calc(100vh - var(--header-height) - 32px); */
  height: 100%; /* 占满父容器 */
  width: 100%;
  background: #f5f7fa;
  /* border-radius: 8px; 移除圆角，改为全屏风格 */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* --- List View --- */
.device-list-view {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.filter-bar {
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.02);
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .filter-group {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .label {
      font-weight: 600;
      color: #303133;
    }
    
    .tags {
      display: flex;
      gap: 8px;
    }
    
    .filter-tag {
      cursor: pointer;
      border-radius: 4px;
      &:hover { opacity: 0.8; }
    }
  }
  
  .search-box {
    display: flex;
    gap: 12px;
    width: 300px;
  }
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.device-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  position: relative;
  transition: all 0.3s ease;
  cursor: pointer;
  border: 1px solid transparent; 
  box-shadow: 0 6px 16px rgba(0,0,0,0.08);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0,0,0,0.12);
  }
  
  .status-badge {
    position: absolute;
    top: 0;
    right: 0;
    padding: 4px 12px;
    font-size: 12px;
    color: #fff;
    border-radius: 0 12px 0 12px;
    font-weight: 500;
    
    &.online { background: var(--success-color); }
    &.busy { background: var(--warning-color); }
    &.offline { background: #909399; }
  }
  
  .card-body {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
  }
  
  .device-img {
    width: 60px;
    height: 100px;
    background: transparent;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
    transition: transform 0.3s ease;
    
    &:hover {
      transform: scale(1.05);
    }
    
    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    
    .placeholder-icon {
      color: #dcdfe6;
    }
  }
  
  .device-details {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 6px;
    
    .header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
      
      .platform-icon { font-size: 18px; }
      .android { color: #3ddc84; }
      .ios { color: #000; }
      
      .model {
        font-weight: 600;
        font-size: 18px;
        color: #303133;
      }
    }
    
    .info-row {
      display: flex;
      gap: 8px;
      font-size: 14px;
      color: #606266;
      margin-bottom: 2px;
      
      .label { color: #909399; }
      .value { font-weight: 500; }
    }
  }
  
  .card-footer {
    display: flex;
    justify-content: flex-end;
  }
}

/* --- Debug View --- */
.debug-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.debug-header {
  height: 56px;
  padding: 0 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  
  .left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .device-title {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .name {
        font-size: 16px;
        font-weight: 600;
      }
    }
  }
  
  .timer {
    font-family: monospace;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    padding: 4px 12px;
    background: #f5f7fa;
    border-radius: 4px;
  }
}

.debug-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  
  .mirror-panel {
    flex: 0 0 400px;
    border-right: 1px solid #eee;
    background: #f5f7fa;
    display: flex;
    justify-content: center;
    padding-top: 20px;
    overflow: hidden;
  }
  
  .tools-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #fff;
    min-width: 0;
    
    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0 20px;
      border-bottom: 1px solid #eee;
    }
    
    :deep(.el-tabs__content) {
      flex: 1;
      padding: 0;
      overflow-y: auto;
    }
    
    .tools-tabs {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
  }
}

.tool-content {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.logcat-content {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 0;
  
  .log-controls {
    padding: 8px 16px;
    background: #2d2d2d;
    display: flex;
    gap: 12px;
    align-items: center;
  }
  
  .log-viewer {
    flex: 1;
    padding: 12px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
    line-height: 1.5;
    
    .log-line {
      margin-bottom: 2px;
      &:hover { background: #333; }
    }
  }
}

.terminal-content {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  color: #0f0;
}

.terminal-placeholder {
  text-align: center;
  color: #333;
  p { margin-top: 16px; }
}
</style>




