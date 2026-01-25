<template>
  <div class="executions-page">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h1>执行记录</h1>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px;"
          @change="handleSearch"
        />
        <el-select v-model="filterStatus" placeholder="状态" style="width: 120px;" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="通过" value="passed" />
          <el-option label="失败" value="failed" />
          <el-option label="运行中" value="running" />
        </el-select>
        <el-button @click="refreshExecutions" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon total">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总执行数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.passed }}</div>
          <div class="stat-label">通过</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon danger">
          <el-icon><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.failed }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon warning">
          <el-icon><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.running }}</div>
          <div class="stat-label">运行中</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon info">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.passRate }}%</div>
          <div class="stat-label">通过率</div>
        </div>
      </div>
    </div>
    
    <!-- 执行记录列表 -->
    <div class="executions-table">
      <el-table 
        :data="executions" 
        style="width: 100%"
        v-loading="loading"
        row-key="id"
      >
        <el-table-column prop="id" label="执行ID" width="120">
          <template #default="{ row }">
            <span class="execution-id" @click="viewReport(row)">{{ row.id }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="caseName" label="用例名称" min-width="200">
          <template #default="{ row }">
            <div class="case-name">
              <span>{{ row.caseName }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="device" label="执行设备" width="150">
          <template #default="{ row }">
            <div class="device-info">
              <el-icon v-if="row.platform === 'android'" class="android">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.6 9.48l1.84-3.18c.16-.31.04-.69-.26-.85a.637.637 0 0 0-.83.22l-1.88 3.24a11.463 11.463 0 0 0-8.94 0L5.65 5.67a.643.643 0 0 0-.87-.2c-.28.18-.37.54-.22.83L6.4 9.48A10.78 10.78 0 0 0 1 18h22a10.78 10.78 0 0 0-5.4-8.52z"/></svg>
              </el-icon>
              <el-icon v-else class="ios">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
              </el-icon>
              <span>{{ row.device }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="default">
              <el-icon v-if="row.status === 'running'" class="is-loading"><Loading /></el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="progress" label="进度" width="180">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress 
                :percentage="row.progress" 
                :status="row.status === 'failed' ? 'exception' : row.status === 'passed' ? 'success' : ''"
                :stroke-width="8"
              />
              <span class="progress-text">{{ row.passedSteps }}/{{ row.totalSteps }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.duration || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="executor" label="执行人" width="100" />
        
        <el-table-column prop="startTime" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.startTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewReport(row)">
              查看报告
            </el-button>
            <el-button 
              v-if="row.status === 'running'"
              type="danger" 
              link 
              size="small" 
              @click="stopExecution(row)"
            >
              停止
            </el-button>
            <el-button 
              v-else
              type="success" 
              link 
              size="small" 
              @click="rerunExecution(row)"
            >
              重跑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Refresh, Document, CircleCheck, CircleClose, Loading, TrendCharts
} from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const dateRange = ref([])
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 统计数据
const stats = reactive({
  total: 156,
  passed: 142,
  failed: 12,
  running: 2,
  passRate: 91.0
})

// 执行记录
const executions = ref([
  {
    id: 'E20260117001',
    caseName: '登录功能测试',
    platform: 'android',
    device: 'OnePlus NE2210',
    status: 'passed',
    progress: 100,
    passedSteps: 8,
    totalSteps: 8,
    duration: '2m 15s',
    executor: 'QA',
    startTime: '2026-01-17T10:30:00'
  },
  {
    id: 'E20260117002',
    caseName: '用户注册流程',
    platform: 'android',
    device: 'OnePlus NE2210',
    status: 'running',
    progress: 60,
    passedSteps: 6,
    totalSteps: 10,
    duration: null,
    executor: 'QA',
    startTime: '2026-01-17T10:45:00'
  },
  {
    id: 'E20260117003',
    caseName: '商品搜索功能',
    platform: 'ios',
    device: 'iPhone 15 Pro',
    status: 'failed',
    progress: 75,
    passedSteps: 6,
    totalSteps: 8,
    duration: '3m 20s',
    executor: 'QA',
    startTime: '2026-01-17T09:15:00'
  },
  {
    id: 'E20260117004',
    caseName: '支付流程测试',
    platform: 'android',
    device: 'OnePlus NE2210',
    status: 'passed',
    progress: 100,
    passedSteps: 12,
    totalSteps: 12,
    duration: '5m 30s',
    executor: 'QA',
    startTime: '2026-01-17T08:00:00'
  },
  {
    id: 'E20260116001',
    caseName: '个人中心测试',
    platform: 'android',
    device: 'OnePlus NE2210',
    status: 'passed',
    progress: 100,
    passedSteps: 5,
    totalSteps: 5,
    duration: '1m 45s',
    executor: 'QA',
    startTime: '2026-01-16T16:30:00'
  }
])

let refreshTimer = null

function getStatusType(status) {
  const map = {
    passed: 'success',
    failed: 'danger',
    running: 'primary',
    pending: 'info'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    passed: '通过',
    failed: '失败',
    running: '运行中',
    pending: '待执行'
  }
  return map[status] || status
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

function handleSearch() {
  loadExecutions()
}

async function loadExecutions() {
  loading.value = true
  try {
    // TODO: 调用 API 加载数据
    await new Promise(resolve => setTimeout(resolve, 500))
    total.value = executions.value.length
  } catch (e) {
    ElMessage.error('加载执行记录失败')
  } finally {
    loading.value = false
  }
}

function refreshExecutions() {
  loadExecutions()
}

function viewReport(row) {
  router.push(`/ui/report/${row.id}`)
}

function stopExecution(row) {
  ElMessage.warning('正在停止执行...')
  // TODO: 调用停止 API
}

function rerunExecution(row) {
  ElMessage.info('功能开发中')
}

onMounted(() => {
  loadExecutions()
  
  // 定时刷新运行中的任务
  refreshTimer = setInterval(() => {
    const hasRunning = executions.value.some(e => e.status === 'running')
    if (hasRunning) {
      loadExecutions()
    }
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.executions-page {
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    
    &.total {
      background: rgba(24, 144, 255, 0.1);
      color: var(--primary-color);
    }
    
    &.success {
      background: rgba(82, 196, 26, 0.1);
      color: var(--success-color);
    }
    
    &.danger {
      background: rgba(255, 77, 79, 0.1);
      color: var(--danger-color);
    }
    
    &.warning {
      background: rgba(250, 173, 20, 0.1);
      color: var(--warning-color);
    }
    
    &.info {
      background: rgba(102, 126, 234, 0.1);
      color: #667eea;
    }
  }
  
  .stat-content {
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: var(--text-primary);
    }
    
    .stat-label {
      font-size: 14px;
      color: var(--text-muted);
    }
  }
}

.executions-table {
  flex: 1;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.execution-id {
  color: var(--primary-color);
  cursor: pointer;
  font-family: monospace;
  
  &:hover {
    text-decoration: underline;
  }
}

.case-name {
  color: var(--text-primary);
}

.device-info {
  display: flex;
  align-items: center;
  gap: 6px;
  
  .el-icon {
    font-size: 16px;
    
    svg {
      width: 16px;
      height: 16px;
    }
    
    &.android {
      color: #3ddc84;
    }
    
    &.ios {
      color: #999;
    }
  }
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .el-progress {
    flex: 1;
  }
  
  .progress-text {
    font-size: 12px;
    color: var(--text-muted);
    white-space: nowrap;
  }
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>






