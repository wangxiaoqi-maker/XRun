<template>
  <div class="skills-page">
    <div class="page-header">
      <div class="header-left">
        <div class="page-icon">
          <el-icon :size="24"><MagicStick /></el-icon>
        </div>
        <div class="page-title">
          <h1>Skills 技能</h1>
          <div class="stats">
            <span class="stat-item">共 {{ skills.length }} 个技能</span>
            <span class="stat-item success">{{ enabledCount }} 个已启用</span>
            <span class="stat-item builtin">{{ builtinCount }} 个内置</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="showSearchDialog">
          <el-icon><Search /></el-icon>
          搜索安装
        </el-button>
        <el-button @click="showImportDialog">
          <el-icon><Download /></el-icon>
          从URL导入
        </el-button>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          手动添加
        </el-button>
        <el-button :icon="Refresh" @click="loadSkills" :loading="loading">刷新</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-radio-group v-model="filterCategory" @change="loadSkills">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="tcg_method">测试方法</el-radio-button>
        <el-radio-button label="tcg_case">用例生成</el-radio-button>
        <el-radio-button label="general">通用</el-radio-button>
      </el-radio-group>
    </div>

    <div class="skills-grid" v-loading="loading">
      <div
        v-for="skill in skills"
        :key="skill.id"
        class="skill-card"
        :class="{ disabled: !skill.is_enabled, builtin: skill.is_builtin }"
      >
        <div class="card-header">
          <div class="skill-icon">{{ skill.icon || '⚙' }}</div>
          <div class="skill-info">
            <div class="skill-name">
              {{ skill.name }}
              <el-tag v-if="skill.is_builtin" size="small" type="info">内置</el-tag>
              <el-tag v-if="skill.source_type === 'skills_sh'" size="small" type="warning">skills.sh</el-tag>
              <el-tag v-if="skill.source_type === 'github'" size="small">GitHub</el-tag>
            </div>
            <div class="skill-key">{{ skill.key }}</div>
          </div>
          <el-switch
            v-model="skill.is_enabled"
            @change="toggleSkill(skill)"
            size="small"
          />
        </div>

        <div class="card-desc">{{ skill.description || '暂无描述' }}</div>

        <div class="card-meta">
          <span v-if="skill.category" class="meta-tag">
            <el-icon><Collection /></el-icon>
            {{ categoryLabel(skill.category) }}
          </span>
          <span v-if="skill.files_count" class="meta-tag">
            📎 {{ skill.files_count }} 个脚本
          </span>
          <span v-if="skill.source_repo" class="meta-tag">
            <el-icon><Link /></el-icon>
            {{ skill.source_repo }}
          </span>
          <span v-if="skill.author" class="meta-tag">{{ skill.author }}</span>
        </div>

        <div class="card-footer">
          <span class="create-time">{{ formatDate(skill.created_at) }}</span>
          <div class="actions">
            <el-button text type="primary" @click="viewSkill(skill)" title="查看内容">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button text type="primary" @click="editSkill(skill)" title="编辑">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text type="danger" @click="deleteSkill(skill)" title="删除">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看内容对话框 -->
    <el-dialog v-model="viewDialogVisible" :title="viewingSkill?.name" width="750px">
      <el-tabs v-model="viewActiveTab">
        <el-tab-pane label="主文档" name="doc">
          <div class="skill-content-viewer">
            <pre>{{ viewingSkill?.raw_content || '无内容' }}</pre>
          </div>
        </el-tab-pane>
        <el-tab-pane
          v-for="(file, idx) in (viewingSkill?.files || [])"
          :key="idx"
          :label="file.filename"
          :name="'file_' + idx"
        >
          <div class="file-viewer-header">
            <el-tag size="small" type="info">{{ file.language }}</el-tag>
          </div>
          <div class="skill-content-viewer">
            <pre>{{ file.content }}</pre>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 搜索安装对话框 -->
    <el-dialog v-model="searchDialogVisible" title="搜索 Skills" width="640px">
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="搜索 skills.sh 上的技能..."
          @keyup.enter="doSearch"
          clearable
        >
          <template #append>
            <el-button @click="doSearch" :loading="searching">搜索</el-button>
          </template>
        </el-input>
      </div>
      <div class="search-results" v-loading="searching">
        <div v-if="searchResults.length === 0 && !searching" class="empty-results">
          {{ searchQuery ? '未找到结果' : '输入关键词搜索' }}
        </div>
        <div v-for="item in searchResults" :key="item.url" class="search-item">
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-desc">{{ item.description }}</div>
            <div class="item-meta">
              <span v-if="item.repo">{{ item.repo }}</span>
              <span v-if="item.weekly_installs">{{ item.weekly_installs }} installs/week</span>
            </div>
          </div>
          <el-button
            type="primary"
            size="small"
            @click="installSkill(item)"
            :loading="item._installing"
          >
            安装
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- URL 导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="从URL导入 Skill" width="500px">
      <el-form :model="importForm" label-width="80px">
        <el-form-item label="URL">
          <el-input v-model="importForm.url" placeholder="https://skills.sh/owner/repo/skill 或 GitHub SKILL.md 地址" />
          <div class="form-tip">支持 skills.sh 链接或 GitHub 仓库中 SKILL.md 的原始链接</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="doImport" :loading="importing">导入</el-button>
      </template>
    </el-dialog>

    <!-- 手动添加/编辑对话框 -->
    <el-dialog v-model="editDialogVisible" :title="editingSkill ? '编辑 Skill' : '添加 Skill'" width="720px">
      <el-form :model="form" label-width="80px" ref="formRef">
        <el-form-item label="Key" required>
          <el-input v-model="form.key" placeholder="唯一标识，如 my-test-skill" :disabled="!!editingSkill" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="技能名称" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="Emoji 图标，如 🧪" style="width: 120px" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" placeholder="选择分类">
            <el-option label="通用" value="general" />
            <el-option label="测试方法" value="tcg_method" />
            <el-option label="用例生成" value="tcg_case" />
            <el-option label="文档解析" value="tcg_parse" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="技能描述" />
        </el-form-item>
        <el-form-item label="主文档" required>
          <el-input
            v-model="form.raw_content"
            type="textarea"
            :rows="10"
            placeholder="SKILL.md 内容（Markdown 格式）"
          />
        </el-form-item>

        <!-- 脚本文件管理 -->
        <el-form-item label="脚本文件">
          <div class="files-section">
            <div v-for="(file, idx) in form.files" :key="idx" class="file-block">
              <div class="file-block-header">
                <el-input v-model="file.filename" placeholder="文件名，如 run.sh" style="width: 200px" />
                <el-select v-model="file.language" style="width: 140px">
                  <el-option label="Shell" value="shell" />
                  <el-option label="Python" value="python" />
                  <el-option label="JavaScript" value="javascript" />
                  <el-option label="TypeScript" value="typescript" />
                  <el-option label="YAML" value="yaml" />
                  <el-option label="JSON" value="json" />
                </el-select>
                <el-button type="danger" text @click="removeFile(idx)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
              <el-input
                v-model="file.content"
                type="textarea"
                :rows="8"
                placeholder="脚本内容"
                class="file-content-input"
              />
            </div>
            <el-button @click="addFile" :icon="Plus" size="small">添加脚本文件</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ editingSkill ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick, Plus, Refresh, Search, Download, Edit, Delete, View, Link, Collection
} from '@element-plus/icons-vue'
import { skillApi } from '@/api'

const loading = ref(false)
const skills = ref([])
const filterCategory = ref('')

const enabledCount = computed(() => skills.value.filter(s => s.is_enabled).length)
const builtinCount = computed(() => skills.value.filter(s => s.is_builtin).length)

const CATEGORY_LABELS = {
  general: '通用',
  tcg_method: '测试方法',
  tcg_case: '用例生成',
  tcg_parse: '文档解析',
}

function categoryLabel(cat) {
  return CATEGORY_LABELS[cat] || cat
}

async function loadSkills() {
  loading.value = true
  try {
    const params = { enabled_only: false }
    if (filterCategory.value) params.category = filterCategory.value
    const res = await skillApi.list(params)
    skills.value = res.data?.items || res.data || []
  } catch (e) {
    ElMessage.error('加载技能列表失败')
  } finally {
    loading.value = false
  }
}

// 查看内容
const viewDialogVisible = ref(false)
const viewingSkill = ref(null)
const viewActiveTab = ref('doc')

async function viewSkill(skill) {
  viewActiveTab.value = 'doc'
  try {
    const res = await skillApi.get(skill.id)
    viewingSkill.value = res.data?.data || res.data
    viewDialogVisible.value = true
  } catch {
    viewingSkill.value = skill
    viewDialogVisible.value = true
  }
}

// 搜索安装
const searchDialogVisible = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const searching = ref(false)

function showSearchDialog() {
  searchDialogVisible.value = true
  searchQuery.value = ''
  searchResults.value = []
}

async function doSearch() {
  if (!searchQuery.value.trim()) return
  searching.value = true
  try {
    const res = await skillApi.search({ q: searchQuery.value })
    searchResults.value = (res.data?.items || res.data || []).map(item => ({ ...item, _installing: false }))
  } catch (e) {
    ElMessage.error('搜索失败')
  } finally {
    searching.value = false
  }
}

async function installSkill(item) {
  item._installing = true
  try {
    await skillApi.install({ url: item.url || item.source_url, name: item.name })
    ElMessage.success(`${item.name} 安装成功`)
    loadSkills()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '安装失败')
  } finally {
    item._installing = false
  }
}

// URL 导入
const importDialogVisible = ref(false)
const importForm = ref({ url: '' })
const importing = ref(false)

function showImportDialog() {
  importDialogVisible.value = true
  importForm.value = { url: '' }
}

async function doImport() {
  if (!importForm.value.url.trim()) {
    ElMessage.warning('请输入URL')
    return
  }
  importing.value = true
  try {
    await skillApi.importUrl({ url: importForm.value.url })
    ElMessage.success('导入成功')
    importDialogVisible.value = false
    loadSkills()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

// 手动添加/编辑
const editDialogVisible = ref(false)
const editingSkill = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const defaultForm = () => ({
  key: '', name: '', icon: '⚙', category: 'general',
  description: '', raw_content: '', files: [],
})
const form = ref(defaultForm())

function addFile() {
  form.value.files.push({ filename: '', language: 'shell', content: '' })
}

function removeFile(idx) {
  form.value.files.splice(idx, 1)
}

function showAddDialog() {
  editingSkill.value = null
  form.value = defaultForm()
  editDialogVisible.value = true
}

async function editSkill(skill) {
  editingSkill.value = skill
  form.value = {
    key: skill.key,
    name: skill.name,
    icon: skill.icon || '⚙',
    category: skill.category || 'general',
    description: skill.description || '',
    raw_content: '',
    files: [],
  }
  editDialogVisible.value = true
  try {
    const res = await skillApi.get(skill.id)
    const detail = res.data?.data || res.data
    form.value.raw_content = detail.raw_content || ''
    form.value.files = (detail.files || []).map(f => ({ ...f }))
  } catch {
    ElMessage.warning('获取内容失败，请手动填写')
  }
}

async function submitForm() {
  if (!form.value.key || !form.value.name || !form.value.raw_content) {
    ElMessage.warning('请填写必填项')
    return
  }
  const validFiles = form.value.files.filter(f => f.filename && f.content)
  submitting.value = true
  try {
    const data = {
      key: form.value.key,
      name: form.value.name,
      icon: form.value.icon,
      category: form.value.category,
      description: form.value.description,
      raw_content: form.value.raw_content,
      files: validFiles,
    }
    if (editingSkill.value) {
      await skillApi.update(editingSkill.value.id, data)
      ElMessage.success('更新成功')
    } else {
      data.content = data.raw_content
      await skillApi.create(data)
      ElMessage.success('添加成功')
    }
    editDialogVisible.value = false
    loadSkills()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function toggleSkill(skill) {
  try {
    await skillApi.update(skill.id, { is_enabled: skill.is_enabled })
  } catch {
    skill.is_enabled = !skill.is_enabled
    ElMessage.error('操作失败')
  }
}

async function deleteSkill(skill) {
  await ElMessageBox.confirm(`确定删除技能 "${skill.name}"？`, '提示', { type: 'warning' })
  try {
    await skillApi.delete(skill.id)
    ElMessage.success('删除成功')
    loadSkills()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadSkills()
})
</script>

<style lang="scss" scoped>
.skills-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .page-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .page-title {
    h1 { margin: 0; font-size: 20px; font-weight: 600; color: #1e293b; }
    .stats {
      display: flex; gap: 16px; margin-top: 4px; font-size: 13px; color: #64748b;
      .success { color: #10b981; }
      .builtin { color: #667eea; }
    }
  }

  .header-actions { display: flex; gap: 12px; }
}

.filter-bar {
  margin-bottom: 20px;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.skill-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;

  &:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); transform: translateY(-2px); }
  &.disabled { opacity: 0.5; }
  &.builtin { border-left: 3px solid #667eea; }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;

  .skill-icon {
    width: 44px; height: 44px; border-radius: 10px; background: #f1f5f9;
    display: flex; align-items: center; justify-content: center; font-size: 22px;
  }

  .skill-info {
    flex: 1;
    .skill-name {
      font-size: 15px; font-weight: 600; color: #1e293b;
      display: flex; align-items: center; gap: 6px;
    }
    .skill-key { font-size: 12px; color: #94a3b8; font-family: monospace; }
  }
}

.card-desc {
  font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 12px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.card-meta {
  display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px;

  .meta-tag {
    display: flex; align-items: center; gap: 4px;
    font-size: 12px; color: #94a3b8;
    background: #f8fafc; padding: 2px 8px; border-radius: 4px;
  }
}

.card-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 12px; border-top: 1px solid #f1f5f9;

  .create-time { font-size: 12px; color: #94a3b8; }
  .actions { display: flex; gap: 4px; }
}

.skill-content-viewer {
  pre {
    background: #f8fafc; padding: 16px; border-radius: 8px;
    font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;
    max-height: 500px; overflow-y: auto;
  }
}

.search-box { margin-bottom: 16px; }

.search-results {
  max-height: 400px; overflow-y: auto;

  .empty-results {
    text-align: center; padding: 40px 0; color: #94a3b8;
  }
}

.search-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid #f1f5f9;

  &:hover { background: #f8fafc; }

  .item-info { flex: 1; margin-right: 16px; }
  .item-name { font-size: 14px; font-weight: 600; color: #1e293b; }
  .item-desc { font-size: 13px; color: #64748b; margin-top: 4px; }
  .item-meta {
    display: flex; gap: 12px; margin-top: 4px;
    span { font-size: 12px; color: #94a3b8; }
  }
}

.form-tip { font-size: 12px; color: #94a3b8; margin-top: 4px; }

.files-section {
  width: 100%;
}

.file-block {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: #f8fafc;
}

.file-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.file-content-input {
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}

.file-viewer-header {
  margin-bottom: 8px;
}
</style>
