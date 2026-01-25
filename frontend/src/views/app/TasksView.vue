<template>
  <div class="tasks-page">
    <!-- 子导航 -->
    <div class="sub-nav">
      <span class="sub-nav-item" @click="goToScripts">脚本管理</span>
      <span class="sub-nav-item active">任务管理</span>
    </div>
    
    <div class="page-content">
      <!-- 筛选 -->
      <div class="filter-bar">
        <el-input v-model="filters.name" placeholder="任务名称" clearable style="width: 160px;" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 100px;">
          <el-option label="全部" value="" />
          <el-option label="已完成" value="done" />
          <el-option label="执行中" value="running" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-date-picker v-model="filters.date" type="daterange" start-placeholder="开始" end-placeholder="结束" style="width: 220px;" />
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
        <div class="filter-right">
          <el-button type="primary" @click="createTask">新建任务</el-button>
        </div>
      </div>
      
      <!-- 表格 -->
      <el-table :data="tasks" border size="small" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="任务名称" min-width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="viewReport(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行进度" width="180">
          <template #default="{ row }">
            <div class="progress-wrapper">
              <el-progress :percentage="row.progress" :stroke-width="6" :show-text="false" />
              <span class="progress-text">
                <span class="pass">{{ row.passed }}</span> / 
                <span class="fail">{{ row.failed }}</span> / 
                <span class="total">{{ row.total }}</span>
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="creator" label="创建人" width="80" />
        <el-table-column prop="createTime" label="创建时间" width="150" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewReport(row)">报告</el-button>
            <el-button v-if="row.status === 'running'" type="warning" link size="small" @click="stopTask(row)">终止</el-button>
            <el-button v-else type="success" link size="small" @click="rerunTask(row)">重跑</el-button>
            <el-button type="danger" link size="small" @click="deleteTask(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          small
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(45)

const filters = reactive({ name: '', status: '', date: [] })

const tasks = ref([
  { id: 101, name: '登录模块回归测试', duration: '12分30秒', status: 'done', progress: 100, passed: 15, failed: 0, total: 15, creator: '张三', createTime: '2026-01-17 09:00' },
  { id: 102, name: '支付流程测试', duration: '8分45秒', status: 'done', progress: 100, passed: 10, failed: 2, total: 12, creator: '李四', createTime: '2026-01-16 14:30' },
  { id: 103, name: '日常冒烟测试', duration: '-', status: 'running', progress: 60, passed: 6, failed: 1, total: 10, creator: '张三', createTime: '2026-01-17 11:00' },
  { id: 104, name: '版本发布验证', duration: '25分10秒', status: 'done', progress: 100, passed: 28, failed: 5, total: 33, creator: '王五', createTime: '2026-01-15 16:20' },
  { id: 105, name: '性能压测', duration: '5分20秒', status: 'failed', progress: 30, passed: 3, failed: 7, total: 10, creator: '李四', createTime: '2026-01-14 10:15' },
])

function goToScripts() {
  router.push('/app/scripts')
}

function handleSearch() {
  loading.value = true
  setTimeout(() => { loading.value = false }, 200)
}

function handleReset() {
  filters.name = ''
  filters.status = ''
  filters.date = []
}

function getStatusType(status) {
  const map = { done: 'success', running: 'warning', failed: 'danger' }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = { done: '已完成', running: '执行中', failed: '失败' }
  return map[status] || status
}

function createTask() {
  ElMessage.info('创建任务')
}

function viewReport(row) {
  router.push(`/app/report/${row.id}`)
}

function stopTask(row) {
  ElMessage.success('任务已终止')
}

function rerunTask(row) {
  ElMessage.success('重新执行中...')
}

function deleteTask(row) {
  ElMessageBox.confirm(`确定删除「${row.name}」？`, '提示', { type: 'warning' })
    .then(() => ElMessage.success('删除成功'))
    .catch(() => {})
}
</script>

<style lang="scss" scoped>
.tasks-page {
  background: #fff;
  border-radius: 4px;
  min-height: calc(100vh - 132px);
}

.sub-nav {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: 0 16px;
}

.sub-nav-item {
  padding: 12px 20px;
  cursor: pointer;
  color: var(--text-secondary);
  position: relative;
  
  &:hover { color: var(--primary-color); }
  
  &.active {
    color: var(--primary-color);
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 20px;
      right: 20px;
      height: 2px;
      background: var(--primary-color);
    }
  }
}

.page-content {
  padding: 16px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  
  .filter-right { margin-left: auto; }
}

.progress-wrapper {
  .el-progress { margin-bottom: 4px; }
  
  .progress-text {
    font-size: 12px;
    .pass { color: var(--success-color); }
    .fail { color: var(--danger-color); }
    .total { color: var(--text-muted); }
  }
}

.pagination {
  padding-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
