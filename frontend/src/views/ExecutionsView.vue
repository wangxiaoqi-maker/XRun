<template>
  <div class="executions-view">
    <div class="page-header">
      <h1>执行记录</h1>
      <div class="header-actions">
        <el-button @click="loadExecutions" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>
    
    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filterStatus" placeholder="执行状态" clearable style="width: 140px;">
        <el-option value="pending" label="等待中" />
        <el-option value="running" label="执行中" />
        <el-option value="success" label="成功" />
        <el-option value="failed" label="失败" />
        <el-option value="error" label="错误" />
      </el-select>
      <el-button @click="loadExecutions">筛选</el-button>
    </div>
    
    <!-- 执行列表 -->
    <el-table 
      :data="executions" 
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column label="用例" min-width="180">
        <template #default="{ row }">
          <span>{{ getCaseName(row.case_id) }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="device_id" label="设备" width="180" />
      
      <el-table-column prop="platform" label="平台" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.platform === 'android' ? 'success' : ''">
            {{ row.platform === 'android' ? 'Android' : 'iOS' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="duration_ms" label="耗时" width="100">
        <template #default="{ row }">
          {{ formatDuration(row.duration_ms) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="created_at" label="开始时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">
            详情
          </el-button>
          <el-button 
            v-if="row.report_path" 
            size="small" 
            type="success"
            @click="viewReport(row)"
          >
            报告
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadExecutions"
        @current-change="loadExecutions"
      />
    </div>
    
    <!-- 详情弹窗 -->
    <el-dialog 
      v-model="detailVisible" 
      title="执行详情" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentExecution" class="execution-detail">
        <div class="detail-header">
          <div class="detail-info">
            <h3>{{ getCaseName(currentExecution.case_id) }}</h3>
            <el-tag :type="getStatusType(currentExecution.status)">
              {{ getStatusText(currentExecution.status) }}
            </el-tag>
          </div>
          <div class="detail-meta">
            <span>设备: {{ currentExecution.device_id }}</span>
            <span>耗时: {{ formatDuration(currentExecution.duration_ms) }}</span>
          </div>
        </div>
        
        <div v-if="currentExecution.error_message" class="error-message">
          <el-alert type="error" :closable="false">
            {{ currentExecution.error_message }}
          </el-alert>
        </div>
        
        <div class="log-container">
          <h4>执行日志</h4>
          <pre class="log-content" ref="logRef">{{ currentExecution.logs || '暂无日志' }}</pre>
        </div>
      </div>
    </el-dialog>
    
    <!-- 实时执行弹窗 -->
    <el-dialog 
      v-model="liveDialogVisible" 
      title="正在执行" 
      width="800px"
      :close-on-click-modal="false"
      @close="closeLiveDialog"
    >
      <div class="live-execution">
        <div class="live-header">
          <el-tag v-if="liveStatus" :type="getStatusType(liveStatus)">
            {{ getStatusText(liveStatus) }}
          </el-tag>
        </div>
        
        <div class="log-container">
          <pre class="log-content live-log" ref="liveLogRef">{{ liveLogs.join('\n') }}</pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { executionApi, caseApi } from '../api'

const loading = ref(false)
const executions = ref([])
const cases = ref({})
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const detailVisible = ref(false)
const currentExecution = ref(null)
const logRef = ref(null)

const liveDialogVisible = ref(false)
const liveStatus = ref('')
const liveLogs = ref([])
const liveLogRef = ref(null)
let liveWs = null

onMounted(() => {
  loadCases()
  loadExecutions()
})

async function loadCases() {
  try {
    const res = await caseApi.list()
    res.data.items.forEach(c => {
      cases.value[c.id] = c.name
    })
  } catch (e) {
    console.error(e)
  }
}

async function loadExecutions() {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    
    const res = await executionApi.list(params)
    executions.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

function getCaseName(caseId) {
  return cases.value[caseId] || caseId
}

function getStatusType(status) {
  const types = {
    'pending': 'info',
    'running': 'warning',
    'success': 'success',
    'failed': 'danger',
    'error': 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status) {
  const texts = {
    'pending': '等待中',
    'running': '执行中',
    'success': '成功',
    'failed': '失败',
    'error': '错误'
  }
  return texts[status] || status
}

function formatDuration(ms) {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function viewDetail(row) {
  try {
    const res = await executionApi.get(row.id)
    currentExecution.value = res.data
    detailVisible.value = true
    
    nextTick(() => {
      if (logRef.value) {
        logRef.value.scrollTop = logRef.value.scrollHeight
      }
    })
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

function viewReport(row) {
  if (row.report_path) {
    window.open(`/static/reports/${row.id}.html`, '_blank')
  }
}

// 开始实时执行监控
function startLiveMonitor(executionId) {
  liveDialogVisible.value = true
  liveLogs.value = []
  liveStatus.value = 'pending'
  
  liveWs = executionApi.connectLogs(executionId)
  
  liveWs.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.type === 'log') {
      liveLogs.value.push(data.data)
      nextTick(() => {
        if (liveLogRef.value) {
          liveLogRef.value.scrollTop = liveLogRef.value.scrollHeight
        }
      })
    } else if (data.type === 'status') {
      liveStatus.value = data.data
    } else if (data.type === 'finished') {
      ElMessage.success('执行完成')
      loadExecutions()
    }
  }
  
  liveWs.onerror = () => {
    ElMessage.error('连接中断')
  }
}

function closeLiveDialog() {
  if (liveWs) {
    liveWs.close()
    liveWs = null
  }
}

// 暴露给外部调用
defineExpose({
  startLiveMonitor
})
</script>

<style lang="scss" scoped>
.executions-view {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h1 {
    font-size: 24px;
    margin: 0;
    color: #fff;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.execution-detail {
  .detail-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    h3 {
      margin: 0 0 8px 0;
    }
    
    .detail-meta {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.6);
    }
  }
  
  .error-message {
    margin-bottom: 16px;
  }
}

.log-container {
  h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
  }
}

.log-content {
  background: #0f0f23;
  border-radius: 8px;
  padding: 16px;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #a3e635;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
  
  &.live-log {
    min-height: 300px;
  }
}

.live-execution {
  .live-header {
    margin-bottom: 16px;
  }
}
</style>
