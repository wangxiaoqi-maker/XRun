<template>
  <div class="knowledge-layout">
    <!-- 左侧目录 -->
    <aside class="sidebar-panel">
      <div class="sidebar-header">
        <div class="header-left">
          <div class="logo-box">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          <div class="brand-info">
            <span class="app-name">{{ currentAppName }}</span>
            <span class="workspace">UI 自动化工作台</span>
          </div>
        </div>
        <button class="mini-add-btn" @click="showAddModuleDialog()" :disabled="!selectedAppId" title="新建模块">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>

      <!-- 应用选择 -->
      <div class="app-selector">
        <el-select 
          v-model="selectedAppId" 
          placeholder="选择应用" 
          class="app-select"
          @change="onAppChange"
        >
          <el-option
            v-for="app in appStore.apps"
            :key="app.id"
            :label="app.app_name"
            :value="app.id"
          />
        </el-select>
      </div>

      <div class="nav-scroll">
        <div class="nav-group-label">主要视图</div>
        <div class="nav-item" :class="{ active: selectedModule === 'all' }" @click="selectModule('all')">
          <span class="icon">💠</span> 全部页面 
          <span class="badge">{{ pages.length }}</span>
        </div>
        <div class="nav-item" :class="{ active: selectedModule === 'common' }" @click="selectModule('common')">
          <span class="icon">🧩</span> 公共组件 
          <span class="badge gray">{{ commonPagesCount }}</span>
        </div>
        
        <div class="nav-group-label mt-16">业务模块</div>
        
        <!-- 模块列表 -->
        <template v-for="module in flatModuleList" :key="module.id">
          <div 
            class="nav-item module-item"
            :class="{ active: selectedModule === module.id }"
            :style="{ paddingLeft: (12 + module.depth * 16) + 'px' }"
            @click="selectModule(module.id)"
          >
            <!-- 展开/折叠 -->
            <span 
              v-if="module.children && module.children.length > 0"
              class="expand-icon"
              :class="{ expanded: expandedModules.includes(module.id) }"
              @click.stop="toggleModule(module.id)"
            >▶</span>
            <span v-else class="expand-placeholder"></span>
            
            <span class="icon">📂</span>
            <span class="module-name">{{ module.module_name }}</span>
            <span class="badge gray" v-if="module.pages_count">{{ module.pages_count }}</span>
            
            <!-- 操作菜单 -->
            <el-dropdown trigger="click" @command="handleModuleCommand($event, module)" class="module-actions">
              <span class="action-dots" @click.stop>⋯</span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="add">新增子模块</el-dropdown-item>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c;">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
        
        <!-- 空状态 -->
        <div class="empty-modules" v-if="moduleTree.length === 0 && !loadingModules">
          <span>暂无业务模块</span>
          <a href="javascript:;" @click="showAddModuleDialog()">+ 创建模块</a>
        </div>
      </div>
    </aside>

    <!-- 右侧内容区 -->
    <main class="gallery-container" v-loading="deleting" element-loading-text="删除中...">
      <!-- Hero Header -->
      <header class="hero-header">
        <div class="hero-left">
          <div class="hero-icon-box">📱</div>
          <div class="hero-text">
            <div class="title-row">
              <h1 class="page-title">UI 页面知识库</h1>
              <div class="status-badge">
                <span class="dot"></span> Online
              </div>
            </div>
            <p class="page-desc">
              管理已识别的 App 页面及其 UI 元素资产
              <span class="divider">|</span>
              <span class="stat-text">共收录 <strong>{{ pages.length }}</strong> 个页面</span>
            </p>
          </div>
        </div>
        
        <div class="hero-right">
          <div class="search-box">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input 
              type="text" 
              v-model="searchKeyword"
              placeholder="搜索页面 ID 或名称..."
              @keyup.enter="handleSearch"
            >
          </div>
          
          <div class="view-switcher">
            <button class="switch-btn active" title="网格视图">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            </button>
            <div class="v-line"></div>
            <button class="switch-btn" title="列表视图">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            </button>
          </div>

          <button class="btn-new" @click="goToNewAnalysis">
            <span class="plus">+</span> 新增页面
          </button>
        </div>
      </header>

      <!-- 页面网格 -->
      <div class="gallery-scroll-area">
        <!-- 加载状态 -->
        <div class="card-grid" v-if="loading">
          <div v-for="i in 6" :key="i" class="page-card skeleton">
            <div class="card-top-bar"><div class="skeleton-id"></div></div>
            <div class="card-preview skeleton-preview"></div>
            <div class="card-info">
              <div class="skeleton-title"></div>
              <div class="skeleton-meta"></div>
            </div>
          </div>
        </div>
        
        <!-- 页面列表 -->
        <div class="card-grid" v-else>
          <div
            v-for="(page, index) in filteredPages"
            :key="`page-${page.id}-${index}`"
            class="page-card clickable"
            @click="viewPageDetail(page)"
          >
            <!-- App 标签 -->
            <div class="card-badge" :style="{ backgroundColor: getAppColor(page.app_name) }">
              {{ page.app_name || '未知应用' }}
            </div>
            
            <!-- 截图预览 -->
            <div class="card-preview">
              <img 
                v-if="page.screenshot_url" 
                :src="page.screenshot_url" 
                class="preview-image"
                @error="handleImageError($event, page)"
              />
              <div v-else class="preview-placeholder">
                <el-icon :size="24"><Picture /></el-icon>
                <span>UI Screenshot</span>
              </div>
              <!-- Hover 操作层 -->
              <div class="card-hover-actions">
                <el-button size="small" @click.stop="reAnalyze(page)">重新识别</el-button>
                <el-button size="small" type="danger" plain @click.stop="deletePage(page)">删除</el-button>
              </div>
            </div>
            
            <!-- 页面信息 -->
            <div class="card-info">
              <div class="card-title">{{ page.page_name }}</div>
              <div class="card-meta">
                <el-tag size="small" type="info">{{ page.elements_count || 0 }} 元素</el-tag>
                <el-tag size="small" type="info">V{{ page.version || '1.0' }}</el-tag>
              </div>
              <div class="card-footer">
                <span class="update-time">{{ formatTime(page.updated_at || page.created_at) }}</span>
                <span class="view-detail" @click.stop="openEditDialog(page)">修改</span>
              </div>
            </div>
          </div>

          <!-- 添加新页面卡片 -->
          <div class="page-card add-card" @click="goToNewAnalysis">
            <div class="add-content">
              <el-icon :size="28"><Plus /></el-icon>
              <span>添加新页面</span>
            </div>
          </div>
        </div>
        
        <!-- 空状态提示（仅在无页面且无添加卡片时显示） -->
        <div class="empty-hint" v-if="filteredPages.length === 0 && !loading">
          <span>当前模块暂无页面，点击上方卡片添加</span>
        </div>
      </div>
    </main>

    <!-- 编辑页面弹窗 -->
    <el-dialog v-model="editDialogVisible" title="编辑页面信息" width="500px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="页面名称">
          <el-input v-model="editForm.page_name" placeholder="请输入页面名称" />
        </el-form-item>
        <el-form-item label="所属模块">
          <el-select v-model="editForm.module_id" placeholder="选择模块" clearable style="width: 100%">
            <el-option label="公共组件库" value="common" />
            <el-option v-for="module in allModulesFlat" :key="module.id" :label="module.module_name" :value="module.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="页面描述">
          <el-input v-model="editForm.page_description" type="textarea" :rows="3" placeholder="请输入页面描述" />
        </el-form-item>
        <el-form-item label="标记公共">
          <el-switch v-model="editForm.is_common" />
          <span class="form-tip">公共组件可被多个模块复用</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePage" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增模块弹窗 -->
    <el-dialog v-model="addModuleDialogVisible" title="新增业务模块" width="400px" :close-on-click-modal="false">
      <el-form :model="moduleForm" label-width="80px">
        <el-form-item label="模块名称" required>
          <el-input v-model="moduleForm.module_name" placeholder="如：充值/缴费、转账业务" />
        </el-form-item>
        <el-form-item label="父模块">
          <el-select v-model="moduleForm.parent_id" placeholder="选择父模块（可选）" clearable style="width: 100%">
            <el-option v-for="module in allModulesFlat" :key="module.id" :label="module.module_name" :value="module.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="模块描述">
          <el-input v-model="moduleForm.description" type="textarea" :rows="2" placeholder="模块功能描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addModuleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createModule" :loading="creatingModule">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑模块弹窗 -->
    <el-dialog v-model="editModuleDialogVisible" title="编辑模块" width="400px" :close-on-click-modal="false">
      <el-form :model="editModuleForm" label-width="80px">
        <el-form-item label="模块名称" required>
          <el-input v-model="editModuleForm.module_name" placeholder="模块名称" />
        </el-form-item>
        <el-form-item label="模块描述">
          <el-input v-model="editModuleForm.description" type="textarea" :rows="2" placeholder="模块功能描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editModuleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="updateModule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const appStore = useAppStore()

// 状态
const loading = ref(true)
const loadingModules = ref(true)
const deleting = ref(false)
const saving = ref(false)
const creatingModule = ref(false)

const pages = ref([])
const moduleTree = ref([])
const searchKeyword = ref('')
const selectedModule = ref('all')
const selectedAppId = ref('')
const expandedModules = ref([])

// 计算属性
const currentAppId = computed(() => selectedAppId.value)

const currentAppName = computed(() => {
  const app = appStore.apps.find(a => a.id === selectedAppId.value)
  return app?.app_name || '选择应用'
})

const commonPagesCount = computed(() => pages.value.filter(p => p.is_common).length)

const flatModuleList = computed(() => {
  const result = []
  function flatten(modules, depth = 0) {
    for (const module of modules) {
      result.push({ ...module, depth })
      if (module.children?.length > 0 && expandedModules.value.includes(module.id)) {
        flatten(module.children, depth + 1)
      }
    }
  }
  flatten(moduleTree.value)
  return result
})

const allModulesFlat = computed(() => {
  const result = []
  function flatten(modules, prefix = '') {
    for (const module of modules) {
      result.push({ id: module.id, module_name: prefix + module.module_name })
      if (module.children?.length > 0) {
        flatten(module.children, prefix + module.module_name + ' / ')
      }
    }
  }
  flatten(moduleTree.value)
  return result
})

// 获取模块及其所有子模块的 ID 列表
function getModuleAndChildrenIds(moduleId) {
  const ids = [moduleId]
  function collectChildren(modules) {
    for (const m of modules) {
      if (m.id === moduleId || ids.includes(m.parent_id)) {
        if (!ids.includes(m.id)) ids.push(m.id)
      }
      if (m.children?.length > 0) {
        collectChildren(m.children)
      }
    }
  }
  // 递归遍历整棵树
  function traverse(modules) {
    for (const m of modules) {
      if (ids.includes(m.id) && m.children?.length > 0) {
        for (const child of m.children) {
          if (!ids.includes(child.id)) ids.push(child.id)
        }
        traverse(m.children)
      } else if (m.children?.length > 0) {
        traverse(m.children)
      }
    }
  }
  traverse(moduleTree.value)
  return ids
}

const filteredPages = computed(() => {
  let result = pages.value
  if (selectedModule.value === 'common') {
    result = result.filter(p => p.is_common)
  } else if (selectedModule.value !== 'all') {
    // 获取当前模块及其所有子模块的 ID
    const moduleIds = getModuleAndChildrenIds(selectedModule.value)
    result = result.filter(p => moduleIds.includes(p.module_id))
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(p =>
      p.page_name?.toLowerCase().includes(keyword) ||
      p.page_description?.toLowerCase().includes(keyword)
    )
  }
  return result
})

// 弹窗状态
const editDialogVisible = ref(false)
const editForm = ref({ id: '', page_name: '', page_description: '', module_id: '', is_common: false })
const addModuleDialogVisible = ref(false)
const moduleForm = ref({ module_name: '', parent_id: '', description: '' })
const editModuleDialogVisible = ref(false)
const editModuleForm = ref({ id: '', module_name: '', description: '' })

// 工具函数
const appColors = ['#f97316', '#ef4444', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#6366f1']

function getAppColor(appName) {
  if (!appName) return '#94a3b8'
  let hash = 0
  for (let i = 0; i < appName.length; i++) {
    hash = appName.charCodeAt(i) + ((hash << 5) - hash)
  }
  return appColors[Math.abs(hash) % appColors.length]
}

function formatTime(timeStr) {
  if (!timeStr) return '未知'
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString('zh-CN')
}

// 数据加载
async function loadModules() {
  if (!currentAppId.value) return
  loadingModules.value = true
  try {
    const res = await knowledgeApi.getModuleTree(currentAppId.value)
    moduleTree.value = res.data?.modules || []
  } catch (e) {
    console.error('加载模块列表失败:', e)
  } finally {
    loadingModules.value = false
  }
}

async function loadPages() {
  loading.value = true
  try {
    if (currentAppId.value) {
      const res = await knowledgeApi.getPagesByModule(currentAppId.value)
      const data = res.data || {}
      let allPages = [...(data.unassigned_pages || [])]
      for (const moduleGroup of (data.modules || [])) {
        allPages = allPages.concat(moduleGroup.pages || [])
      }
      pages.value = allPages
    } else {
      const res = await knowledgeApi.getPages({ limit: 100 })
      pages.value = res.data || []
    }
  } catch (e) {
    console.error('加载页面列表失败:', e)
    try {
      const res = await knowledgeApi.getPages({ limit: 100 })
      pages.value = res.data || []
    } catch (e2) {
      ElMessage.error('加载页面列表失败')
    }
  } finally {
    loading.value = false
  }
}

// 模块操作
function selectModule(moduleId) {
  selectedModule.value = moduleId
}

function toggleModule(moduleId) {
  const index = expandedModules.value.indexOf(moduleId)
  if (index > -1) {
    expandedModules.value.splice(index, 1)
  } else {
    expandedModules.value.push(moduleId)
  }
}

function showAddModuleDialog(parentId = null) {
  moduleForm.value = { module_name: '', parent_id: parentId || '', description: '' }
  addModuleDialogVisible.value = true
}

function handleModuleCommand(command, module) {
  if (command === 'add') showAddModuleDialog(module.id)
  else if (command === 'edit') {
    editModuleForm.value = { id: module.id, module_name: module.module_name, description: module.description || '' }
    editModuleDialogVisible.value = true
  }
  else if (command === 'delete') deleteModuleConfirm(module)
}

async function createModule() {
  if (!moduleForm.value.module_name) {
    ElMessage.warning('请输入模块名称')
    return
  }
  if (!currentAppId.value) {
    ElMessage.warning('请先选择应用')
    return
  }
  creatingModule.value = true
  try {
    await knowledgeApi.createModule({
      app_id: currentAppId.value,
      module_name: moduleForm.value.module_name,
      parent_id: moduleForm.value.parent_id || null,
      description: moduleForm.value.description
    })
    ElMessage.success('模块创建成功')
    addModuleDialogVisible.value = false
    if (moduleForm.value.parent_id && !expandedModules.value.includes(moduleForm.value.parent_id)) {
      expandedModules.value.push(moduleForm.value.parent_id)
    }
    loadModules()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建模块失败')
  } finally {
    creatingModule.value = false
  }
}

async function updateModule() {
  if (!editModuleForm.value.module_name) {
    ElMessage.warning('请输入模块名称')
    return
  }
  try {
    await knowledgeApi.updateModule(editModuleForm.value.id, {
      module_name: editModuleForm.value.module_name,
      description: editModuleForm.value.description
    })
    ElMessage.success('模块更新成功')
    editModuleDialogVisible.value = false
    loadModules()
  } catch (e) {
    ElMessage.error('更新模块失败')
  }
}

async function deleteModuleConfirm(module) {
  try {
    await ElMessageBox.confirm(`确定要删除模块「${module.module_name}」吗？`, '删除确认', { type: 'warning' })
    await knowledgeApi.deleteModule(module.id)
    ElMessage.success('模块删除成功')
    if (selectedModule.value === module.id) selectedModule.value = 'all'
    loadModules()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除模块失败')
  }
}

// 页面操作
function goToNewAnalysis() {
  router.push('/ui/knowledge/new')
}

function viewPageDetail(page) {
  router.push(`/ui/knowledge/${page.id}`)
}

function handleImageError(event, page) {
  page.screenshot_url = null
}

function handleSearch() {
  // 由 computed 自动处理
}

function handlePageCommand(command, page) {
  if (command === 'edit') openEditDialog(page)
  else if (command === 'reanalyze') reAnalyze(page)
  else if (command === 'delete') deletePage(page)
}

function openEditDialog(page) {
  editForm.value = {
    id: page.id,
    page_name: page.page_name || '',
    page_description: page.page_description || '',
    module_id: page.module_id || '',
    is_common: page.is_common || false
  }
  editDialogVisible.value = true
}

async function savePage() {
  if (!editForm.value.page_name) {
    ElMessage.warning('请输入页面名称')
    return
  }
  saving.value = true
  try {
    await knowledgeApi.updatePage(editForm.value.id, {
      page_name: editForm.value.page_name,
      page_description: editForm.value.page_description,
      module_id: editForm.value.module_id === 'common' ? null : editForm.value.module_id,
      is_common: editForm.value.is_common
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadPages()
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function reAnalyze(page) {
  router.push('/ui/knowledge/new')
}

async function deletePage(page) {
  try {
    await ElMessageBox.confirm(`确定要删除页面「${page.page_name}」吗？此操作不可恢复。`, '删除确认', { type: 'warning' })
    deleting.value = true
    await knowledgeApi.deletePage(page.id)
    ElMessage.success('删除成功')
    loadPages()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}

// 应用切换
function onAppChange(appId) {
  selectedModule.value = 'all'
  if (appId) {
    appStore.selectApp(appStore.apps.find(a => a.id === appId))
    loadModules()
    loadPages()
  } else {
    moduleTree.value = []
    pages.value = []
  }
}

watch(currentAppId, () => {
  if (currentAppId.value) {
    loadModules()
    loadPages()
  }
})

onMounted(async () => {
  await appStore.loadApps()
  if (appStore.apps.length > 0) {
    selectedAppId.value = appStore.currentApp?.id || appStore.apps[0].id
    await loadModules()
    loadPages()
  } else {
    loadPages()
    loading.value = false
    loadingModules.value = false
  }
})
</script>

<style scoped>
/* 基础布局 */
.knowledge-layout {
  display: flex;
  height: 100%;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
}

/* ===== 左侧目录 ===== */
.sidebar-panel {
  width: 240px;
  background: white;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f1f5f9;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-box {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
  flex-shrink: 0;
}

.brand-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.app-name {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.workspace {
  font-size: 10px;
  color: #94a3b8;
  font-weight: 500;
}

/* 应用选择 */
.app-selector {
  padding: 8px 12px;
  border-bottom: 1px solid #f1f5f9;
}

.app-select {
  width: 100%;
}

.app-select :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e2e8f0 !important;
  border-radius: 8px;
}

.app-select :deep(.el-input__inner) {
  font-size: 13px;
}

.mini-add-btn {
  width: 24px;
  height: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.mini-add-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #eff6ff;
}

.mini-add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 导航 */
.nav-scroll {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-group-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 700;
  padding: 0 12px 8px;
  text-transform: uppercase;
}

.mt-16 {
  margin-top: 16px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 2px;
  transition: all 0.15s;
  position: relative;
}

.nav-item:hover {
  background: #f1f5f9;
}

.nav-item.active {
  background: #eff6ff;
  color: #3b82f6;
  font-weight: 600;
}

.nav-item .icon {
  font-size: 14px;
}

.nav-item .badge {
  margin-left: auto;
  font-size: 10px;
  background: #dbeafe;
  color: #3b82f6;
  padding: 1px 6px;
  border-radius: 10px;
}

.nav-item .badge.gray {
  background: #f1f5f9;
  color: #94a3b8;
}

/* 模块项 */
.module-item {
  padding-right: 8px;
}

.module-item:hover .module-actions {
  opacity: 1;
}

.expand-icon {
  font-size: 8px;
  color: #94a3b8;
  transition: transform 0.2s;
  cursor: pointer;
  margin-right: 2px;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  width: 12px;
}

.module-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-actions {
  opacity: 0;
  transition: opacity 0.15s;
}

.action-dots {
  font-size: 14px;
  color: #94a3b8;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
}

.action-dots:hover {
  color: #3b82f6;
  background: #e2e8f0;
}

.empty-modules {
  text-align: center;
  padding: 20px;
  color: #94a3b8;
  font-size: 12px;
}

.empty-modules a {
  color: #3b82f6;
  text-decoration: none;
  display: block;
  margin-top: 8px;
}

/* ===== 右侧内容区 ===== */
.gallery-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Hero Header */
.hero-header {
  height: 88px;
  padding: 0 32px;
  background: white;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-icon-box {
  width: 48px;
  height: 48px;
  background: #f1f5f9;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  line-height: 1;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #15803d;
  background: #dcfce7;
  padding: 2px 8px;
  border-radius: 12px;
  border: 1px solid #bbf7d0;
}

.status-badge .dot {
  width: 6px;
  height: 6px;
  background: #15803d;
  border-radius: 50%;
}

.page-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.divider {
  color: #e2e8f0;
  font-size: 12px;
}

.stat-text {
  color: #64748b;
  font-size: 12px;
  background: #f8fafc;
  padding: 2px 6px;
  border-radius: 4px;
}

.stat-text strong {
  color: #0f172a;
  font-weight: 700;
}

/* Hero Right */
.hero-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  position: relative;
}

.search-box input {
  padding: 9px 12px 9px 34px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  width: 200px;
  outline: none;
  font-size: 13px;
  background: #fff;
  transition: all 0.2s;
}

.search-box input:focus {
  border-color: #3b82f6;
  width: 240px;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
}

.view-switcher {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  padding: 2px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.switch-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  border-radius: 6px;
}

.switch-btn.active {
  background: white;
  color: #3b82f6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.v-line {
  width: 1px;
  height: 16px;
  background: #cbd5e1;
  margin: 0 2px;
}

.btn-new {
  padding: 0 20px;
  height: 38px;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
  transition: all 0.2s;
}

.btn-new:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

.btn-new .plus {
  font-size: 16px;
  font-weight: 300;
}

/* 网格区域 */
.gallery-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 1400px) {
  .card-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 1100px) {
  .card-grid { grid-template-columns: repeat(2, 1fr); }
}

/* 页面卡片 */
.page-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;
  border: 1px solid #e2e8f0;
  position: relative;
}

.page-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -6px rgba(0, 0, 0, 0.1);
}

.page-card.clickable {
  cursor: pointer;
}

/* App 标签 */
.card-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  z-index: 2;
}

/* 截图预览 */
.card-preview {
  height: 140px;
  background: linear-gradient(180deg, #e2e8f0 0%, #f1f5f9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
}

.preview-placeholder span {
  font-size: 12px;
  font-weight: 500;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
}

/* Hover 操作层 */
.card-hover-actions {
  position: absolute;
  inset: 0;
  background: rgba(51, 65, 85, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.page-card:hover .card-hover-actions {
  opacity: 1;
}

.card-hover-actions .el-button {
  min-width: 80px;
  border-radius: 6px;
}

/* 页面信息 */
.card-info {
  padding: 14px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.card-meta .el-tag {
  border: none;
  background: #f1f5f9;
  color: #64748b;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}

.update-time {
  font-size: 11px;
  color: #94a3b8;
}

.view-detail {
  font-size: 12px;
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}

.view-detail:hover {
  color: #2563eb;
}

/* 添加卡片 */
.add-card {
  border: 2px dashed #cbd5e1;
  background: transparent;
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.add-card:hover {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.02);
}

.add-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}

.add-card:hover .add-content {
  color: #3b82f6;
}

.add-content span {
  font-size: 13px;
  font-weight: 500;
}

/* 骨架屏 */
.page-card.skeleton {
  pointer-events: none;
}

.skeleton-id {
  width: 50px;
  height: 18px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

.skeleton-preview {
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-title {
  height: 18px;
  width: 70%;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-meta {
  height: 14px;
  width: 50%;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 空状态提示 */
.empty-hint {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 13px;
}

/* 表单提示 */
.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #94a3b8;
}
</style>
