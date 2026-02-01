<template>
  <div class="page-knowledge" v-loading="deleting" element-loading-text="删除中...">
    <!-- 顶部标题区 -->
    <div class="page-header">
      <div class="header-left">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="32" height="32">
            <defs>
              <linearGradient id="kbGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#818cf8"/>
                <stop offset="100%" style="stop-color:#6366f1"/>
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="20" height="20" rx="6" fill="url(#kbGradient)"/>
            <path d="M8 8h8M8 12h8M8 16h5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="header-text">
          <h1 class="page-title">UI 页面知识库</h1>
          <p class="page-subtitle">管理已识别的 APP 页面及其 UI 元素资产</p>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" class="add-btn" @click="goToNewAnalysis">
          <el-icon><Plus /></el-icon>
          新增分析
        </el-button>
        <div class="header-stats">
          <div class="stat-item">
            <span class="stat-value">{{ stats.total_pages || 0 }}</span>
            <span class="stat-label">页面</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ stats.total_elements || 0 }}</span>
            <span class="stat-label">元素</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索页面名称或 ID..."
        prefix-icon="Search"
        clearable
        class="search-input"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      />
      <el-select v-model="selectedApp" placeholder="所有应用" clearable @change="handleFilter" class="app-select">
        <el-option
          v-for="app in apps"
          :key="app.id"
          :label="app.app_name"
          :value="app.id"
        />
      </el-select>
    </div>

    <!-- 加载状态骨架屏 -->
    <div class="page-grid" v-if="loading">
      <div v-for="i in 10" :key="i" class="page-card skeleton-card">
        <div class="skeleton-badge"></div>
        <div class="skeleton-preview"></div>
        <div class="skeleton-info">
          <div class="skeleton-title"></div>
          <div class="skeleton-meta"></div>
          <div class="skeleton-footer"></div>
        </div>
      </div>
    </div>

    <!-- 网格视图 -->
    <div class="page-grid" v-else>
      <div
        v-for="(page, index) in pages"
        :key="`page-${page.id}-${index}`"
        class="page-card clickable-card"
        @click="viewPageDetail(page)"
      >
        <!-- App 标签 -->
        <div class="card-badge" :style="{ backgroundColor: getAppColor(page.app_name) }">
          {{ page.app_name || '未知' }}
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
          <div class="card-hover-actions" @click.stop>
            <el-button size="small" @click.stop="reAnalyze(page)">重新识别</el-button>
            <el-button size="small" type="danger" plain @click.stop="deletePage(page)">删除</el-button>
          </div>
        </div>
        
        <!-- 页面信息 -->
        <div class="card-info">
          <div class="card-title-row">
            <span class="card-title">{{ page.page_name }}</span>
            <span class="status-dot" :class="getStatusClass(page)"></span>
          </div>
          <div class="card-meta">
            <el-tag size="small" type="info">{{ page.elements_count || 0 }} 元素</el-tag>
            <el-tag size="small" type="info">V{{ page.visit_count || '1.0' }}</el-tag>
          </div>
          <div class="card-footer">
            <span class="update-time">{{ formatTime(page.updated_at || page.created_at) }}</span>
            <div class="card-actions" @click.stop>
              <span class="action-link" @click.stop="openEditDialog(page)">修改</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 添加新页面卡片 -->
      <div class="page-card add-card" @click="goToNewAnalysis" v-if="pages.length > 0">
        <div class="add-content">
          <el-icon :size="24"><Plus /></el-icon>
          <span>添加新页面</span>
        </div>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" v-if="pages.length === 0">
        <el-icon :size="48"><FolderOpened /></el-icon>
        <p>暂无页面数据</p>
        <el-button type="primary" @click="goToNewAnalysis">
          <el-icon><Plus /></el-icon>
          新增页面分析
        </el-button>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > pageSize && !loading">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, prev, pager, next"
        @size-change="loadPages"
        @current-change="loadPages"
      />
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑页面信息"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="页面名称">
          <el-input v-model="editForm.page_name" placeholder="请输入页面名称" />
        </el-form-item>
        <el-form-item label="页面描述">
          <el-input
            v-model="editForm.page_description"
            type="textarea"
            :rows="3"
            placeholder="请输入页面描述"
          />
        </el-form-item>
        <el-form-item label="页面类型">
          <el-select v-model="editForm.page_type" placeholder="选择类型" style="width: 100%">
            <el-option label="首页" value="home" />
            <el-option label="详情页" value="detail" />
            <el-option label="列表页" value="list" />
            <el-option label="个人中心" value="profile" />
            <el-option label="设置页" value="settings" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePage" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Picture, FolderOpened } from '@element-plus/icons-vue'
import { knowledgeApi } from '@/api'

const router = useRouter()

// 状态
const loading = ref(true)
const deleting = ref(false)
const saving = ref(false)
const pages = ref([])
const apps = ref([])
const stats = ref({})
const searchKeyword = ref('')
const selectedApp = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 编辑弹窗
const editDialogVisible = ref(false)
const editForm = ref({
  id: '',
  page_name: '',
  page_description: '',
  page_type: ''
})

// 颜色映射
const appColors = {
  '翼支付': '#f97316',
  '淘宝': '#f59e0b',
  'BestPay': '#3b82f6'
}
const defaultColors = ['#6366f1', '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#ec4899']
let colorIndex = 0

function getAppColor(appName) {
  if (!appName) return '#94a3b8'
  if (appColors[appName]) return appColors[appName]
  if (!appColors[appName]) {
    appColors[appName] = defaultColors[colorIndex % defaultColors.length]
    colorIndex++
  }
  return appColors[appName]
}

function getStatusClass(page) {
  if (page.confidence_score >= 0.8) return 'status-success'
  if (page.confidence_score >= 0.5) return 'status-warning'
  return 'status-danger'
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

// 加载数据
async function loadStats() {
  try {
    const res = await knowledgeApi.getStats()
    stats.value = res.data || {}
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

async function loadApps() {
  try {
    const res = await knowledgeApi.getApps()
    apps.value = res.data || []
  } catch (e) {
    console.error('加载应用列表失败:', e)
  }
}

async function loadPages() {
  loading.value = true
  try {
    const params = {
      offset: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    if (selectedApp.value) {
      const app = apps.value.find(a => a.id === selectedApp.value)
      if (app) params.app_name = app.app_name
    }
    
    const res = await knowledgeApi.getPages(params)
    let pageList = res.data || []
    
    // 前端搜索过滤
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      pageList = pageList.filter(page => 
        page.page_name?.toLowerCase().includes(keyword) ||
        page.page_description?.toLowerCase().includes(keyword)
      )
    }
    
    pages.value = pageList
    total.value = stats.value.total_pages || pageList.length
  } catch (e) {
    console.error('加载页面列表失败:', e)
    ElMessage.error('加载页面列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadPages()
}

function handleFilter() {
  currentPage.value = 1
  loadPages()
}

// 页面操作
function goToNewAnalysis() {
  router.push('/ui/knowledge/new')
}

function viewPageDetail(page) {
  router.push(`/ui/knowledge/${page.id}`)
}

function reAnalyze(page) {
  router.push('/ui/knowledge/new')
}

function handleImageError(event, page) {
  // 图片加载失败，隐藏图片显示占位符
  page.screenshot_url = null
}

// 编辑功能
function openEditDialog(page) {
  editForm.value = {
    id: page.id,
    page_name: page.page_name || '',
    page_description: page.page_description || '',
    page_type: page.page_type || 'other'
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
      page_type: editForm.value.page_type
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadPages()
  } catch (e) {
    console.error('保存失败:', e)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function deletePage(page) {
  try {
    await ElMessageBox.confirm(
      `确定要删除页面「${page.page_name}」吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    
    deleting.value = true
    await knowledgeApi.deletePage(page.id)
    ElMessage.success('删除成功')
    loadPages()
    loadStats()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadStats(), loadApps()])
  loadPages()
})
</script>

<style scoped>
.page-knowledge {
  padding: 20px 32px;
  height: 100%;
  overflow-y: auto;
  background: #f8fafc;
}

/* 顶部标题区 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  flex-shrink: 0;
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.page-subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-stats {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 0 10px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.stat-divider {
  width: 1px;
  height: 24px;
  background: #e2e8f0;
}

.add-btn {
  height: 36px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
}

.add-btn:hover {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
}

.search-input {
  width: 280px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #e2e8f0;
}

.app-select {
  width: 140px;
}

/* 网格视图 - 固定5列 */
.page-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

@media (max-width: 1400px) {
  .page-grid { grid-template-columns: repeat(4, 1fr); }
}

@media (max-width: 1100px) {
  .page-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 800px) {
  .page-grid { grid-template-columns: repeat(2, 1fr); }
}

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

.clickable-card {
  cursor: pointer;
}

.card-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  z-index: 2;
}

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
  gap: 4px;
  color: #94a3b8;
}

.preview-placeholder span {
  font-size: 11px;
  font-weight: 500;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top center;
}

/* Hover 操作层 - 只有两个按钮，水平排列 */
.card-hover-actions {
  position: absolute;
  inset: 0;
  background: rgba(51, 65, 85, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.page-card:hover .card-hover-actions {
  opacity: 1;
}

.card-hover-actions .el-button {
  min-width: 70px;
  height: 28px;
  border-radius: 6px;
  font-size: 12px;
  padding: 0 12px;
}

.card-info {
  padding: 10px;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-success { background: #10b981; }
.status-warning { background: #f59e0b; }
.status-danger { background: #ef4444; }

.card-meta {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.card-meta .el-tag {
  border-radius: 4px;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  font-size: 10px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.update-time {
  font-size: 10px;
  color: #94a3b8;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-link {
  font-size: 11px;
  color: #64748b;
  cursor: pointer;
  transition: color 0.2s;
}

.action-link:hover {
  color: #6366f1;
}

.action-link.primary {
  color: #6366f1;
  font-weight: 500;
}

.action-link.primary:hover {
  color: #4f46e5;
}

/* 添加卡片 */
.add-card {
  border: 2px dashed #cbd5e1;
  background: transparent;
  min-height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.add-card:hover {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.02);
}

.add-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
}

.add-card:hover .add-content {
  color: #6366f1;
}

.add-content span {
  font-size: 12px;
  font-weight: 500;
}

/* 骨架屏 */
.skeleton-card {
  pointer-events: none;
}

.skeleton-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 40px;
  height: 18px;
  border-radius: 6px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-preview {
  height: 100px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-info {
  padding: 10px;
}

.skeleton-title {
  height: 14px;
  width: 70%;
  border-radius: 4px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  margin-bottom: 8px;
}

.skeleton-meta {
  height: 18px;
  width: 50%;
  border-radius: 4px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  margin-bottom: 10px;
}

.skeleton-footer {
  height: 10px;
  width: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-state p {
  margin: 12px 0 20px;
  font-size: 14px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>
