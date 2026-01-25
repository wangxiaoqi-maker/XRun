<template>
  <div class="devices-page">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1>设备管理</h1>
        <el-tag type="success" size="small">{{ onlineCount }} 在线</el-tag>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索设备名称/UDID"
          prefix-icon="Search"
          clearable
          style="width: 250px;"
        />
        <el-select v-model="filterPlatform" placeholder="平台" style="width: 120px;">
          <el-option label="全部" value="" />
          <el-option label="Android" value="android" />
          <el-option label="iOS" value="ios" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px;">
          <el-option label="全部" value="" />
          <el-option label="在线" value="connected" />
          <el-option label="离线" value="disconnected" />
          <el-option label="使用中" value="busy" />
        </el-select>
        <el-button type="primary" @click="refreshDevices" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>
    
    <!-- 设备卡片列表 -->
    <div class="devices-grid" v-loading="loading">
      <div 
        v-for="device in filteredDevices" 
        :key="device.udid"
        class="device-card"
        :class="{ 
          'is-online': device.status === 'connected',
          'is-busy': device.status === 'busy',
          'is-offline': device.status === 'disconnected'
        }"
      >
        <!-- 设备预览图 -->
        <div class="device-preview">
          <div class="device-frame">
            <div class="device-screen">
              <img v-if="device.screenshot" :src="device.screenshot" alt="预览" />
              <div v-else class="no-preview">
                <el-icon :size="32"><Iphone /></el-icon>
                <span>{{ device.status === 'connected' ? '点击投屏' : '设备离线' }}</span>
              </div>
            </div>
          </div>
          
          <!-- 状态指示器 -->
          <div class="status-indicator" :class="device.status">
            <span class="status-dot"></span>
            <span class="status-text">{{ getStatusText(device.status) }}</span>
          </div>
        </div>
        
        <!-- 设备信息 -->
        <div class="device-info">
          <div class="device-name">
            <el-icon v-if="device.platform === 'android'"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85a.637.637 0 0 0-.83.22l-1.88 3.24a11.463 11.463 0 0 0-8.94 0L5.65 5.67a.643.643 0 0 0-.87-.2c-.28.18-.37.54-.22.83L6.4 9.48A10.78 10.78 0 0 0 1 18h22a10.78 10.78 0 0 0-5.4-8.52zM7 15.25a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5zm10 0a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5z"/></svg></el-icon>
            <el-icon v-else><svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg></el-icon>
            <span>{{ device.name || device.model }}</span>
          </div>
          
          <div class="device-meta">
            <div class="meta-item">
              <span class="label">型号:</span>
              <span class="value">{{ device.model }}</span>
            </div>
            <div class="meta-item">
              <span class="label">系统:</span>
              <span class="value">{{ device.platform }} {{ device.os_version }}</span>
            </div>
            <div class="meta-item">
              <span class="label">分辨率:</span>
              <span class="value">{{ device.resolution }}</span>
            </div>
            <div class="meta-item">
              <span class="label">UDID:</span>
              <span class="value udid">{{ device.udid }}</span>
            </div>
          </div>
          
          <!-- Agent 信息 -->
          <div class="agent-info" v-if="device.agent_host">
            <el-tag size="small" type="info">
              Agent: {{ device.agent_host }}:{{ device.agent_port }}
            </el-tag>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="device-actions">
          <el-button 
            type="primary" 
            @click="openMirror(device)"
            :disabled="device.status !== 'connected'"
          >
            <el-icon><VideoPlay /></el-icon>
            投屏
          </el-button>
          <el-button 
            @click="runCase(device)"
            :disabled="device.status !== 'connected'"
          >
            <el-icon><CaretRight /></el-icon>
            执行
          </el-button>
          <el-dropdown trigger="click">
            <el-button>
              <el-icon><More /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="viewDetail(device)">
                  <el-icon><View /></el-icon>查看详情
                </el-dropdown-item>
                <el-dropdown-item @click="installApp(device)">
                  <el-icon><Download /></el-icon>安装应用
                </el-dropdown-item>
                <el-dropdown-item @click="captureScreen(device)">
                  <el-icon><Camera /></el-icon>截图
                </el-dropdown-item>
                <el-dropdown-item divided @click="rebootDevice(device)">
                  <el-icon><RefreshRight /></el-icon>重启设备
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="filteredDevices.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无设备">
          <el-button type="primary" @click="refreshDevices">刷新设备</el-button>
        </el-empty>
      </div>
    </div>
    
    <!-- 投屏弹窗 -->
    <el-dialog 
      v-model="mirrorDialogVisible" 
      :title="`投屏 - ${currentDevice?.name || ''}`"
      width="450px"
      class="mirror-dialog"
      destroy-on-close
    >
      <DeviceMirror 
        v-if="mirrorDialogVisible && currentDevice"
        :device="currentDevice"
        ref="mirrorRef"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Refresh, Search, Iphone, VideoPlay, CaretRight, More,
  View, Download, Camera, RefreshRight
} from '@element-plus/icons-vue'
import DeviceMirror from '@/components/DeviceMirror.vue'
import { deviceApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const searchKeyword = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')

const devices = ref([])

const mirrorDialogVisible = ref(false)
const currentDevice = ref(null)
const mirrorRef = ref(null)

// 在线设备数量
const onlineCount = computed(() => {
  return devices.value.filter(d => d.status === 'connected').length
})

// 过滤后的设备列表
const filteredDevices = computed(() => {
  return devices.value.filter(device => {
    // 关键词搜索
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      const matchName = (device.name || '').toLowerCase().includes(keyword)
      const matchUdid = device.udid.toLowerCase().includes(keyword)
      const matchModel = (device.model || '').toLowerCase().includes(keyword)
      if (!matchName && !matchUdid && !matchModel) return false
    }
    
    // 平台过滤
    if (filterPlatform.value && device.platform !== filterPlatform.value) {
      return false
    }
    
    // 状态过滤
    if (filterStatus.value && device.status !== filterStatus.value) {
      return false
    }
    
    return true
  })
})

function getStatusText(status) {
  const map = {
    'connected': '在线',
    'disconnected': '离线',
    'busy': '使用中'
  }
  return map[status] || '未知'
}

async function refreshDevices() {
  loading.value = true
  try {
    const res = await deviceApi.list()
    // 合并 Android 和 iOS 设备
    const androidDevices = (res.data.android || []).map(d => ({ ...d, platform: 'android' }))
    const iosDevices = (res.data.ios || []).map(d => ({ ...d, platform: 'ios' }))
    devices.value = [...androidDevices, ...iosDevices]
  } catch (e) {
    ElMessage.error('获取设备列表失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function openMirror(device) {
  // 跳转到投屏页面
  router.push({
    path: '/ui/mirror',
    query: { udid: device.udid }
  })
}

function runCase(device) {
  router.push({
    path: '/ui/cases',
    query: { device: device.udid }
  })
}

function viewDetail(device) {
  ElMessage.info('功能开发中')
}

function installApp(device) {
  ElMessage.info('功能开发中')
}

function captureScreen(device) {
  ElMessage.info('功能开发中')
}

function rebootDevice(device) {
  ElMessage.info('功能开发中')
}

onMounted(() => {
  refreshDevices()
})
</script>

<style lang="scss" scoped>
.devices-page {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h1 {
      font-size: 20px;
      font-weight: 600;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  flex: 1;
}

.device-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    transform: translateY(-4px);
  }
  
  &.is-online {
    border-color: var(--success-color);
  }
  
  &.is-offline {
    opacity: 0.7;
  }
}

.device-preview {
  position: relative;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  display: flex;
  justify-content: center;
}

.device-frame {
  width: 140px;
  height: 280px;
  background: #1a1a1a;
  border-radius: 24px;
  padding: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.device-screen {
  width: 100%;
  height: 100%;
  background: #2a2a2a;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .no-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    color: rgba(255, 255, 255, 0.5);
    
    span {
      font-size: 12px;
    }
  }
}

.status-indicator {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  font-size: 12px;
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
  
  &.connected {
    .status-dot { background: var(--success-color); }
    .status-text { color: var(--success-color); }
  }
  
  &.disconnected {
    .status-dot { background: #d9d9d9; }
    .status-text { color: var(--text-muted); }
  }
  
  &.busy {
    .status-dot { background: var(--warning-color); }
    .status-text { color: var(--warning-color); }
  }
}

.device-info {
  padding: 16px;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  
  .el-icon {
    font-size: 20px;
    
    svg {
      width: 20px;
      height: 20px;
    }
  }
}

.device-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 13px;
  
  .meta-item {
    .label {
      color: var(--text-muted);
      margin-right: 4px;
    }
    
    .value {
      color: var(--text-secondary);
      
      &.udid {
        font-family: monospace;
        font-size: 11px;
      }
    }
  }
}

.agent-info {
  margin-top: 12px;
}

.device-actions {
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 8px;
  
  .el-button {
    flex: 1;
    
    &:last-child {
      flex: none;
    }
  }
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px;
  text-align: center;
}

.mirror-dialog {
  :deep(.el-dialog__body) {
    padding: 0;
    background: #1a1a2e;
  }
}
</style>






