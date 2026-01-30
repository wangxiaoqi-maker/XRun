<template>
  <div class="providers-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-left">
        <div class="page-icon">
          <el-icon :size="24"><Connection /></el-icon>
        </div>
        <div class="page-title">
          <h1>模型供应商</h1>
          <div class="stats">
            <span class="stat-item">共 {{ providers.length }} 个供应商</span>
            <span class="stat-item success">✓ {{ enabledCount }} 个已启用</span>
            <span class="stat-item disabled" v-if="disabledCount > 0">× {{ disabledCount }} 个已禁用</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="$router.push('/llm/usage')">
          <el-icon><DataAnalysis /></el-icon>
          用量统计
        </el-button>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加供应商
        </el-button>
        <el-button :icon="Refresh" @click="loadProviders" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- 供应商列表 -->
    <div class="providers-grid" v-loading="loading">
      <div 
        v-for="provider in providers" 
        :key="provider.id" 
        class="provider-card"
        :class="{ disabled: provider.status === 'disabled' }"
      >
        <div class="card-header">
          <div class="provider-icon">
            <img v-if="provider.icon" :src="provider.icon" :alt="provider.name" />
            <el-icon v-else :size="28"><Cpu /></el-icon>
          </div>
          <div class="provider-info">
            <div class="provider-name">
              {{ provider.name }}
              <span class="status-dot" :class="provider.status"></span>
            </div>
            <div class="provider-code">{{ provider.code }}</div>
          </div>
        </div>

        <div class="card-url">
          <el-icon><Link /></el-icon>
          <span>{{ provider.base_url }}</span>
        </div>

        <div class="card-stats">
          <div class="stat">
            <span class="value">{{ formatNumber(provider.total_requests) }}</span>
            <span class="label">请求数</span>
          </div>
          <div class="stat">
            <span class="value">{{ formatTokens(provider.total_tokens) }}</span>
            <span class="label">Tokens</span>
          </div>
          <div class="stat">
            <span class="value success">{{ provider.success_rate }}%</span>
            <span class="label">成功率</span>
          </div>
          <div class="stat">
            <span class="value">{{ provider.avg_latency?.toFixed(1) || 0 }}s</span>
            <span class="label">延迟</span>
          </div>
        </div>

        <div class="card-footer">
          <span class="create-time">{{ formatDate(provider.created_at) }}</span>
          <div class="actions">
            <el-button text type="primary" @click="editProvider(provider)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text @click="manageModels(provider)">
              <el-icon><Setting /></el-icon>
            </el-button>
            <el-button text type="danger" @click="deleteProvider(provider)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 添加卡片 -->
      <div class="provider-card add-card" @click="showAddDialog">
        <el-icon :size="40"><Plus /></el-icon>
        <span>添加供应商</span>
      </div>
    </div>

    <!-- 添加/编辑对话框 - 简化版 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="editingProvider ? '编辑供应商' : '添加供应商'"
      width="480px"
    >
      <el-form :model="form" label-width="90px" :rules="rules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：豆包、通义千问、OpenAI" />
        </el-form-item>
        <el-form-item label="API 地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="如：https://ark.cn-beijing.volces.com/api/v3" />
          <div class="form-tip">从供应商文档获取 base_url</div>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="从供应商控制台获取" />
        </el-form-item>
        <el-form-item label="状态" v-if="editingProvider">
          <el-switch v-model="form.enabled" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ editingProvider ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模型管理对话框 -->
    <el-dialog v-model="modelsDialogVisible" :title="`${currentProvider?.name} - 模型管理`" width="700px">
      <div class="models-dialog">
        <div class="models-header">
          <el-button type="primary" size="small" @click="showAddModelDialog">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
        <el-table :data="currentModels" v-loading="loadingModels">
          <el-table-column prop="name" label="模型名称" />
          <el-table-column prop="model_id" label="模型ID" />
          <el-table-column prop="model_type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.model_type === 'vision' ? 'warning' : ''">
                {{ row.model_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="supports_vision" label="视觉" width="60">
            <template #default="{ row }">
              <el-icon v-if="row.supports_vision" color="#10b981"><Check /></el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'enabled' ? 'success' : 'info'" size="small">
                {{ row.status === 'enabled' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="editModel(row)">编辑</el-button>
              <el-button text type="danger" size="small" @click="deleteModel(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 添加/编辑模型对话框 - 简化版 -->
    <el-dialog v-model="modelDialogVisible" :title="editingModel ? '编辑模型' : '添加模型'" width="420px">
      <el-form :model="modelForm" label-width="90px" ref="modelFormRef">
        <el-form-item label="模型ID" required>
          <el-input v-model="modelForm.model_id" placeholder="如：doubao-1-5-thinking-vision-pro-250428" />
          <div class="form-tip">从供应商文档获取，如 gpt-4、qwen-vl-max</div>
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="modelForm.name" placeholder="可选，如：豆包视觉Pro" />
        </el-form-item>
        <el-form-item label="支持视觉">
          <el-switch v-model="modelForm.supports_vision" />
          <span class="switch-tip">开启后可用于 AI 页面分析</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitModelForm" :loading="submittingModel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Connection, Plus, Refresh, Edit, Delete, Setting, Link, Cpu, DataAnalysis, Check
} from '@element-plus/icons-vue'
import { llmApi } from '@/api'

const loading = ref(false)
const providers = ref([])
const dialogVisible = ref(false)
const editingProvider = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  name: '',
  code: '',
  base_url: '',
  api_key: '',
  icon: '',
  description: '',
  enabled: true
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  base_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }]
}

// 模型管理
const modelsDialogVisible = ref(false)
const currentProvider = ref(null)
const currentModels = ref([])
const loadingModels = ref(false)
const modelDialogVisible = ref(false)
const editingModel = ref(null)
const submittingModel = ref(false)
const modelFormRef = ref(null)

const modelForm = ref({
  name: '',
  model_id: '',
  model_type: 'chat',
  max_tokens: 4096,
  supports_vision: false,
  supports_function_call: false
})

const enabledCount = computed(() => providers.value.filter(p => p.status === 'enabled').length)
const disabledCount = computed(() => providers.value.filter(p => p.status === 'disabled').length)

async function loadProviders() {
  loading.value = true
  try {
    const res = await llmApi.listProviders(true)
    providers.value = res.data.providers || []
  } catch (e) {
    ElMessage.error('加载供应商列表失败')
  } finally {
    loading.value = false
  }
}

function showAddDialog() {
  editingProvider.value = null
  form.value = { name: '', code: '', base_url: '', api_key: '', icon: '', description: '', enabled: true }
  dialogVisible.value = true
}

async function editProvider(provider) {
  editingProvider.value = provider
  const res = await llmApi.getProvider(provider.id, true)
  form.value = {
    name: res.data.name,
    code: res.data.code,
    base_url: res.data.base_url,
    api_key: res.data.api_key || '',
    icon: res.data.icon || '',
    description: res.data.description || '',
    enabled: res.data.status === 'enabled'
  }
  dialogVisible.value = true
}

async function submitForm() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    // 自动生成 code（取名称的拼音或简写）
    const code = form.value.code || form.value.name.toLowerCase().replace(/[^a-z0-9]/g, '') || `provider_${Date.now()}`
    
    const data = {
      name: form.value.name,
      code: code,
      base_url: form.value.base_url,
      api_key: form.value.api_key || undefined,
      status: form.value.enabled ? 'enabled' : 'disabled'
    }
    
    if (editingProvider.value) {
      await llmApi.updateProvider(editingProvider.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await llmApi.createProvider(data)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadProviders()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function deleteProvider(provider) {
  await ElMessageBox.confirm(`确定删除供应商 ${provider.name}？`, '提示', { type: 'warning' })
  try {
    await llmApi.deleteProvider(provider.id)
    ElMessage.success('删除成功')
    loadProviders()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function manageModels(provider) {
  currentProvider.value = provider
  modelsDialogVisible.value = true
  loadingModels.value = true
  try {
    const res = await llmApi.listModels({ provider_id: provider.id, include_disabled: true })
    currentModels.value = res.data.models || []
  } finally {
    loadingModels.value = false
  }
}

function showAddModelDialog() {
  editingModel.value = null
  modelForm.value = {
    name: '', model_id: '', supports_vision: false
  }
  modelDialogVisible.value = true
}

function editModel(model) {
  editingModel.value = model
  modelForm.value = {
    name: model.name || '',
    model_id: model.model_id || '',
    supports_vision: model.supports_vision || false
  }
  modelDialogVisible.value = true
}

async function submitModelForm() {
  if (!modelForm.value.model_id) {
    ElMessage.warning('请输入模型ID')
    return
  }
  
  submittingModel.value = true
  try {
    const data = {
      provider_id: currentProvider.value.id,
      model_id: modelForm.value.model_id,
      name: modelForm.value.name || modelForm.value.model_id,  // 如果没填名称，用 model_id
      model_type: modelForm.value.supports_vision ? 'vision' : 'chat',
      supports_vision: modelForm.value.supports_vision,
      supports_function_call: true,  // 默认支持
      max_tokens: 4096  // 默认值
    }
    
    if (editingModel.value) {
      await llmApi.updateModel(editingModel.value.id, data)
    } else {
      await llmApi.createModel(data)
    }
    ElMessage.success('保存成功')
    modelDialogVisible.value = false
    manageModels(currentProvider.value)
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    submittingModel.value = false
  }
}

async function deleteModel(model) {
  await ElMessageBox.confirm(`确定删除模型 ${model.name}？`, '提示', { type: 'warning' })
  try {
    await llmApi.deleteModel(model.id)
    ElMessage.success('删除成功')
    manageModels(currentProvider.value)
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function formatTokens(num) {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadProviders()
})
</script>

<style lang="scss" scoped>
.providers-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .page-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }
  
  .page-title {
    h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
      color: #1e293b;
    }
    
    .stats {
      display: flex;
      gap: 16px;
      margin-top: 4px;
      font-size: 13px;
      color: #64748b;
      
      .success { color: #10b981; }
      .disabled { color: #94a3b8; }
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.providers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.provider-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  
  &.disabled {
    opacity: 0.6;
  }
  
  &.add-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    border: 2px dashed #e2e8f0;
    color: #94a3b8;
    cursor: pointer;
    
    &:hover {
      border-color: #667eea;
      color: #667eea;
      background: #f8faff;
    }
    
    span {
      margin-top: 8px;
      font-size: 14px;
    }
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  
  .provider-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    background: #f1f5f9;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      width: 32px;
      height: 32px;
      object-fit: contain;
    }
  }
  
  .provider-info {
    flex: 1;
    
    .provider-name {
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .provider-code {
      font-size: 12px;
      color: #94a3b8;
    }
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  
  &.disabled {
    background: #94a3b8;
  }
}

.card-url {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #64748b;
  
  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.card-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 16px;
  
  .stat {
    text-align: center;
    
    .value {
      display: block;
      font-size: 16px;
      font-weight: 600;
      color: #1e293b;
      
      &.success { color: #10b981; }
    }
    
    .label {
      font-size: 11px;
      color: #94a3b8;
    }
  }
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
  
  .create-time {
    font-size: 12px;
    color: #94a3b8;
  }
  
  .actions {
    display: flex;
    gap: 4px;
  }
}

.models-dialog {
  .models-header {
    margin-bottom: 16px;
  }
}

.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.switch-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 8px;
}
</style>
