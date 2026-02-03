<template>
  <div class="script-manager">
    <!-- 左侧目录树 -->
    <aside class="sidebar-tree">
      <div class="sidebar-header">
        <div class="app-info">
          <div class="icon-box">⚡</div>
          <span class="app-name">{{ truncateText(currentProject?.name || '翼支付', 6) }} Pro</span>
        </div>
        <button class="add-btn" @click="addFolder">+</button>
      </div>
      
      <div class="tree-content">
        <div 
          v-for="node in visibleTreeNodes" 
          :key="node.id"
          class="tree-node"
          :class="{ active: activeNodeId === node.id }"
          :style="{ paddingLeft: (node.level * 16 + 12) + 'px' }"
          @click="handleNodeClick(node)"
        >
          <div 
            class="arrow-wrapper" 
            :class="{ expanded: node.expanded, hidden: !node.hasChildren }"
            @click.stop="toggleExpand(node)"
          >
            <el-icon><ArrowRight /></el-icon>
          </div>
          <el-icon class="folder-icon"><Folder /></el-icon>
          <span class="node-name">{{ node.name }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="trash-item" @click="selectTrash">
          <el-icon><Delete /></el-icon>
          回收站
        </div>
      </div>
    </aside>

    <!-- 右侧内容区 -->
    <main class="content-area">
      <!-- 头部 -->
      <header class="compact-header">
        <div class="header-meta">
          <div class="module-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="title-group">
            <h1 class="page-title">脚本管理</h1>
            <div class="breadcrumb-row">
              <span class="path" @click="selectAllScripts">全部脚本</span>
              <span class="sep">/</span>
              <span class="path active">{{ currentPathName }}</span>
            </div>
          </div>
        </div>
        
        <div class="header-actions">
          <div class="search-box">
            <el-icon class="search-icon"><Search /></el-icon>
            <input v-model="searchText" type="text" placeholder="搜索脚本...">
          </div>
          <button class="action-btn" @click="showFilter = !showFilter">
            <el-icon><Filter /></el-icon>
            筛选
          </button>
          <button class="primary-btn" @click="createScript">
            <span class="plus">+</span> 新建脚本
          </button>
        </div>
      </header>

      <!-- 表格卡片 -->
      <div class="table-card">
        <div class="table-content">
          <!-- 表头 -->
          <div class="t-row t-header">
            <div class="th col-name">脚本名称</div>
            <div class="th col-id">ID</div>
            <div class="th col-platform">平台</div>
            <div class="th col-author">负责人</div>
            <div class="th col-status">状态</div>
            <div class="th col-action">操作</div>
          </div>

          <!-- 表体 -->
          <div class="t-body">
            <div class="t-row" v-for="script in scripts" :key="script.id" @click="editScript(script)">
              <div class="td col-name">
                <div class="file-icon">TS</div>
                <div class="info">
                  <div class="name">{{ script.name }}</div>
                  <div class="desc">{{ script.description }}</div>
                </div>
              </div>
              <div class="td col-id">#{{ script.id }}</div>
              <div class="td col-platform">
                <span class="platform-badge" :class="script.platform.toLowerCase()">{{ script.platform }}</span>
              </div>
              <div class="td col-author">
                <img :src="script.authorAvatar" class="avatar" />
                <span>{{ script.author }}</span>
              </div>
              <div class="td col-status">
                <span class="status-pill" :class="script.status">{{ getStatusText(script.status) }}</span>
              </div>
              <div class="td col-action">
                <el-dropdown trigger="click" @command="handleCommand($event, script)">
                  <button class="more-icon" @click.stop>•••</button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="run">执行</el-dropdown-item>
                      <el-dropdown-item command="copy">复制</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div class="t-footer">
            <button class="nav-btn" @click="prevPage">Previous</button>
            <div class="page-nums">
              <span 
                v-for="p in totalPages" 
                :key="p" 
                class="num"
                :class="{ active: page === p }"
                @click="page = p"
              >{{ p }}</span>
            </div>
            <button class="nav-btn" @click="nextPage">Next</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Folder, ArrowRight, Delete, Document, Filter } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.currentProject)

const searchText = ref('')
const showFilter = ref(false)
const activeNodeId = ref('1-1')
const page = ref(1)
const pageSize = ref(10)
const total = ref(56)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 3)

// 目录树数据
const rawTreeData = ref([
  {
    id: '1', name: '全量回归测试', expanded: true, children: [
      { id: '1-1', name: '登录注册模块' },
      { id: '1-2', name: '支付收银台' }
    ]
  },
  {
    id: '2', name: '营销活动页', expanded: false, children: [
      { id: '2-1', name: '双11大促' },
      { id: '2-2', name: '元旦活动' }
    ]
  },
  { id: '3', name: '公共组件库', expanded: false },
  { id: '4', name: '个人中心', expanded: false }
])

// 展开的树节点
const visibleTreeNodes = computed(() => {
  const result = []
  const traverse = (nodes, level = 0) => {
    for (const node of nodes) {
      result.push({ ...node, level, hasChildren: node.children && node.children.length > 0 })
      if (node.children && node.expanded) traverse(node.children, level + 1)
    }
  }
  traverse(rawTreeData.value)
  return result
})

// 当前路径名
const currentPathName = computed(() => {
  const node = visibleTreeNodes.value.find(n => n.id === activeNodeId.value)
  return node ? node.name : '全部脚本'
})

// 脚本列表 Mock 数据
const scripts = ref([
  { id: '827364', name: 'Login_Flow_Main', description: 'Main login flow check', platform: 'Android', author: 'Felix', authorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix', status: 'active' },
  { id: '293847', name: 'Payment_Wechat', description: 'Check wechat pay sdk', platform: 'Backend', author: 'Ana', authorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ana', status: 'pending' },
  { id: '102938', name: 'Banner_Loop_Click', description: 'Verify banner auto scroll', platform: 'iOS', author: 'Bob', authorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob', status: 'failed' },
  { id: '556123', name: 'Settings_Logout', description: 'User logout action', platform: 'Web', author: 'Sarah', authorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah', status: 'active' },
  { id: '123456', name: 'Search_Function', description: 'Keyword search test', platform: 'Android', author: 'Mike', authorAvatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike', status: 'active' },
])

// 点击节点
function handleNodeClick(node) {
  activeNodeId.value = node.id
  if (node.hasChildren) {
    const original = rawTreeData.value.find(n => n.id === node.id) || 
      rawTreeData.value.flatMap(n => n.children || []).find(n => n.id === node.id)
    if (original) original.expanded = !original.expanded
  }
}

// 展开/折叠
function toggleExpand(node) {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.id === node.id) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(rawTreeData.value)
}

// 选择全部脚本
function selectAllScripts() {
  activeNodeId.value = ''
}

// 选择回收站
function selectTrash() {
  activeNodeId.value = 'trash'
}

// 新建文件夹
function addFolder() {
  ElMessageBox.prompt('请输入目录名称', '新建目录', {
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(({ value }) => {
    if (value) {
      rawTreeData.value.push({ id: Date.now().toString(), name: value, expanded: false })
      ElMessage.success('目录创建成功')
    }
  }).catch(() => {})
}

function truncateText(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

function getStatusText(status) {
  const map = { pending: 'Pending', active: 'Active', inactive: 'Inactive', failed: 'Failed' }
  return map[status] || status
}

function createScript() {
  router.push('/ui/scripts/new')
}

function editScript(script) {
  router.push(`/ui/scripts/${script.id}/edit`)
}

function handleCommand(cmd, script) {
  switch (cmd) {
    case 'edit': editScript(script); break
    case 'run': ElMessage.success(`开始执行: ${script.name}`); break
    case 'copy': ElMessage.success('脚本已复制'); break
    case 'delete':
      ElMessageBox.confirm(`确定删除「${script.name}」？`, '提示', { type: 'warning' })
        .then(() => ElMessage.success('删除成功'))
        .catch(() => {})
      break
  }
}

function prevPage() { if (page.value > 1) page.value-- }
function nextPage() { if (page.value < totalPages.value) page.value++ }
</script>

<style lang="scss" scoped>
/* 全局容器 */
.script-manager {
  display: flex;
  height: 100%;
  width: 100%;
  background: #f8fafc;
  padding: 20px;
  box-sizing: border-box;
  gap: 20px;
}

/* 左侧目录树 */
.sidebar-tree {
  width: 260px;
  background: white;
  border-radius: 16px;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.sidebar-header {
  padding: 0 20px 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 8px;
}

.app-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #0f172a;
  font-size: 15px;
}

.icon-box {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.add-btn {
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  
  &:hover {
    background: #f1f5f9;
    color: #3b82f6;
  }
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.tree-node {
  display: flex;
  align-items: center;
  height: 36px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  color: #334155;
  font-size: 14px;
  transition: all 0.15s;
  user-select: none;
  
  &:hover {
    background: #f8fafc;
    color: #0f172a;
  }
  
  &.active {
    background: #eff6ff;
    color: #3b82f6;
    font-weight: 600;
  }
}

.arrow-wrapper {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
  transition: transform 0.2s;
  margin-right: 2px;
  font-size: 12px;
  
  &.expanded {
    transform: rotate(90deg);
    color: #64748b;
  }
  
  &.hidden {
    visibility: hidden;
  }
  
  &:hover {
    color: #3b82f6;
  }
}

.folder-icon {
  margin-right: 8px;
  color: #60a5fa;
  font-size: 16px;
}

.node-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  padding: 12px 20px 0 20px;
  border-top: 1px solid #f1f5f9;
  margin-top: 8px;
}

.trash-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-size: 14px;
  cursor: pointer;
  
  &:hover {
    color: #ef4444;
  }
}

/* 右侧内容区 */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部 */
.compact-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
  padding: 0 4px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.module-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 10px -2px rgba(59, 130, 246, 0.4);
}

.title-group {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.page-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  line-height: 1.2;
}

.breadcrumb-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  
  .sep {
    color: #cbd5e1;
    font-size: 10px;
  }
  
  .path {
    cursor: pointer;
    &:hover { color: #3b82f6; }
    &.active { color: #3b82f6; font-weight: 500; }
  }
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-box {
  position: relative;
  
  input {
    padding: 8px 10px 8px 32px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    width: 180px;
    outline: none;
    font-size: 13px;
    background: white;
    transition: all 0.2s;
    
    &:focus {
      border-color: #3b82f6;
      width: 220px;
      box-shadow: 0 0 0 2px rgba(59,130,246,0.1);
    }
  }
  
  .search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
    font-size: 14px;
  }
}

.action-btn {
  height: 34px;
  padding: 0 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #475569;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  
  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
}

.primary-btn {
  height: 34px;
  padding: 0 16px;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  
  &:hover {
    background: #1e293b;
    transform: translateY(-1px);
  }
  
  .plus {
    font-size: 16px;
    font-weight: 400;
  }
}

/* 表格卡片 */
.table-card {
  flex: 1;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Grid 布局 */
.t-row {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1fr 1.5fr 1.2fr 60px;
  gap: 16px;
  padding: 0 24px;
  align-items: center;
}

/* 表头 */
.t-header {
  height: 48px;
  background: #fdfdfd;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.th {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 表体 */
.t-body {
  flex: 1;
  overflow-y: auto;
  
  .t-row {
    height: 72px;
    border-bottom: 1px solid #f8fafc;
    transition: background 0.15s;
    cursor: pointer;
    
    &:hover {
      background: #fcfcfc;
    }
  }
}

.col-action {
  text-align: right;
}

/* 脚本名称列 */
.col-name {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  width: 36px;
  height: 36px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  border: 1px solid #dbeafe;
  flex-shrink: 0;
}

.info {
  min-width: 0;
}

.name {
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}

.desc {
  font-size: 12px;
  color: #94a3b8;
}

.col-id {
  font-family: monospace;
  color: #64748b;
  font-size: 13px;
}

/* 平台标签 */
.platform-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
  display: inline-block;
  
  &.android { background: #dcfce7; color: #166534; }
  &.ios { background: #f1f5f9; color: #475569; }
  &.backend { background: #e0e7ff; color: #4338ca; }
  &.web { background: #ffedd5; color: #c2410c; }
}

/* 负责人列 */
.col-author {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #334155;
}

.avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

/* 状态标签 */
.status-pill {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  display: inline-block;
  
  &.active { background: #dcfce7; color: #15803d; }
  &.pending { background: #ffedd5; color: #c2410c; }
  &.failed { background: #fee2e2; color: #b91c1c; }
  &.inactive { background: #f3f4f6; color: #6b7280; }
}

.more-icon {
  background: transparent;
  border: none;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 16px;
  
  &:hover {
    color: #64748b;
  }
}

/* 分页 */
.t-footer {
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  border-top: 1px solid #f1f5f9;
  background: white;
  flex-shrink: 0;
}

.nav-btn {
  background: transparent;
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  
  &:hover {
    color: #3b82f6;
  }
}

.page-nums {
  display: flex;
  gap: 4px;
}

.num {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  
  &.active {
    background: #eff6ff;
    color: #3b82f6;
    font-weight: 600;
  }
  
  &:hover:not(.active) {
    background: #f8fafc;
  }
}
</style>
