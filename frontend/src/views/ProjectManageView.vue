<template>
  <div class="project-manage">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">项目管理</h1>
        <span class="page-desc">管理测试项目，创建和配置项目信息</span>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
    </div>
    
    <div class="project-list" v-loading="loading">
      <div 
        v-for="project in projects" 
        :key="project.id" 
        class="project-card"
        :class="{ 'is-inactive': !project.is_active }"
      >
        <div class="card-header">
          <span class="project-icon" :style="{ background: project.color + '20' }">
            {{ project.icon }}
          </span>
          <div class="project-info">
            <h3 class="project-name">{{ project.name }}</h3>
          </div>
          <el-dropdown trigger="click" @command="cmd => handleCommand(cmd, project)">
            <el-button text size="small">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">编辑</el-dropdown-item>
                <el-dropdown-item command="members">成员管理</el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <span style="color: #f56c6c">删除项目</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <p class="project-desc">{{ project.description || '暂无描述' }}</p>
        <div class="card-footer">
          <span class="create-time">创建于 {{ formatTime(project.created_at) }}</span>
          <el-tag v-if="!project.is_active" type="info" size="small">已禁用</el-tag>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="!loading && projects.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Folder /></el-icon>
        <p>暂无项目</p>
        <el-button type="primary" @click="openCreateDialog">创建第一个项目</el-button>
      </div>
    </div>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="480px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目图标">
          <div class="icon-picker">
            <span 
              v-for="emoji in emojiList" 
              :key="emoji" 
              class="emoji-item"
              :class="{ active: form.icon === emoji }"
              @click="form.icon = emoji"
            >{{ emoji }}</span>
          </div>
        </el-form-item>
        <el-form-item label="主题色">
          <div class="color-picker">
            <span 
              v-for="color in colorList" 
              :key="color" 
              class="color-item"
              :class="{ active: form.color === color }"
              :style="{ background: color }"
              @click="form.color = color"
            ></span>
          </div>
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入项目描述（可选）" 
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 成员管理对话框 -->
    <el-dialog 
      v-model="memberDialogVisible" 
      title="成员管理"
      width="600px"
    >
      <div class="member-dialog-content">
        <div class="member-header">
          <span class="member-count">共 {{ members.length }} 名成员</span>
          <el-button size="small" @click="showAddMember = true">
            <el-icon><Plus /></el-icon>
            添加成员
          </el-button>
        </div>
        
        <!-- 添加成员区域 -->
        <div v-if="showAddMember" class="add-member-area">
          <el-select 
            v-model="newMember.userId" 
            placeholder="选择用户"
            filterable
            style="flex: 1"
          >
            <el-option 
              v-for="user in availableUsers" 
              :key="user.id"
              :label="`${user.nickname || user.username} (${user.email})`"
              :value="user.id"
            />
          </el-select>
          <el-select v-model="newMember.role" style="width: 120px">
            <el-option label="成员" value="member" />
            <el-option label="管理员" value="admin" />
            <el-option label="负责人" value="owner" />
          </el-select>
          <el-button type="primary" :loading="addingMember" @click="handleAddMember">添加</el-button>
          <el-button @click="showAddMember = false">取消</el-button>
        </div>
        
        <!-- 成员列表 -->
        <div class="member-list" v-loading="loadingMembers">
          <div v-for="member in members" :key="member.id" class="member-item">
            <div class="member-info">
              <span class="member-name">{{ member.user?.nickname || member.user?.username }}</span>
              <span class="member-email">{{ member.user?.email }}</span>
            </div>
            <div class="member-actions">
              <el-select 
                v-model="member.role" 
                size="small"
                @change="updateMemberRole(member)"
              >
                <el-option label="成员" value="member" />
                <el-option label="管理员" value="admin" />
                <el-option label="负责人" value="owner" />
              </el-select>
              <el-button 
                type="danger" 
                text 
                size="small"
                @click="removeMember(member)"
              >
                移除
              </el-button>
            </div>
          </div>
          
          <div v-if="!loadingMembers && members.length === 0" class="empty-members">
            暂无成员
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, Folder } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { projectApi } from '@/api'

const route = useRoute()
const projectStore = useProjectStore()

const loading = ref(false)
const projects = ref([])
const dialogVisible = ref(false)
const editingProject = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 成员管理
const memberDialogVisible = ref(false)
const currentProject = ref(null)
const members = ref([])
const loadingMembers = ref(false)
const showAddMember = ref(false)
const availableUsers = ref([])
const addingMember = ref(false)
const newMember = ref({ userId: '', role: 'member' })

const form = ref({
  name: '',
  icon: '📁',
  color: '#184BFA',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

const emojiList = ['📁', '🚀', '💼', '🎯', '⭐', '🔥', '💡', '🎨', '📱', '🖥️', '🌐', '🔧']
const colorList = ['#184BFA', '#8b5cf6', '#ec4899', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#64748b']

async function loadProjects() {
  loading.value = true
  try {
    const res = await projectApi.list()
    projects.value = res.data
  } catch (e) {
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingProject.value = null
  form.value = {
    name: '',
    icon: '📁',
    color: '#184BFA',
    description: ''
  }
  dialogVisible.value = true
}

function handleCommand(cmd, project) {
  switch (cmd) {
    case 'edit':
      editingProject.value = project
      form.value = {
        name: project.name,
        icon: project.icon,
        color: project.color,
        description: project.description || ''
      }
      dialogVisible.value = true
      break
    case 'members':
      openMemberDialog(project)
      break
    case 'delete':
      ElMessageBox.confirm(`确定要删除项目「${project.name}」吗？`, '删除确认', {
        type: 'warning'
      }).then(async () => {
        await projectStore.deleteProject(project.id)
        projects.value = projects.value.filter(p => p.id !== project.id)
        ElMessage.success('项目已删除')
      }).catch(() => {})
      break
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  
  submitting.value = true
  try {
    if (editingProject.value) {
      await projectStore.updateProject(editingProject.value.id, {
        name: form.value.name,
        icon: form.value.icon,
        color: form.value.color,
        description: form.value.description
      })
      // 更新列表
      const idx = projects.value.findIndex(p => p.id === editingProject.value.id)
      if (idx > -1) {
        projects.value[idx] = { ...projects.value[idx], ...form.value }
      }
      ElMessage.success('项目已更新')
    } else {
      const newProject = await projectStore.createProject(form.value)
      projects.value.unshift(newProject)
      ElMessage.success('项目创建成功')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 成员管理
async function openMemberDialog(project) {
  currentProject.value = project
  memberDialogVisible.value = true
  showAddMember.value = false
  newMember.value = { userId: '', role: 'member' }
  await loadMembers()
}

async function loadMembers() {
  if (!currentProject.value) return
  loadingMembers.value = true
  try {
    const res = await projectApi.listMembers(currentProject.value.id)
    members.value = res.data
  } catch (e) {
    ElMessage.error('加载成员列表失败')
  } finally {
    loadingMembers.value = false
  }
}

async function loadAvailableUsers() {
  if (!currentProject.value) return
  try {
    const res = await projectApi.getAvailableUsers(currentProject.value.id)
    availableUsers.value = res.data
  } catch (e) {
    console.error('加载可用用户失败', e)
  }
}

// 显示添加成员时加载可用用户
import { watch } from 'vue'
watch(showAddMember, (val) => {
  if (val) {
    loadAvailableUsers()
  }
})

async function handleAddMember() {
  if (!newMember.value.userId) {
    ElMessage.warning('请选择用户')
    return
  }
  
  addingMember.value = true
  try {
    await projectApi.addMember(currentProject.value.id, newMember.value.userId, newMember.value.role)
    ElMessage.success('成员添加成功')
    showAddMember.value = false
    newMember.value = { userId: '', role: 'member' }
    await loadMembers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    addingMember.value = false
  }
}

async function updateMemberRole(member) {
  try {
    await projectApi.updateMemberRole(currentProject.value.id, member.user?.id, member.role)
    ElMessage.success('角色已更新')
  } catch (e) {
    ElMessage.error('更新失败')
    await loadMembers()
  }
}

async function removeMember(member) {
  try {
    await ElMessageBox.confirm(`确定要移除成员「${member.user?.nickname || member.user?.username}」吗？`, '确认移除')
    await projectApi.removeMember(currentProject.value.id, member.user?.id)
    ElMessage.success('成员已移除')
    await loadMembers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadProjects()
  if (route.query.action === 'create') {
    openCreateDialog()
  }
})
</script>

<style scoped>
.project-manage {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  background: #f8fafc;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.page-desc {
  font-size: 14px;
  color: #64748b;
}

.project-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.project-card.is-inactive {
  opacity: 0.6;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.project-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.project-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.create-time {
  font-size: 12px;
  color: #94a3b8;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0 0 20px 0;
  font-size: 14px;
}

/* 图标选择器 */
.icon-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.emoji-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.emoji-item:hover {
  border-color: #94a3b8;
}

.emoji-item.active {
  border-color: #184BFA;
  background: #eef2ff;
}

/* 颜色选择器 */
.color-picker {
  display: flex;
  gap: 8px;
}

.color-item {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.color-item:hover {
  transform: scale(1.1);
}

.color-item.active {
  border-color: #1e293b;
  box-shadow: 0 0 0 2px white, 0 0 0 4px currentColor;
}

/* 成员管理 */
.member-dialog-content {
  min-height: 300px;
}

.member-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.member-count {
  font-size: 14px;
  color: #64748b;
}

.add-member-area {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.member-email {
  font-size: 12px;
  color: #94a3b8;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.empty-members {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 14px;
}
</style>
