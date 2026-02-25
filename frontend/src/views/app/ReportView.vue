<template>
  <div class="report-page">
    <!-- 报告头部 -->
    <div class="report-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="report-title">{{ reportData.name }}</span>
      </div>
      <div class="header-right">
        <el-button>导出报告</el-button>
        <el-button type="primary" @click="rerun">重新执行</el-button>
      </div>
    </div>
    
    <!-- 报告概要 -->
    <div class="report-summary">
      <div class="summary-item">
        <span class="label">执行状态</span>
        <el-tag :type="getStatusType(reportData.status)">{{ getStatusText(reportData.status) }}</el-tag>
      </div>
      <div class="summary-item">
        <span class="label">应用文件夹</span>
        <span class="value">{{ reportData.folder }}</span>
      </div>
      <div class="summary-item">
        <span class="label">执行耗时</span>
        <span class="value">{{ reportData.duration }}</span>
      </div>
      <div class="summary-item">
        <span class="label">创建人</span>
        <span class="value">{{ reportData.creator }}</span>
      </div>
      <div class="summary-item">
        <span class="label">开始时间</span>
        <span class="value">{{ reportData.startTime }}</span>
      </div>
      <div class="summary-item">
        <span class="label">结束时间</span>
        <span class="value">{{ reportData.endTime }}</span>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card total">
        <div class="stat-value">{{ reportData.total }}</div>
        <div class="stat-label">总用例数</div>
      </div>
      <div class="stat-card pass">
        <div class="stat-value">{{ reportData.passed }}</div>
        <div class="stat-label">通过</div>
      </div>
      <div class="stat-card fail">
        <div class="stat-value">{{ reportData.failed }}</div>
        <div class="stat-label">失败</div>
      </div>
      <div class="stat-card skip">
        <div class="stat-value">{{ reportData.skipped }}</div>
        <div class="stat-label">跳过</div>
      </div>
      <div class="stat-card rate">
        <div class="stat-value">{{ passRate }}%</div>
        <div class="stat-label">通过率</div>
      </div>
    </div>
    
    <!-- 执行详情表格 -->
    <div class="report-detail">
      <div class="detail-header">
        <span class="title">执行详情</span>
        <div class="filter-actions">
          <el-radio-group v-model="resultFilter" size="small">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="pass">通过</el-radio-button>
            <el-radio-button value="fail">失败</el-radio-button>
            <el-radio-button value="skip">跳过</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <el-table :data="filteredCases" border size="small">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="name" label="脚本名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="viewCaseDetail(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="device" label="执行设备" width="120" />
        <el-table-column prop="result" label="结果" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getResultType(row.result)">{{ getResultText(row.result) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" />
        <el-table-column prop="startTime" label="开始时间" width="160" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewCaseDetail(row)">详情</el-button>
            <el-button type="primary" link size="small" @click="viewScreenshot(row)">截图</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const resultFilter = ref('')

const reportData = ref({
  id: route.params.id,
  name: 'H5交互3.0demo-原生接口测试',
  folder: '翼支付app',
  status: 'completed',
  duration: '23分29秒',
  creator: '胡康康',
  startTime: '2026-01-17 05:00:00',
  endTime: '2026-01-17 05:23:29',
  total: 39,
  passed: 23,
  failed: 16,
  skipped: 0
})

const caseResults = ref([
  { id: 1, name: '获取用户信息接口', device: 'OPPO A5', result: 'pass', duration: '12s', startTime: '2026-01-17 05:00:05' },
  { id: 2, name: '分享到微信', device: 'OPPO A5', result: 'fail', duration: '45s', startTime: '2026-01-17 05:00:17', error: '元素未找到' },
  { id: 3, name: '扫码支付', device: 'OPPO A5', result: 'pass', duration: '30s', startTime: '2026-01-17 05:01:02' },
  { id: 4, name: '查询余额', device: 'OPPO A5', result: 'pass', duration: '8s', startTime: '2026-01-17 05:01:32' },
  { id: 5, name: '转账功能', device: 'OPPO A5', result: 'fail', duration: '1m 20s', startTime: '2026-01-17 05:01:40', error: '网络超时' },
  { id: 6, name: '消息推送', device: 'OPPO A5', result: 'pass', duration: '15s', startTime: '2026-01-17 05:03:00' },
  { id: 7, name: '充值话费', device: 'OPPO A5', result: 'pass', duration: '25s', startTime: '2026-01-17 05:03:15' },
  { id: 8, name: '信用卡还款', device: 'OPPO A5', result: 'fail', duration: '58s', startTime: '2026-01-17 05:03:40', error: '断言失败' },
])

const passRate = computed(() => {
  if (!reportData.value.total) return 0
  return Math.round(reportData.value.passed / reportData.value.total * 100)
})

const filteredCases = computed(() => {
  if (!resultFilter.value) return caseResults.value
  return caseResults.value.filter(c => c.result === resultFilter.value)
})

function getStatusType(status) {
  const map = { completed: 'success', running: 'warning', cancelled: 'info' }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = { completed: '已完成', running: '执行中', cancelled: '已取消' }
  return map[status] || status
}

function getResultType(result) {
  const map = { pass: 'success', fail: 'danger', skip: 'info' }
  return map[result] || 'info'
}

function getResultText(result) {
  const map = { pass: '通过', fail: '失败', skip: '跳过' }
  return map[result] || result
}

function goBack() {
  router.push('/app/tasks')
}

function rerun() {
  ElMessage.info('重新执行任务...')
}

function viewCaseDetail(row) {
  ElMessage.info(`查看用例详情: ${row.name}`)
}

function viewScreenshot(row) {
  ElMessage.info(`查看截图: ${row.name}`)
}
</script>

<style lang="scss" scoped>
.report-page {
  min-height: calc(100vh - var(--header-height) - 32px);
  background: #fff;
  border-radius: 4px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .report-title {
    font-size: 16px;
    font-weight: 500;
  }
  
  .header-right {
    display: flex;
    gap: 8px;
  }
}

.report-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid var(--border-color);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .label {
    color: var(--text-secondary);
    font-size: 13px;
  }
  
  .value {
    color: var(--text-color);
    font-size: 13px;
  }
}

.stats-cards {
  display: flex;
  gap: 16px;
  padding: 16px;
}

.stat-card {
  flex: 1;
  padding: 16px;
  text-align: center;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  
  .stat-value {
    font-size: 28px;
    font-weight: 600;
    line-height: 1.2;
  }
  
  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
  }
  
  &.total .stat-value { color: var(--text-color); }
  &.pass .stat-value { color: var(--success-color); }
  &.fail .stat-value { color: var(--danger-color); }
  &.skip .stat-value { color: var(--text-muted); }
  &.rate .stat-value { color: var(--primary-color); }
}

.report-detail {
  padding: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  
  .title {
    font-size: 15px;
    font-weight: 500;
  }
}
</style>






