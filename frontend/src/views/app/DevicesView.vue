<template>
  <div class="devices-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>手机管理</h2>
      <div class="header-actions">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索设备名称/UDID"
          :prefix-icon="Search"
          clearable
          style="width: 240px;"
        />
        <el-select v-model="filterPlatform" placeholder="平台" style="width: 100px;">
          <el-option label="全部" value="" />
          <el-option label="Android" value="android" />
          <el-option label="iOS" value="ios" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="状态" style="width: 100px;">
          <el-option label="全部" value="" />
          <el-option label="在线" value="online" />
          <el-option label="离线" value="offline" />
          <el-option label="使用中" value="busy" />
        </el-select>
        <el-button @click="refreshDevices" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>
    
    <!-- 统计栏 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">设备总数</span>
        <span class="stat-value">{{ devices.length }}</span>
      </div>
      <div class="stat-item online">
        <span class="stat-label">在线</span>
        <span class="stat-value">{{ onlineCount }}</span>
      </div>
      <div class="stat-item offline">
        <span class="stat-label">离线</span>
        <span class="stat-value">{{ offlineCount }}</span>
      </div>
      <div class="stat-item busy">
        <span class="stat-label">使用中</span>
        <span class="stat-value">{{ busyCount }}</span>
      </div>
    </div>
    
    <!-- 设备表格 -->
    <div class="devices-table">
      <el-table 
        :data="filteredDevices" 
        style="width: 100%"
        v-loading="loading"
        border
        size="small"
      >
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="设备名称" min-width="150">
          <template #default="{ row }">
            <div class="device-name">
              <el-icon v-if="row.platform === 'android'" class="android-icon">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85a.637.637 0 0 0-.83.22l-1.88 3.24a11.463 11.463 0 0 0-8.94 0L5.65 5.67a.643.643 0 0 0-.87-.2c-.28.18-.37.54-.22.83L6.4 9.48A10.78 10.78 0 0 0 1 18h22a10.78 10.78 0 0 0-5.4-8.52z"/></svg>
              </el-icon>
              <el-icon v-else class="ios-icon">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="platform" label="平台" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.platform === 'android' ? 'success' : ''">
              {{ row.platform === 'android' ? 'Android' : 'iOS' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="os_version" label="系统版本" width="100" />
        <el-table-column prop="resolution" label="分辨率" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <span :class="['status-dot', row.status]"></span>
            <span>{{ getStatusText(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="agent" label="Agent" width="180">
          <template #default="{ row }">
            {{ row.agent_host }}:{{ row.agent_port }}
          </template>
        </el-table-column>
        <el-table-column prop="udid" label="UDID" min-width="200">
          <template #default="{ row }">
            <span class="udid-text">{{ row.udid }}</span>
            <el-button text size="small" @click="copyUdid(row.udid)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              link 
              size="small" 
              :disabled="row.status !== 'online'"
              @click="openMirror(row)"
            >投屏</el-button>
            <el-button 
              type="success" 
              link 
              size="small" 
              :disabled="row.status !== 'online'"
              @click="runTest(row)"
            >执行</el-button>
            <el-dropdown trigger="click">
              <el-button type="primary" link size="small">...</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="viewDetail(row)">详情</el-dropdown-item>
                  <el-dropdown-item @click="installApp(row)">安装应用</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh, CopyDocument } from '@element-plus/icons-vue'
import { deviceApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const searchKeyword = ref('')
const filterPlatform = ref('')
const filterStatus = ref('')

const devices = ref([])

const onlineCount = computed(() => devices.value.filter(d => d.status === 'online').length)
const offlineCount = computed(() => devices.value.filter(d => d.status === 'offline').length)
const busyCount = computed(() => devices.value.filter(d => d.status === 'busy').length)

const filteredDevices = computed(() => {
  return devices.value.filter(device => {
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      if (!device.name?.toLowerCase().includes(keyword) && 
          !device.udid?.toLowerCase().includes(keyword)) {
        return false
      }
    }
    if (filterPlatform.value && device.platform !== filterPlatform.value) {
      return false
    }
    if (filterStatus.value && device.status !== filterStatus.value) {
      return false
    }
    return true
  })
})

function getStatusText(status) {
  const map = {
    online: '在线',
    offline: '离线',
    busy: '使用中'
  }
  return map[status] || status
}

async function refreshDevices() {
  loading.value = true
  try {
    const res = await deviceApi.list()
    const androidDevices = (res.data.android || []).map(d => ({ ...d, platform: 'android', status: d.status === 'connected' ? 'online' : 'offline' }))
    const iosDevices = (res.data.ios || []).map(d => ({ ...d, platform: 'ios', status: d.status === 'connected' ? 'online' : 'offline' }))
    devices.value = [...androidDevices, ...iosDevices]
  } catch (e) {
    ElMessage.error('获取设备列表失败')
  } finally {
    loading.value = false
  }
}

function copyUdid(udid) {
  navigator.clipboard.writeText(udid)
  ElMessage.success('已复制')
}

function openMirror(device) {
  router.push({ path: '/mirror', query: { udid: device.udid } })
}

function runTest(device) {
  router.push({ path: '/app/scripts', query: { device: device.udid } })
}

function viewDetail(device) {
  ElMessage.info('查看设备详情')
}

function installApp(device) {
  ElMessage.info('安装应用')
}

onMounted(() => {
  refreshDevices()
})
</script>

<style lang="scss" scoped>
.devices-page {
  height: calc(100vh - var(--header-height) - 32px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 4px;
  padding: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  h2 {
    font-size: 16px;
    font-weight: 500;
    margin: 0;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.stats-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
  }
  
  .stat-value {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-color);
  }
  
  &.online .stat-value {
    color: var(--success-color);
  }
  
  &.offline .stat-value {
    color: var(--text-muted);
  }
  
  &.busy .stat-value {
    color: var(--primary-color);
  }
}

.devices-table {
  flex: 1;
  overflow: auto;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 6px;
  
  .android-icon {
    color: #3ddc84;
    font-size: 16px;
    
    svg { width: 16px; height: 16px; }
  }
  
  .ios-icon {
    color: #666;
    font-size: 16px;
    
    svg { width: 16px; height: 16px; }
  }
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  
  &.online { background: var(--success-color); }
  &.offline { background: #d9d9d9; }
  &.busy { background: var(--primary-color); }
}

.udid-text {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>






