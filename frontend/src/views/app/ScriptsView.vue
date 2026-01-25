<template>
  <div class="scripts-page">
    <!-- 子导航 -->
    <div class="sub-nav">
      <span 
        class="sub-nav-item" 
        :class="{ active: subNav === 'scripts' }"
        @click="subNav = 'scripts'"
      >脚本管理</span>
      <span 
        class="sub-nav-item" 
        :class="{ active: subNav === 'tasks' }"
        @click="goToTasks"
      >任务管理</span>
    </div>
    
    <div class="page-content">
      <!-- 左侧目录 -->
      <div class="tree-panel">
        <el-input 
          v-model="treeSearch" 
          placeholder="搜索目录"
          :prefix-icon="Search"
          clearable
          size="small"
        />
        <el-tree
          :data="treeData"
          :props="{ label: 'name', children: 'children' }"
          node-key="id"
          default-expand-all
          highlight-current
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span>{{ node.label }}</span>
              <span class="count">{{ data.count }}</span>
            </span>
          </template>
        </el-tree>
      </div>
      
      <!-- 右侧列表 -->
      <div class="list-panel">
        <!-- 筛选 -->
        <div class="filter-bar">
          <el-input v-model="filters.name" placeholder="脚本名称" clearable style="width: 160px;" />
          <el-select v-model="filters.status" placeholder="状态" clearable style="width: 100px;">
            <el-option label="全部" value="" />
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <div class="filter-right">
            <el-button type="primary" @click="createScript">新建脚本</el-button>
          </div>
        </div>
        
        <!-- 表格 -->
        <el-table :data="scripts" border size="small" v-loading="loading">
          <el-table-column type="selection" width="40" />
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="脚本名称" min-width="180">
            <template #default="{ row }">
              <el-link type="primary" @click="editScript(row)">{{ row.name }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="platform" label="平台" width="80" />
          <el-table-column prop="updater" label="更新人" width="90" />
          <el-table-column prop="updateTime" label="更新时间" width="160" />
          <el-table-column prop="status" label="状态" width="70">
            <template #default="{ row }">
              <span :class="['status', row.status]">{{ row.status === 'enabled' ? '启用' : '禁用' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="editScript(row)">编辑</el-button>
              <el-button type="primary" link size="small" @click="runScript(row)">执行</el-button>
              <el-button type="danger" link size="small" @click="deleteScript(row)">删除</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const subNav = ref('scripts')
const treeSearch = ref('')
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(56)

const filters = reactive({ name: '', status: '' })

const treeData = ref([
  { id: '1', name: '全部脚本', count: 56, children: [
    { id: '2', name: '登录模块', count: 12 },
    { id: '3', name: '支付模块', count: 18 },
    { id: '4', name: '个人中心', count: 8 },
    { id: '5', name: '回收站', count: 3 }
  ]}
])

const scripts = ref([
  { id: 1001, name: '用户登录流程', platform: 'Android', updater: '张三', updateTime: '2026-01-17 10:30', status: 'enabled' },
  { id: 1002, name: '微信支付', platform: 'iOS', updater: '李四', updateTime: '2026-01-16 15:20', status: 'enabled' },
  { id: 1003, name: '余额查询', platform: 'Android', updater: '张三', updateTime: '2026-01-15 09:10', status: 'enabled' },
  { id: 1004, name: '转账功能', platform: 'Android', updater: '王五', updateTime: '2026-01-14 14:45', status: 'disabled' },
  { id: 1005, name: '个人信息修改', platform: 'iOS', updater: '李四', updateTime: '2026-01-13 11:30', status: 'enabled' },
])

function goToTasks() {
  router.push('/app/tasks')
}

function handleNodeClick(data) {
  handleSearch()
}

function handleSearch() {
  loading.value = true
  setTimeout(() => { loading.value = false }, 200)
}

function handleReset() {
  filters.name = ''
  filters.status = ''
}

function createScript() {
  router.push('/ui/scripts/new')
}

function editScript(row) {
  router.push(`/ui/scripts/${row.id}/edit`)
}

function runScript(row) {
  ElMessage.success(`开始执行: ${row.name}`)
}

function deleteScript(row) {
  ElMessageBox.confirm(`确定删除「${row.name}」？`, '提示', { type: 'warning' })
    .then(() => ElMessage.success('删除成功'))
    .catch(() => {})
}
</script>

<style lang="scss" scoped>
.scripts-page {
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
  display: flex;
  height: calc(100vh - 180px);
}

.tree-panel {
  width: 200px;
  border-right: 1px solid var(--border-color);
  padding: 12px;
  overflow: auto;
  
  .el-input { margin-bottom: 12px; }
  
  .tree-node {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 13px;
    
    .count { color: var(--text-muted); font-size: 12px; }
  }
}

.list-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  overflow: hidden;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  
  .filter-right { margin-left: auto; }
}

.el-table { flex: 1; }

.status {
  &.enabled { color: var(--success-color); }
  &.disabled { color: var(--text-muted); }
}

.pagination {
  padding-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
