<template>
  <div class="app-manage">
    <div class="page-header">
      <div class="header-left">
        <div class="title-icon">
          <el-icon><Grid /></el-icon>
        </div>
        <div class="title-text">
          <h1 class="page-title">应用管理</h1>
          <span class="page-divider">/</span>
          <span class="page-desc">管理被测应用及其版本、自动化配置参数</span>
        </div>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        接入新应用
      </el-button>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <el-input 
        v-model="keyword" 
        placeholder="搜索应用名称或包名..." 
        prefix-icon="Search"
        clearable
        class="search-input"
        @input="debouncedSearch"
      />
      <div class="platform-filter">
        <span 
          class="filter-item" 
          :class="{ active: platform === '' }"
          @click="platform = ''"
        >全部</span>
        <span 
          class="filter-item" 
          :class="{ active: platform === 'android' }"
          @click="platform = 'android'"
        >Android</span>
        <span 
          class="filter-item" 
          :class="{ active: platform === 'ios' }"
          @click="platform = 'ios'"
        >iOS</span>
      </div>
    </div>
    
    <!-- 应用列表 -->
    <div class="app-list" v-loading="loading">
      <div 
        v-for="app in apps" 
        :key="app.id" 
        class="app-card"
      >
        <div class="card-header">
          <div class="app-icon">
            <img v-if="app.icon_url" :src="app.icon_url" alt="icon" />
            <span v-else class="default-icon">{{ app.name?.charAt(0) }}</span>
          </div>
          <div class="app-info">
            <div class="app-name-row">
              <span class="app-name">{{ app.name }}</span>
              <span v-if="app.name_en" class="app-name-en">({{ app.name_en }})</span>
              <el-tag 
                :type="app.platform === 'android' ? 'success' : ''" 
                size="small"
                class="platform-tag"
                :class="app.platform"
              >
                <span class="platform-icon">{{ app.platform === 'android' ? '🤖' : '🍎' }}</span>
                {{ app.platform === 'android' ? 'Android' : 'iOS' }}
              </el-tag>
            </div>
            <span class="package-name">{{ app.package_name }}</span>
          </div>
          <el-dropdown trigger="click" @command="cmd => handleCommand(cmd, app)">
            <span class="more-btn">•••</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="config">配置</el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <span style="color: #f56c6c">删除</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div class="version-info">
          <div class="info-item">
            <span class="label">当前版本</span>
            <span class="value version">{{ app.latest_version || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">最后更新</span>
            <span class="value">{{ formatTime(app.updated_at) }}</span>
          </div>
        </div>
        
        <div class="card-footer">
          <div class="stat-item">
            <span class="stat-value">{{ app.page_count || 0 }}</span>
            <span class="stat-label">页面</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">{{ app.ui_element_count || 0 }}</span>
            <span class="stat-label">UI 元素</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item config-btn" @click="handleCommand('config', app)">
            <el-icon><Setting /></el-icon>
            <span class="stat-label">配置</span>
          </div>
        </div>
      </div>
      
      <!-- 添加新应用卡片 -->
      <div v-if="projectStore.currentProject" class="app-card add-card" @click="openCreateDialog">
        <div class="add-content">
          <el-icon class="add-icon"><Loading /></el-icon>
          <span class="add-text">接入新应用</span>
        </div>
      </div>
      
      <!-- 无项目提示 -->
      <div v-if="!projectStore.currentProject && !loading" class="no-project-tip">
        <el-icon class="tip-icon"><Folder /></el-icon>
        <p>请先在顶部选择一个项目</p>
      </div>
    </div>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="editingApp ? '编辑应用' : '接入新应用'"
      width="560px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="应用名称" prop="name">
          <el-input v-model="form.name" placeholder="如：翼支付" />
        </el-form-item>
        <el-form-item label="英文名称">
          <el-input v-model="form.name_en" placeholder="如：BestPay（可选）" />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-radio-group v-model="form.platform" :disabled="!!editingApp">
            <el-radio value="android">
              <span class="platform-option">🤖 Android</span>
            </el-radio>
            <el-radio value="ios">
              <span class="platform-option">🍎 iOS</span>
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包名" prop="package_name">
          <el-input 
            v-model="form.package_name" 
            :placeholder="form.platform === 'ios' ? 'Bundle ID，如：com.bestpay.app' : '包名，如：com.chinatelecom.bestpay'"
            :disabled="!!editingApp"
          />
        </el-form-item>
        <el-form-item label="当前版本">
          <el-input v-model="form.latest_version" placeholder="如：V10.6.5" />
        </el-form-item>
        <el-form-item label="图标URL">
          <el-input v-model="form.icon_url" placeholder="应用图标的URL地址（可选）" />
        </el-form-item>
        <el-form-item v-if="form.platform === 'android'" label="启动Activity">
          <el-input 
            v-model="form.launch_activity" 
            placeholder="如：.activity.SplashActivity（可选）" 
          />
        </el-form-item>
        <el-form-item label="应用描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="2"
            placeholder="应用描述（可选）" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingApp ? '保存' : '接入' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 配置对话框 -->
    <el-dialog 
      v-model="configDialogVisible" 
      title="应用配置"
      width="560px"
    >
      <div v-if="configApp" class="config-content">
        <div class="config-header">
          <div class="app-icon">
            <img v-if="configApp.icon_url" :src="configApp.icon_url" alt="icon" />
            <span v-else class="default-icon">{{ configApp.name?.charAt(0) }}</span>
          </div>
          <div class="config-info">
            <h3>{{ configApp.name }}</h3>
            <span>{{ configApp.package_name }}</span>
          </div>
        </div>
        
        <el-divider />
        
        <el-form label-width="100px">
          <el-form-item label="启动Activity" v-if="configApp.platform === 'android'">
            <el-input v-model="configForm.launch_activity" placeholder="启动Activity" />
          </el-form-item>
          <el-form-item label="当前版本">
            <el-input v-model="configForm.latest_version" placeholder="版本号" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingConfig" @click="saveConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Setting, Grid, Loading, Folder } from '@element-plus/icons-vue'
import { appApi } from '@/api'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

const loading = ref(false)
const apps = ref([])
const keyword = ref('')
const platform = ref('')

const dialogVisible = ref(false)
const editingApp = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const configDialogVisible = ref(false)
const configApp = ref(null)
const configForm = ref({})
const savingConfig = ref(false)

const form = ref({
  name: '',
  name_en: '',
  platform: 'android',
  package_name: '',
  latest_version: '',
  icon_url: '',
  launch_activity: '',
  description: '',
  project_id: ''
})

const rules = {
  name: [{ required: true, message: '请输入应用名称', trigger: 'blur' }],
  platform: [{ required: true, message: '请选择平台', trigger: 'change' }],
  package_name: [{ required: true, message: '请输入包名', trigger: 'blur' }]
}

let searchTimer = null
function debouncedSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadApps()
  }, 300)
}

watch(platform, () => {
  loadApps()
})

async function loadApps() {
  loading.value = true
  try {
    const params = { 
      platform: platform.value, 
      keyword: keyword.value 
    }
    // 按当前项目筛选应用
    if (projectStore.currentProject?.id) {
      params.project_id = projectStore.currentProject.id
    }
    const res = await appApi.list(params)
    apps.value = res.data
  } catch (e) {
    ElMessage.error('加载应用列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingApp.value = null
  form.value = {
    name: '',
    name_en: '',
    platform: 'android',
    package_name: '',
    latest_version: '',
    icon_url: '',
    launch_activity: '',
    description: '',
    project_id: projectStore.currentProject?.id || ''  // 默认关联当前项目
  }
  dialogVisible.value = true
}

function handleCommand(cmd, app) {
  switch (cmd) {
    case 'edit':
      editingApp.value = app
      form.value = {
        name: app.name,
        name_en: app.name_en || '',
        platform: app.platform,
        package_name: app.package_name,
        latest_version: app.latest_version || '',
        icon_url: app.icon_url || '',
        launch_activity: app.launch_activity || '',
        description: app.description || '',
        project_id: app.project_id || ''
      }
      dialogVisible.value = true
      break
    case 'config':
      configApp.value = app
      configForm.value = {
        launch_activity: app.launch_activity || '',
        latest_version: app.latest_version || ''
      }
      configDialogVisible.value = true
      break
    case 'delete':
      ElMessageBox.confirm(`确定要删除应用「${app.name}」吗？`, '删除确认', {
        type: 'warning'
      }).then(async () => {
        await appApi.delete(app.id)
        apps.value = apps.value.filter(a => a.id !== app.id)
        ElMessage.success('应用已删除')
      }).catch(() => {})
      break
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    if (editingApp.value) {
      const res = await appApi.update(editingApp.value.id, {
        name: form.value.name,
        name_en: form.value.name_en,
        latest_version: form.value.latest_version,
        icon_url: form.value.icon_url,
        launch_activity: form.value.launch_activity,
        description: form.value.description
      })
      const idx = apps.value.findIndex(a => a.id === editingApp.value.id)
      if (idx > -1) {
        apps.value[idx] = res.data
      }
      ElMessage.success('应用已更新')
    } else {
      const res = await appApi.create(form.value)
      apps.value.unshift(res.data)
      ElMessage.success('应用接入成功')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function saveConfig() {
  if (!configApp.value) return
  
  savingConfig.value = true
  try {
    await appApi.update(configApp.value.id, configForm.value)
    const idx = apps.value.findIndex(a => a.id === configApp.value.id)
    if (idx > -1) {
      apps.value[idx] = { ...apps.value[idx], ...configForm.value }
    }
    ElMessage.success('配置已保存')
    configDialogVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingConfig.value = false
  }
}

function formatTime(time) {
  if (!time) return '-'
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 监听项目变化
watch(() => projectStore.currentProject, () => {
  loadApps()
})

onMounted(() => {
  loadApps()
})
</script>

<style scoped>
.app-manage {
  padding: 24px 32px;
  height: 100%;
  overflow-y: auto;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #184BFA 0%, #3d6afc 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.title-text {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.page-divider {
  color: #cbd5e1;
  font-size: 18px;
}

.page-desc {
  font-size: 14px;
  color: #64748b;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-input {
  width: 280px;
}

:deep(.search-input .el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.platform-filter {
  display: flex;
  background: white;
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.filter-item {
  padding: 8px 20px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.filter-item:hover {
  color: #1e293b;
}

.filter-item.active {
  background: #184BFA;
  color: white;
}

/* 应用列表 */
.app-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.app-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
  border: 1px solid transparent;
}

.app-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #e2e8f0;
}

/* 添加卡片 */
.add-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  border: 2px dashed #e2e8f0;
  background: transparent;
  cursor: pointer;
}

.add-card:hover {
  border-color: #184BFA;
  background: #f8fafc;
}

.add-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
}

.add-card:hover .add-content {
  color: #184BFA;
}

.add-icon {
  font-size: 32px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.add-card:not(:hover) .add-icon {
  animation: none;
}

.add-text {
  font-size: 14px;
}

/* 卡片头部 */
.card-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.app-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-icon {
  font-size: 20px;
  font-weight: 600;
  color: white;
}

.app-info {
  flex: 1;
  min-width: 0;
}

.app-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.app-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.app-name-en {
  font-size: 14px;
  color: #64748b;
}

.platform-tag {
  margin-left: 4px;
  border: none;
}

.platform-tag.android {
  background: #dcfce7;
  color: #16a34a;
}

.platform-tag.ios {
  background: #fef3c7;
  color: #d97706;
}

.platform-icon {
  margin-right: 2px;
}

.package-name {
  font-size: 12px;
  color: #94a3b8;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-btn {
  color: #94a3b8;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 14px;
  letter-spacing: 1px;
}

.more-btn:hover {
  color: #64748b;
}

/* 版本信息 */
.version-info {
  display: flex;
  gap: 32px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: #94a3b8;
}

.info-item .value {
  font-size: 14px;
  color: #1e293b;
}

.info-item .value.version {
  color: #184BFA;
  font-weight: 500;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  align-items: center;
  padding-top: 16px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: #e2e8f0;
}

.config-btn {
  cursor: pointer;
  transition: all 0.2s;
}

.config-btn:hover {
  color: #184BFA;
}

.config-btn .el-icon {
  font-size: 20px;
  color: #94a3b8;
}

.config-btn:hover .el-icon {
  color: #184BFA;
}

/* 配置对话框 */
.config-content {
  padding: 0 8px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.config-info h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #1e293b;
}

.config-info span {
  font-size: 13px;
  color: #64748b;
}

/* 表单 */
.platform-option {
  font-size: 14px;
}

/* 无项目提示 */
.no-project-tip {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.tip-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.no-project-tip p {
  margin: 0;
  font-size: 14px;
}
</style>
