<template>
  <div class="mirror-page">
    <!-- 左侧：投屏区 -->
    <div class="mirror-panel">
      <DeviceMirror 
        ref="mirrorRef"
        :recording="isRecording"
        @action-recorded="onActionRecorded"
        @screenshot="onScreenshot"
      />
    </div>
    
    <!-- 右侧：操作面板 -->
    <div class="control-panel">
      <!-- 快捷操作 -->
      <div class="panel-section">
        <div class="section-title">快捷操作</div>
        <div class="quick-actions">
          <el-button @click="handleScreenshot" :loading="screenshotLoading">
            <el-icon><Camera /></el-icon>
            截图
          </el-button>
          <el-button 
            :type="isRecording ? 'danger' : 'warning'"
            @click="toggleRecording"
          >
            <el-icon><VideoCamera /></el-icon>
            {{ isRecording ? '停止录制' : '开始录制' }}
          </el-button>
          <el-button @click="handleInstallApp">
            <el-icon><Download /></el-icon>
            安装APK
          </el-button>
        </div>
      </div>
      
      <!-- AI 操作 -->
      <div class="panel-section">
        <div class="section-title">
          <span>AI 智能操作</span>
          <el-tag size="small" type="success">Midscene</el-tag>
        </div>
        <div class="ai-input">
          <el-input
            v-model="aiPrompt"
            type="textarea"
            :rows="3"
            placeholder="用自然语言描述要执行的操作，例如：点击登录按钮，输入用户名123456"
          />
          <el-button 
            type="primary" 
            @click="executeAiAction"
            :loading="aiLoading"
            :disabled="!aiPrompt"
          >
            <el-icon><MagicStick /></el-icon>
            执行
          </el-button>
        </div>
      </div>
      
      <!-- 录制的步骤 -->
      <div class="panel-section flex-1" v-if="recordedSteps.length > 0">
        <div class="section-title">
          <span>录制的步骤 ({{ recordedSteps.length }})</span>
          <div class="title-actions">
            <el-button size="small" text type="primary" @click="saveAsCase">
              保存为用例
            </el-button>
            <el-button size="small" text type="danger" @click="clearSteps">
              清空
            </el-button>
          </div>
        </div>
        <div class="steps-list">
          <div 
            v-for="(step, index) in recordedSteps" 
            :key="index"
            class="step-item"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-type">{{ getStepTypeLabel(step.type) }}</div>
              <div class="step-detail">{{ getStepDetail(step) }}</div>
            </div>
            <el-button 
              size="small" 
              type="danger" 
              text
              @click="removeStep(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 设备信息 -->
      <div class="panel-section">
        <div class="section-title">设备信息</div>
        <div class="device-detail" v-if="currentDevice">
          <div class="detail-row">
            <span class="label">设备名称</span>
            <span class="value">{{ currentDevice.name }}</span>
          </div>
          <div class="detail-row">
            <span class="label">型号</span>
            <span class="value">{{ currentDevice.model }}</span>
          </div>
          <div class="detail-row">
            <span class="label">系统版本</span>
            <span class="value">{{ currentDevice.platform }} {{ currentDevice.os_version }}</span>
          </div>
          <div class="detail-row">
            <span class="label">分辨率</span>
            <span class="value">{{ currentDevice.resolution }}</span>
          </div>
          <div class="detail-row">
            <span class="label">UDID</span>
            <span class="value mono">{{ currentDevice.udid }}</span>
          </div>
        </div>
        <el-empty v-else description="未选择设备" :image-size="60" />
      </div>
    </div>
    
    <!-- 保存用例弹窗 -->
    <el-dialog v-model="saveDialogVisible" title="保存为用例" width="500px">
      <el-form :model="caseForm" label-width="80px">
        <el-form-item label="用例名称" required>
          <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="平台">
          <el-radio-group v-model="caseForm.platform">
            <el-radio value="android">Android</el-radio>
            <el-radio value="ios">iOS</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述">
          <el-input 
            v-model="caseForm.description" 
            type="textarea"
            :rows="3"
            placeholder="用例描述（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveCase" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, VideoCamera, Download, MagicStick, Delete } from '@element-plus/icons-vue'
import DeviceMirror from '@/components/DeviceMirror.vue'
import { deviceApi, caseApi } from '@/api'

const route = useRoute()
const router = useRouter()

const mirrorRef = ref(null)
const isRecording = ref(false)
const recordedSteps = ref([])
const screenshotLoading = ref(false)

// AI 操作
const aiPrompt = ref('')
const aiLoading = ref(false)

// 当前设备
const currentDevice = ref(null)

// 保存用例
const saveDialogVisible = ref(false)
const saving = ref(false)
const caseForm = reactive({
  name: '',
  platform: 'android',
  description: ''
})

const stepTypeLabels = {
  tap: '点击',
  swipe: '滑动',
  input: '输入',
  back: '返回',
  home: 'Home',
  aiTap: 'AI点击',
  aiInput: 'AI输入',
  aiAssert: 'AI断言'
}

function getStepTypeLabel(type) {
  return stepTypeLabels[type] || type
}

function getStepDetail(step) {
  switch (step.type) {
    case 'tap':
      return `坐标 (${step.x}, ${step.y})`
    case 'swipe':
      return `从 (${step.startX}, ${step.startY}) 到 (${step.endX}, ${step.endY})`
    case 'input':
      return `输入: ${step.text}`
    case 'aiTap':
    case 'aiInput':
    case 'aiAssert':
      return step.prompt
    default:
      return step.description || ''
  }
}

function toggleRecording() {
  isRecording.value = !isRecording.value
  if (isRecording.value) {
    ElMessage.success('开始录制，在左侧投屏中操作')
  } else {
    ElMessage.info('录制已停止')
  }
}

function onActionRecorded(action) {
  recordedSteps.value.push(action)
  ElMessage.success(`已记录: ${action.description}`)
}

function onScreenshot(path) {
  ElMessage.success(`截图已保存: ${path}`)
}

function handleScreenshot() {
  mirrorRef.value?.takeScreenshot()
}

function handleInstallApp() {
  ElMessage.info('功能开发中')
}

async function executeAiAction() {
  if (!aiPrompt.value.trim()) return
  
  aiLoading.value = true
  try {
    // TODO: 调用 AI 执行接口
    ElMessage.info('AI 正在分析并执行操作...')
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟添加步骤
    recordedSteps.value.push({
      type: 'aiTap',
      prompt: aiPrompt.value
    })
    
    aiPrompt.value = ''
    ElMessage.success('AI 操作执行成功')
  } catch (e) {
    ElMessage.error('AI 操作执行失败')
  } finally {
    aiLoading.value = false
  }
}

function removeStep(index) {
  recordedSteps.value.splice(index, 1)
}

function clearSteps() {
  recordedSteps.value = []
}

function saveAsCase() {
  if (recordedSteps.value.length === 0) {
    ElMessage.warning('请先录制操作步骤')
    return
  }
  
  caseForm.name = ''
  caseForm.description = ''
  caseForm.platform = currentDevice.value?.platform || 'android'
  saveDialogVisible.value = true
}

async function confirmSaveCase() {
  if (!caseForm.name.trim()) {
    ElMessage.error('请输入用例名称')
    return
  }
  
  saving.value = true
  try {
    // 生成 YAML 内容
    const yamlContent = generateYaml()
    
    await caseApi.create({
      name: caseForm.name,
      platform: caseForm.platform,
      description: caseForm.description,
      yaml_content: yamlContent
    })
    
    ElMessage.success('用例保存成功')
    saveDialogVisible.value = false
    recordedSteps.value = []
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function generateYaml() {
  const steps = recordedSteps.value.map(step => {
    const { description, ...rest } = step
    return rest
  })
  
  return `name: ${caseForm.name}
platform: ${caseForm.platform}
description: ${caseForm.description}
steps:
${steps.map(s => `  - ${JSON.stringify(s)}`).join('\n')}
`
}

async function loadDeviceFromQuery() {
  const udid = route.query.udid
  if (udid) {
    try {
      const res = await deviceApi.list()
      const allDevices = [...(res.data.android || []), ...(res.data.ios || [])]
      currentDevice.value = allDevices.find(d => d.udid === udid)
    } catch (e) {
      console.error(e)
    }
  }
}

onMounted(() => {
  loadDeviceFromQuery()
})
</script>

<style lang="scss" scoped>
.mirror-page {
  height: calc(100vh - var(--header-height) - 40px);
  display: flex;
  gap: 20px;
}

.mirror-panel {
  width: 400px;
  flex-shrink: 0;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 未连接时垂直居中 */
  align-items: center; /* 水平居中 */
}

.control-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.panel-section {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 16px;
  
  &.flex-1 {
    flex: 1;
    min-height: 200px;
    display: flex;
    flex-direction: column;
  }
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  .el-tag {
    margin-left: 8px;
  }
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.ai-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .el-button {
    align-self: flex-end;
  }
}

.steps-list {
  flex: 1;
  overflow-y: auto;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: var(--bg-color);
  border-radius: 8px;
  margin-bottom: 8px;
  
  .step-number {
    width: 24px;
    height: 24px;
    background: var(--primary-color);
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
    flex-shrink: 0;
  }
  
  .step-content {
    flex: 1;
    min-width: 0;
    
    .step-type {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .step-detail {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.device-detail {
  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-color);
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      color: var(--text-muted);
      font-size: 13px;
    }
    
    .value {
      color: var(--text-primary);
      font-size: 13px;
      
      &.mono {
        font-family: monospace;
        font-size: 11px;
      }
    }
  }
}
</style>






