<template>
  <div class="script-manager">
    <!-- 左侧目录树 -->
    <aside class="sidebar-tree">
      <div class="sidebar-header">
        <div class="app-info">
          <div class="icon-box">⚡</div>
          <span class="app-name">{{ truncateText(currentProject?.name || '项目', 8) }}</span>
        </div>
        <el-tooltip content="新建目录" placement="top">
          <button class="add-btn" @click="addFolder">+</button>
        </el-tooltip>
      </div>
      
      <div class="tree-content" v-loading="loadingTree">
        <!-- 全部脚本 -->
        <div 
          class="tree-node all-scripts"
          :class="{ active: !activeNodeId }"
          @click="selectAllScripts"
        >
          <el-icon class="folder-icon"><Document /></el-icon>
          <span class="node-name">全部脚本</span>
        </div>
        
        <!-- 动态目录 -->
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
          <span class="case-count" v-if="node.caseCount">{{ node.caseCount }}</span>
          <div class="node-actions" @click.stop>
            <el-dropdown trigger="click" size="small">
              <el-icon class="more-btn"><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="addSubFolder(node)">新建子目录</el-dropdown-item>
                  <el-dropdown-item @click="renameFolder(node)">重命名</el-dropdown-item>
                  <el-dropdown-item divided @click="deleteFolder(node)">
                    <span style="color: #ef4444;">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="!loadingTree && rawTreeData.length === 0" class="empty-tree">
          <p>暂无目录</p>
          <el-button size="small" @click="addFolder">创建目录</el-button>
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
          <div class="t-body" v-loading="loading">
            <template v-if="scripts.length > 0">
              <div class="t-row" v-for="script in scripts" :key="script.id" @click="editScript(script)">
                <div class="td col-name">
                  <div class="file-icon">TS</div>
                  <div class="info">
                    <div class="name">{{ script.name }}</div>
                    <div class="desc">{{ script.description || '暂无描述' }}</div>
                  </div>
                </div>
                <div class="td col-id">#{{ script.id?.slice(0, 8) }}</div>
                <div class="td col-platform">
                  <span class="platform-badge" :class="script.platform?.toLowerCase()">{{ script.platform || 'N/A' }}</span>
                </div>
                <div class="td col-author">
                  <img :src="getAuthorAvatar(script.createdBy)" class="avatar" />
                  <span>{{ script.createdBy || 'system' }}</span>
                </div>
                <div class="td col-status">
                  <span class="status-pill" :class="script.status?.toLowerCase()">{{ getStatusText(script.status) }}</span>
                </div>
                <div class="td col-action">
                  <el-dropdown trigger="click" @command="handleCommand($event, script)">
                    <button class="more-icon" @click.stop>•••</button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="edit">编辑</el-dropdown-item>
                        <el-dropdown-item command="run">执行</el-dropdown-item>
                        <el-dropdown-item command="viewScript">查看脚本</el-dropdown-item>
                        <el-dropdown-item command="copy">复制</el-dropdown-item>
                        <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>
            <div v-else class="empty-state">
              <el-icon :size="48" color="#cbd5e1"><Document /></el-icon>
              <p>暂无脚本</p>
              <el-button type="primary" @click="createScript">新建脚本</el-button>
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
    
    <!-- 查看 TS 脚本弹框 -->
    <el-dialog 
      v-model="showScriptDialog" 
      :title="`生成的 TypeScript 脚本 - ${currentScript?.name || ''}`"
      width="75%"
      top="5vh"
      class="script-preview-dialog"
    >
      <div class="script-preview-container" v-loading="compilingScript">
        <div class="preview-header">
          <div class="file-info">
            <el-icon><Document /></el-icon>
            <span class="filename">{{ scriptFileName }}</span>
          </div>
          <div class="preview-actions">
            <el-button size="small" @click="copyScript" :icon="CopyDocument">复制代码</el-button>
          </div>
        </div>
        <div class="code-wrapper">
          <pre class="code-content"><code>{{ scriptContent }}</code></pre>
        </div>
        <div v-if="compileWarnings.length" class="warnings">
          <el-alert type="warning" :closable="false">
            <template #title>编译警告</template>
            <ul>
              <li v-for="(w, i) in compileWarnings" :key="i">{{ w }}</li>
            </ul>
          </el-alert>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Folder, ArrowRight, Delete, Document, Filter, MoreFilled, CopyDocument } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { caseV2Api, suiteApi } from '@/api'

// 查看脚本弹框相关
const showScriptDialog = ref(false)
const currentScript = ref(null)
const scriptContent = ref('')
const scriptFileName = ref('')
const compileWarnings = ref([])
const compilingScript = ref(false)

const router = useRouter()
const projectStore = useProjectStore()
const currentProject = computed(() => projectStore.currentProject)

const searchText = ref('')
const showFilter = ref(false)
const activeNodeId = ref('')  // 当前选中的目录 ID
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const loadingTree = ref(false)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

// 目录树数据（从后端获取）
const rawTreeData = ref([])

// 展开的节点 ID 集合
const expandedIds = ref(new Set())

// 展开的树节点（平铺）
const visibleTreeNodes = computed(() => {
  const result = []
  const traverse = (nodes, level = 0) => {
    for (const node of nodes) {
      const expanded = expandedIds.value.has(node.id)
      result.push({ 
        ...node, 
        level, 
        hasChildren: node.children && node.children.length > 0,
        expanded 
      })
      if (node.children && expanded) {
        traverse(node.children, level + 1)
      }
    }
  }
  traverse(rawTreeData.value)
  return result
})

// 当前路径名
const currentPathName = computed(() => {
  if (!activeNodeId.value) return '全部脚本'
  const node = visibleTreeNodes.value.find(n => n.id === activeNodeId.value)
  return node ? node.name : '全部脚本'
})

// 脚本列表（真实数据）
const scripts = ref([])

// 加载目录树
async function loadSuiteTree() {
  loadingTree.value = true
  try {
    const res = await suiteApi.tree(currentProject.value?.id)
    rawTreeData.value = res.data || []
    // 默认展开第一级
    rawTreeData.value.forEach(node => expandedIds.value.add(node.id))
  } catch (e) {
    console.error('加载目录树失败:', e)
  } finally {
    loadingTree.value = false
  }
}

// 加载脚本列表
async function loadScripts() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value
    }
    
    // 根据选择的目录筛选
    if (activeNodeId.value) {
      params.suite_id = activeNodeId.value
    }
    
    // 搜索关键词
    if (searchText.value) {
      params.search = searchText.value
    }
    
    const res = await caseV2Api.list(params)
    scripts.value = res.data.items || res.data || []
    total.value = res.data.total || scripts.value.length
  } catch (e) {
    console.error('加载脚本列表失败:', e)
    ElMessage.error('加载脚本列表失败')
  } finally {
    loading.value = false
  }
}

// 监听筛选条件变化
watch([page, activeNodeId], () => {
  loadScripts()
})

// 搜索防抖
let searchTimer = null
watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadScripts()
  }, 300)
})

// 初始加载
onMounted(() => {
  loadSuiteTree()
  loadScripts()
})

// 点击节点
function handleNodeClick(node) {
  activeNodeId.value = node.id
}

// 展开/折叠
function toggleExpand(node) {
  if (expandedIds.value.has(node.id)) {
    expandedIds.value.delete(node.id)
  } else {
    expandedIds.value.add(node.id)
  }
}

// 选择全部脚本
function selectAllScripts() {
  activeNodeId.value = ''
}

// 选择回收站
function selectTrash() {
  activeNodeId.value = 'trash'
}

// 新建文件夹（支持在选中目录下创建子目录）
async function addFolder() {
  const parentName = activeNodeId.value 
    ? visibleTreeNodes.value.find(n => n.id === activeNodeId.value)?.name 
    : null
  
  const title = parentName ? `在「${parentName}」下新建子目录` : '新建根目录'
  
  ElMessageBox.prompt('请输入目录名称', title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPattern: /^.{1,50}$/,
    inputErrorMessage: '目录名称长度 1-50 个字符'
  }).then(async ({ value }) => {
    if (value) {
      try {
        await suiteApi.create({
          name: value,
          parentId: activeNodeId.value || null,
          projectId: currentProject.value?.id
        })
        ElMessage.success('目录创建成功')
        loadSuiteTree()
      } catch (e) {
        ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
      }
    }
  }).catch(() => {})
}

// 在指定目录下新建子目录
async function addSubFolder(parentNode) {
  ElMessageBox.prompt(`在「${parentNode.name}」下新建子目录`, '新建子目录', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPattern: /^.{1,50}$/,
    inputErrorMessage: '目录名称长度 1-50 个字符'
  }).then(async ({ value }) => {
    if (value) {
      try {
        await suiteApi.create({
          name: value,
          parentId: parentNode.id,
          projectId: currentProject.value?.id
        })
        ElMessage.success('子目录创建成功')
        // 展开父目录
        expandedIds.value.add(parentNode.id)
        loadSuiteTree()
      } catch (e) {
        ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
      }
    }
  }).catch(() => {})
}

// 重命名目录
async function renameFolder(node) {
  ElMessageBox.prompt('请输入新名称', '重命名目录', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: node.name,
    inputPattern: /^.{1,50}$/,
    inputErrorMessage: '目录名称长度 1-50 个字符'
  }).then(async ({ value }) => {
    if (value && value !== node.name) {
      try {
        await suiteApi.update(node.id, { name: value })
        ElMessage.success('重命名成功')
        loadSuiteTree()
      } catch (e) {
        ElMessage.error('重命名失败: ' + (e.response?.data?.detail || e.message))
      }
    }
  }).catch(() => {})
}

// 删除目录
async function deleteFolder(node) {
  ElMessageBox.confirm(`确定删除目录「${node.name}」？`, '提示', { type: 'warning' })
    .then(async () => {
      try {
        await suiteApi.delete(node.id)
        ElMessage.success('删除成功')
        if (activeNodeId.value === node.id) {
          activeNodeId.value = ''
        }
        loadSuiteTree()
      } catch (e) {
        ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
      }
    })
    .catch(() => {})
}

function truncateText(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

function getStatusText(status) {
  const map = { 
    DRAFT: '草稿', 
    ACTIVE: '启用', 
    DEPRECATED: '已废弃',
    pending: '待执行', 
    active: '启用', 
    inactive: '禁用', 
    failed: '失败' 
  }
  return map[status] || status || '草稿'
}

function getAuthorAvatar(author) {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${author || 'system'}`
}

function createScript() {
  router.push('/ui/scripts/new')
}

function editScript(script) {
  router.push(`/ui/scripts/${script.id}/edit`)
}

async function handleCommand(cmd, script) {
  switch (cmd) {
    case 'edit': 
      editScript(script)
      break
    case 'run': 
      ElMessage.info(`即将执行: ${script.name}`)
      router.push(`/ui/scripts/${script.id}/edit?autoRun=true`)
      break
    case 'viewScript':
      await viewGeneratedScript(script)
      break
    case 'copy': 
      try {
        const res = await caseV2Api.create({
          ...script,
          id: undefined,
          name: `${script.name}_copy`,
          createdAt: undefined,
          updatedAt: undefined
        })
        ElMessage.success('脚本已复制')
        loadScripts()
      } catch (e) {
        ElMessage.error('复制失败')
      }
      break
    case 'delete':
      ElMessageBox.confirm(`确定删除「${script.name}」？`, '提示', { type: 'warning' })
        .then(async () => {
          try {
            await caseV2Api.delete(script.id)
            ElMessage.success('删除成功')
            loadScripts()
          } catch (e) {
            ElMessage.error('删除失败')
          }
        })
        .catch(() => {})
      break
  }
}

// 查看生成的 TS 脚本
async function viewGeneratedScript(script) {
  currentScript.value = script
  showScriptDialog.value = true
  compilingScript.value = true
  scriptContent.value = ''
  compileWarnings.value = []
  
  try {
    const res = await caseV2Api.compile(script.id)
    scriptContent.value = res.data.content || res.data.content_preview || '// 编译结果为空'
    scriptFileName.value = res.data.output_path?.split('/').pop() || `${script.name}.test.ts`
    compileWarnings.value = res.data.warnings || []
  } catch (e) {
    console.error('编译失败:', e)
    scriptContent.value = `// 编译失败\n// ${e.response?.data?.detail || e.message}`
    scriptFileName.value = 'error.ts'
  } finally {
    compilingScript.value = false
  }
}

// 复制脚本内容
function copyScript() {
  if (!scriptContent.value) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  
  navigator.clipboard.writeText(scriptContent.value)
    .then(() => ElMessage.success('已复制到剪贴板'))
    .catch(() => ElMessage.error('复制失败'))
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
  flex: 1;
}

.case-count {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 1px 6px;
  border-radius: 10px;
  margin-left: 4px;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.2s;
  margin-left: 4px;
  
  .more-btn {
    color: #94a3b8;
    cursor: pointer;
    padding: 2px;
    border-radius: 4px;
    
    &:hover {
      background: #e2e8f0;
      color: #64748b;
    }
  }
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.all-scripts {
  padding-left: 12px !important;
  margin-bottom: 4px;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 8px;
}

.empty-tree {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
  font-size: 13px;
  
  p {
    margin-bottom: 8px;
  }
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

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
  
  p {
    margin: 16px 0;
    font-size: 14px;
  }
}

/* DRAFT 状态 */
.status-pill.draft {
  background: #f1f5f9;
  color: #64748b;
}

/* 脚本预览弹框 */
:deep(.script-preview-dialog) {
  .el-dialog__body {
    padding: 0;
  }
}

.script-preview-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 13px;
  font-family: monospace;
  
  .el-icon {
    color: #3b82f6;
  }
  
  .filename {
    color: #e2e8f0;
  }
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.code-wrapper {
  flex: 1;
  overflow: auto;
  background: #0f172a;
}

.code-content {
  margin: 0;
  padding: 20px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e2e8f0;
  white-space: pre;
  tab-size: 2;
  
  /* TypeScript 语法高亮（简化版） */
  code {
    color: #e2e8f0;
  }
}

.warnings {
  padding: 12px 20px;
  background: #fefce8;
  border-top: 1px solid #fef08a;
  
  ul {
    margin: 8px 0 0 0;
    padding-left: 20px;
    
    li {
      font-size: 12px;
      color: #854d0e;
    }
  }
}
</style>
