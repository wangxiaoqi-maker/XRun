<template>
  <el-drawer 
    v-model="visible" 
    title="执行用例" 
    direction="rtl" 
    size="500px"
    :close-on-click-modal="false"
  >
    <!-- 执行配置 -->
    <div v-if="!executing && !executionId" class="execution-config">
      <el-form label-width="80px">
        <el-form-item label="选择设备" required>
          <el-select v-model="deviceId" placeholder="选择设备" :loading="loadingDevices" style="width: 100%">
            <el-option-group v-if="platform === 'android'" label="Android 设备">
              <el-option 
                v-for="d in androidDevices" 
                :key="d.udid" 
                :value="d.udid" 
                :label="d.model || d.udid"
              >
                <div class="device-option">
                  <span>{{ d.model || d.udid }}</span>
                  <el-tag size="small" :type="d.status === 'idle' ? 'success' : 'info'">
                    {{ d.status }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
            <el-option-group v-if="platform === 'ios'" label="iOS 设备">
              <el-option 
                v-for="d in iosDevices" 
                :key="d.udid" 
                :value="d.udid" 
                :label="d.name || d.udid"
              >
                <div class="device-option">
                  <span>{{ d.name || d.udid }}</span>
                  <el-tag size="small" :type="d.wda_running ? 'success' : 'warning'">
                    {{ d.wda_running ? 'WDA 运行中' : 'WDA 未启动' }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>

        <el-form-item label="变量覆盖">
          <div v-for="(v, k) in variables" :key="k" class="var-item">
            <span class="var-name">{{ k }}</span>
            <el-input v-model="variables[k]" size="small" style="flex: 1" />
          </div>
          <el-empty v-if="!Object.keys(variables).length" description="无变量" :image-size="40" />
        </el-form-item>
      </el-form>

      <div class="action-buttons">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="startExecution" :loading="starting" :disabled="!deviceId">
          开始执行
        </el-button>
      </div>
    </div>

    <!-- 执行中 / 结果 -->
    <div v-else class="execution-result">
      <!-- 状态 -->
      <div class="status-header">
        <div class="status-info">
          <el-icon :class="statusIconClass" :size="24">
            <component :is="statusIcon" />
          </el-icon>
          <span class="status-text">{{ statusText }}</span>
        </div>
        <div class="status-meta" v-if="executionData">
          <span v-if="executionData.duration_ms">
            耗时: {{ (executionData.duration_ms / 1000).toFixed(1) }}s
          </span>
        </div>
      </div>

      <!-- 步骤统计 -->
      <div class="steps-stats" v-if="executionData">
        <el-progress 
          :percentage="passRate" 
          :status="executionData.status === 'passed' ? 'success' : (executionData.status === 'failed' ? 'exception' : '')"
        />
        <div class="stats-detail">
          <span class="stat passed">通过: {{ executionData.passed_steps || 0 }}</span>
          <span class="stat failed">失败: {{ executionData.failed_steps || 0 }}</span>
          <span class="stat skipped">跳过: {{ executionData.skipped_steps || 0 }}</span>
        </div>
      </div>

      <!-- 实时日志 -->
      <div class="logs-section">
        <div class="logs-header">
          <span>执行日志</span>
          <el-button text size="small" @click="clearLogs">清空</el-button>
        </div>
        <div class="logs-content" ref="logsContainer">
          <div v-for="(log, i) in logs" :key="i" class="log-line" :class="getLogClass(log)">
            {{ log }}
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button v-if="isRunning" type="danger" @click="cancelExecution">
          取消执行
        </el-button>
        <el-button v-if="executionData?.report_url" type="primary" @click="viewReport">
          查看报告
        </el-button>
        <el-button v-if="!isRunning" @click="resetExecution">
          重新执行
        </el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Check, Close, Warning, Clock } from '@element-plus/icons-vue'
import { deviceApi, executionV2Api } from '@/api'

const props = defineProps({
  modelValue: Boolean,
  caseId: String,
  caseName: String,
  platform: {
    type: String,
    default: 'android'
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 状态
const loadingDevices = ref(false)
const starting = ref(false)
const executing = ref(false)
const executionId = ref(null)
const executionData = ref(null)
const logs = ref([])
const logsContainer = ref(null)

// 设备
const deviceId = ref('')
const androidDevices = ref([])
const iosDevices = ref([])
const variables = ref({})

// WebSocket
let ws = null

// 计算属性
const isRunning = computed(() => {
  const status = executionData.value?.status
  return status === 'pending' || status === 'compiling' || status === 'running'
})

const passRate = computed(() => {
  const data = executionData.value
  if (!data?.total_steps) return 0
  return Math.round((data.passed_steps || 0) / data.total_steps * 100)
})

const statusIcon = computed(() => {
  const status = executionData.value?.status
  if (!status || status === 'pending' || status === 'compiling' || status === 'running') return Loading
  if (status === 'passed') return Check
  if (status === 'failed') return Close
  if (status === 'cancelled') return Warning
  if (status === 'timeout') return Clock
  return Loading
})

const statusIconClass = computed(() => {
  const status = executionData.value?.status
  if (status === 'passed') return 'status-success'
  if (status === 'failed') return 'status-error'
  if (status === 'cancelled' || status === 'timeout') return 'status-warning'
  return 'status-running'
})

const statusText = computed(() => {
  const status = executionData.value?.status
  const map = {
    pending: '等待中...',
    compiling: '编译中...',
    running: '执行中...',
    passed: '执行通过',
    failed: '执行失败',
    cancelled: '已取消',
    timeout: '执行超时'
  }
  return map[status] || '准备执行'
})

// 加载设备
const loadDevices = async () => {
  loadingDevices.value = true
  try {
    if (props.platform === 'android') {
      const res = await deviceApi.listAndroid()
      androidDevices.value = res.data || []
    } else {
      const res = await deviceApi.listIOSNative()
      iosDevices.value = res.data || []
    }
  } catch (e) {
    console.error('Failed to load devices', e)
  } finally {
    loadingDevices.value = false
  }
}

// 开始执行
const startExecution = async () => {
  if (!props.caseId) {
    ElMessage.warning('用例未保存')
    return
  }
  if (!deviceId.value) {
    ElMessage.warning('请选择设备')
    return
  }

  starting.value = true
  try {
    const res = await executionV2Api.run({
      caseId: props.caseId,
      deviceId: deviceId.value,
      variables: Object.keys(variables.value).length ? variables.value : null
    })
    
    executionId.value = res.data.execution_id
    executing.value = true
    executionData.value = { status: 'pending' }
    
    // 连接 WebSocket
    connectWebSocket(res.data.execution_id)
    
  } catch (e) {
    ElMessage.error('启动执行失败：' + (e.response?.data?.detail || e.message))
  } finally {
    starting.value = false
  }
}

// WebSocket 连接
const connectWebSocket = (execId) => {
  if (ws) {
    ws.close()
  }
  
  ws = executionV2Api.connectLogs(execId)
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      
      if (data.type === 'log') {
        logs.value.push(data.message)
        scrollToBottom()
      } else if (data.type === 'status') {
        executionData.value = data.data
      } else if (data.type === 'end') {
        // 执行结束，获取最终状态
        fetchExecutionStatus()
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message', e)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error', error)
    ElMessage.error('日志连接失败')
  }
  
  ws.onclose = () => {
    console.log('WebSocket closed')
  }
}

// 获取执行状态
const fetchExecutionStatus = async () => {
  if (!executionId.value) return
  
  try {
    const res = await executionV2Api.get(executionId.value)
    executionData.value = res.data
  } catch (e) {
    console.error('Failed to fetch status', e)
  }
}

// 取消执行
const cancelExecution = async () => {
  if (!executionId.value) return
  
  try {
    await executionV2Api.cancel(executionId.value)
    ElMessage.success('已取消执行')
  } catch (e) {
    ElMessage.error('取消失败')
  }
}

// 重置
const resetExecution = () => {
  executionId.value = null
  executionData.value = null
  logs.value = []
  executing.value = false
  if (ws) {
    ws.close()
    ws = null
  }
}

// 查看报告
const viewReport = () => {
  if (executionData.value?.report_url) {
    window.open(executionData.value.report_url, '_blank')
  }
}

// 清空日志
const clearLogs = () => {
  logs.value = []
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
}

// 日志样式
const getLogClass = (log) => {
  if (log.includes('[Error]') || log.includes('failed')) return 'log-error'
  if (log.includes('[Warning]')) return 'log-warning'
  if (log.includes('[Compiler]')) return 'log-compiler'
  if (log.includes('[Runner]')) return 'log-runner'
  return ''
}

// 监听显示状态
watch(visible, (val) => {
  if (val) {
    loadDevices()
  } else {
    if (ws) {
      ws.close()
      ws = null
    }
  }
})

// 清理
onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style lang="scss" scoped>
.execution-config {
  padding: 16px;
  
  .var-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    
    .var-name {
      width: 100px;
      color: #606266;
    }
  }
}

.execution-result {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  .status-info {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .status-text {
      font-size: 16px;
      font-weight: 500;
    }
  }
  
  .status-meta {
    color: #909399;
    font-size: 13px;
  }
}

.status-running {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.status-success {
  color: #67c23a;
}

.status-error {
  color: #f56c6c;
}

.status-warning {
  color: #e6a23c;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.steps-stats {
  margin-bottom: 16px;
  
  .stats-detail {
    display: flex;
    gap: 16px;
    margin-top: 8px;
    
    .stat {
      font-size: 13px;
      
      &.passed { color: #67c23a; }
      &.failed { color: #f56c6c; }
      &.skipped { color: #909399; }
    }
  }
}

.logs-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  
  .logs-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .logs-content {
    flex: 1;
    overflow: auto;
    background: #1e1e1e;
    border-radius: 4px;
    padding: 12px;
    font-family: 'Fira Code', monospace;
    font-size: 12px;
    line-height: 1.8;
    
    .log-line {
      color: #d4d4d4;
      white-space: pre-wrap;
      word-break: break-all;
      
      &.log-error { color: #f56c6c; }
      &.log-warning { color: #e6a23c; }
      &.log-compiler { color: #67c23a; }
      &.log-runner { color: #409eff; }
    }
  }
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}

.device-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>
