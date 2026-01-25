<template>
  <div class="page-container">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button @click="loadDevices" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新设备
      </el-button>
    </div>
    
    <el-row :gutter="20">
      <!-- Android 设备 -->
      <el-col :span="12">
        <div class="device-section">
          <div class="section-header">
            <el-tag class="platform-tag android" size="large">Android</el-tag>
            <span class="device-count">{{ devices.android.length }} 台设备</span>
          </div>
          
          <div v-if="devices.android.length === 0" class="empty-devices">
            <el-icon :size="40"><Iphone /></el-icon>
            <p>未检测到 Android 设备</p>
            <p class="tip">请确保设备已连接并开启 USB 调试</p>
          </div>
          
          <div v-else class="device-list">
            <div 
              v-for="device in devices.android" 
              :key="device.id"
              class="device-card"
            >
              <div class="device-icon">
                <el-icon :size="32"><Iphone /></el-icon>
              </div>
              <div class="device-info">
                <div class="device-name">{{ device.name || device.model }}</div>
                <div class="device-meta">
                  <span>ID: {{ device.id }}</span>
                  <span v-if="device.os_version">Android {{ device.os_version }}</span>
                  <span v-if="device.resolution">{{ device.resolution }}</span>
                </div>
              </div>
              <div class="device-status">
                <el-tag type="success" size="small">已连接</el-tag>
              </div>
              <div class="device-actions">
                <el-button size="small" @click="takeScreenshot(device, 'android')">
                  <el-icon><Camera /></el-icon>
                  截图
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      
      <!-- iOS 设备 -->
      <el-col :span="12">
        <div class="device-section">
          <div class="section-header">
            <el-tag class="platform-tag ios" size="large">iOS</el-tag>
            <span class="device-count">{{ devices.ios.length }} 台设备</span>
          </div>
          
          <div v-if="devices.ios.length === 0" class="empty-devices">
            <el-icon :size="40"><Iphone /></el-icon>
            <p>未检测到 iOS 设备</p>
            <p class="tip">请确保设备已连接并信任此电脑</p>
          </div>
          
          <div v-else class="device-list">
            <div 
              v-for="device in devices.ios" 
              :key="device.id"
              class="device-card"
            >
              <div class="device-icon ios">
                <el-icon :size="32"><Iphone /></el-icon>
              </div>
              <div class="device-info">
                <div class="device-name">{{ device.name }}</div>
                <div class="device-meta">
                  <span>UDID: {{ device.id.substring(0, 8) }}...</span>
                  <span v-if="device.os_version">iOS {{ device.os_version }}</span>
                </div>
              </div>
              <div class="device-status">
                <el-tag type="success" size="small">已连接</el-tag>
              </div>
              <div class="device-actions">
                <el-button size="small" @click="takeScreenshot(device, 'ios')">
                  <el-icon><Camera /></el-icon>
                  截图
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 截图预览 -->
    <el-dialog v-model="screenshotDialogVisible" title="设备截图" width="400px">
      <div class="screenshot-preview">
        <img v-if="screenshotUrl" :src="screenshotUrl" />
        <div v-else class="loading">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>正在截图...</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Iphone, Camera, Loading } from '@element-plus/icons-vue'
import { deviceApi } from '../api'

const devices = ref({ android: [], ios: [] })
const loading = ref(false)

const screenshotDialogVisible = ref(false)
const screenshotUrl = ref('')

onMounted(() => {
  loadDevices()
})

async function loadDevices() {
  loading.value = true
  try {
    const res = await deviceApi.list()
    devices.value = res.data
  } catch (e) {
    ElMessage.error('加载设备失败')
  } finally {
    loading.value = false
  }
}

async function takeScreenshot(device, platform) {
  screenshotDialogVisible.value = true
  screenshotUrl.value = ''
  
  try {
    const res = await deviceApi.screenshot(device.id, platform)
    screenshotUrl.value = res.data.path
  } catch (e) {
    ElMessage.error('截图失败')
    screenshotDialogVisible.value = false
  }
}
</script>

<style lang="scss" scoped>
.page-container {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

.device-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: 300px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
  
  .device-count {
    color: #909399;
    font-size: 14px;
  }
}

.platform-tag {
  border-radius: 4px;
  
  &.android {
    background: #a4c639;
    border-color: #a4c639;
    color: white;
  }
  
  &.ios {
    background: #333;
    border-color: #333;
    color: white;
  }
}

.empty-devices {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  
  p {
    margin-top: 12px;
    
    &.tip {
      font-size: 12px;
    }
  }
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  
  .device-icon {
    width: 48px;
    height: 48px;
    background: #a4c639;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    
    &.ios {
      background: #333;
    }
  }
  
  .device-info {
    flex: 1;
    
    .device-name {
      font-size: 15px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
    }
    
    .device-meta {
      font-size: 12px;
      color: #909399;
      
      span {
        margin-right: 12px;
      }
    }
  }
}

.screenshot-preview {
  text-align: center;
  
  img {
    max-width: 100%;
    max-height: 500px;
    border-radius: 8px;
  }
  
  .loading {
    padding: 60px 0;
    color: #909399;
    
    p {
      margin-top: 12px;
    }
  }
}
</style>

