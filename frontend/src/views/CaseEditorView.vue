<template>
  <div class="case-editor">
    <div class="editor-header">
      <h1>{{ isNew ? '新建用例' : '编辑用例' }}</h1>
      <div class="header-actions">
        <el-button @click="$router.push('/cases')">取消</el-button>
        <el-button type="primary" @click="saveCase" :loading="saving">保存</el-button>
      </div>
    </div>
    
    <div class="editor-content">
      <!-- 左侧：手机投屏 -->
      <div class="mirror-panel">
        <DeviceMirror 
          ref="mirrorRef"
          :recording="isRecording"
          @action-recorded="onActionRecorded"
          @screenshot="onScreenshot"
        />
      </div>
      
      <!-- 右侧：用例编辑 -->
      <div class="edit-panel">
        <!-- 基本信息 -->
        <el-card class="info-card">
          <template #header>
            <span>基本信息</span>
          </template>
          
          <el-form :model="caseForm" label-width="80px" size="small">
            <el-form-item label="用例名称">
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
                :rows="2"
                placeholder="用例描述（可选）" 
              />
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 步骤编辑 -->
        <el-card class="steps-card">
          <template #header>
            <div class="steps-header">
              <span>测试步骤</span>
              <div class="steps-actions">
                <el-button size="small" type="success" @click="addStep">
                  <el-icon><Plus /></el-icon> 添加步骤
                </el-button>
                <el-button 
                  size="small" 
                  :type="isRecording ? 'danger' : 'warning'"
                  @click="toggleRecording"
                >
                  <el-icon><VideoCamera /></el-icon>
                  {{ isRecording ? '停止录制' : '录制操作' }}
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="steps-list">
            <draggable 
              v-model="caseForm.steps" 
              item-key="id"
              handle=".drag-handle"
              animation="200"
            >
              <template #item="{ element, index }">
                <div class="step-item" :class="{ 'is-ai': element.type.startsWith('ai') }">
                  <div class="drag-handle">
                    <el-icon><Rank /></el-icon>
                  </div>
                  
                  <div class="step-number">{{ index + 1 }}</div>
                  
                  <div class="step-content">
                    <!-- 步骤类型选择 -->
                    <el-select v-model="element.type" size="small" style="width: 120px;" @change="onStepTypeChange(element)">
                      <el-option-group label="AI 智能操作">
                        <el-option value="aiTap" label="AI 点击" />
                        <el-option value="aiInput" label="AI 输入" />
                        <el-option value="aiAssert" label="AI 断言" />
                        <el-option value="aiWait" label="AI 等待" />
                        <el-option value="aiSwipe" label="AI 滑动" />
                        <el-option value="aiQuery" label="AI 查询" />
                      </el-option-group>
                      <el-option-group label="基础操作">
                        <el-option value="tap" label="坐标点击" />
                        <el-option value="swipe" label="滑动" />
                        <el-option value="input" label="输入文本" />
                        <el-option value="back" label="返回" />
                        <el-option value="home" label="Home 键" />
                        <el-option value="sleep" label="等待" />
                        <el-option value="launch" label="启动应用" />
                        <el-option value="screenshot" label="截图" />
                      </el-option-group>
                    </el-select>
                    
                    <!-- 根据类型显示不同的输入 -->
                    <template v-if="element.type === 'aiTap'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="描述要点击的元素，如：登录按钮" 
                        style="flex: 1;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'aiInput'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="描述输入框，如：用户名输入框" 
                        style="width: 180px;"
                      />
                      <el-input 
                        v-model="element.text" 
                        size="small" 
                        placeholder="要输入的内容" 
                        style="flex: 1;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'aiAssert'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="描述断言，如：页面显示登录成功" 
                        style="flex: 1;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'aiWait'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="等待元素出现，如：加载完成" 
                        style="flex: 1;"
                      />
                      <el-input-number 
                        v-model="element.timeout" 
                        size="small" 
                        :min="1000" 
                        :step="1000"
                        :max="60000"
                        placeholder="超时(毫秒)"
                        style="width: 130px;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'aiSwipe'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="描述元素或区域" 
                        style="width: 180px;"
                      />
                      <el-select v-model="element.direction" size="small" style="width: 100px;">
                        <el-option value="up" label="向上" />
                        <el-option value="down" label="向下" />
                        <el-option value="left" label="向左" />
                        <el-option value="right" label="向右" />
                      </el-select>
                    </template>
                    
                    <template v-else-if="element.type === 'aiQuery'">
                      <el-input 
                        v-model="element.prompt" 
                        size="small" 
                        placeholder="查询内容，如：当前页面标题" 
                        style="flex: 1;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'tap'">
                      <el-input-number 
                        v-model="element.x" 
                        size="small" 
                        :min="0" 
                        placeholder="X" 
                        style="width: 100px;"
                      />
                      <el-input-number 
                        v-model="element.y" 
                        size="small" 
                        :min="0" 
                        placeholder="Y" 
                        style="width: 100px;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'swipe'">
                      <span class="coord-label">起点:</span>
                      <el-input-number v-model="element.startX" size="small" :min="0" style="width: 80px;" />
                      <el-input-number v-model="element.startY" size="small" :min="0" style="width: 80px;" />
                      <span class="coord-label">终点:</span>
                      <el-input-number v-model="element.endX" size="small" :min="0" style="width: 80px;" />
                      <el-input-number v-model="element.endY" size="small" :min="0" style="width: 80px;" />
                    </template>
                    
                    <template v-else-if="element.type === 'input'">
                      <el-input 
                        v-model="element.text" 
                        size="small" 
                        placeholder="输入的文本内容" 
                        style="flex: 1;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'sleep'">
                      <el-input-number 
                        v-model="element.duration" 
                        size="small" 
                        :min="100" 
                        :step="500"
                        placeholder="毫秒" 
                        style="width: 120px;"
                      />
                      <span class="unit">毫秒</span>
                    </template>
                    
                    <template v-else-if="element.type === 'launch'">
                      <el-input 
                        v-model="element.package" 
                        size="small" 
                        :placeholder="caseForm.platform === 'ios' ? 'Bundle ID' : '包名'" 
                        style="flex: 1;"
                      />
                      <el-input 
                        v-if="caseForm.platform === 'android'"
                        v-model="element.activity" 
                        size="small" 
                        placeholder="Activity（可选）" 
                        style="width: 180px;"
                      />
                    </template>
                    
                    <template v-else-if="element.type === 'screenshot'">
                      <el-input 
                        v-model="element.description" 
                        size="small" 
                        placeholder="截图描述（可选）" 
                        style="flex: 1;"
                      />
                    </template>
                  </div>
                  
                  <div class="step-actions">
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
              </template>
            </draggable>
            
            <div v-if="caseForm.steps.length === 0" class="no-steps">
              <el-empty description="暂无步骤，点击上方按钮添加" />
            </div>
          </div>
        </el-card>
        
        <!-- YAML 预览 -->
        <el-card class="yaml-card">
          <template #header>
            <div class="yaml-header">
              <span>YAML 预览</span>
              <el-switch 
                v-model="showYamlEditor" 
                active-text="编辑模式" 
                inactive-text="预览模式"
                size="small"
              />
            </div>
          </template>
          
          <div class="yaml-content">
            <el-input
              v-if="showYamlEditor"
              v-model="yamlContent"
              type="textarea"
              :rows="12"
              class="yaml-editor"
              @blur="parseYaml"
            />
            <pre v-else class="yaml-preview">{{ generatedYaml }}</pre>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Rank, VideoCamera } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import YAML from 'js-yaml'
import DeviceMirror from '../components/DeviceMirror.vue'
import { caseApi } from '../api'

const route = useRoute()
const router = useRouter()

const isNew = computed(() => !route.params.id)
const saving = ref(false)
const isRecording = ref(false)
const showYamlEditor = ref(false)
const yamlContent = ref('')
const mirrorRef = ref(null)

const caseForm = ref({
  name: '',
  platform: 'android',
  description: '',
  steps: []
})

let stepIdCounter = 1

onMounted(async () => {
  if (!isNew.value) {
    await loadCase()
  }
})

async function loadCase() {
  try {
    const res = await caseApi.get(route.params.id)
    const data = res.data
    
    caseForm.value.name = data.name
    caseForm.value.platform = data.platform
    caseForm.value.description = data.description || ''
    
    // 解析 YAML 内容
    if (data.yaml_content) {
      yamlContent.value = data.yaml_content
      parseYamlToSteps(data.yaml_content)
    }
  } catch (e) {
    ElMessage.error('加载用例失败')
    console.error(e)
  }
}

function parseYamlToSteps(content) {
  try {
    const parsed = YAML.load(content)
    if (parsed && parsed.steps) {
      caseForm.value.steps = parsed.steps.map(step => ({
        id: stepIdCounter++,
        ...step
      }))
    }
  } catch (e) {
    console.error('YAML 解析失败', e)
  }
}

const generatedYaml = computed(() => {
  const yamlObj = {
    name: caseForm.value.name,
    platform: caseForm.value.platform,
    description: caseForm.value.description,
    steps: caseForm.value.steps.map(step => {
      const { id, ...rest } = step
      return rest
    })
  }
  return YAML.dump(yamlObj)
})

watch(generatedYaml, (val) => {
  if (!showYamlEditor.value) {
    yamlContent.value = val
  }
})

function parseYaml() {
  try {
    const parsed = YAML.load(yamlContent.value)
    if (parsed.name) caseForm.value.name = parsed.name
    if (parsed.platform) caseForm.value.platform = parsed.platform
    if (parsed.description) caseForm.value.description = parsed.description
    if (parsed.steps) {
      caseForm.value.steps = parsed.steps.map(step => ({
        id: stepIdCounter++,
        ...step
      }))
    }
    ElMessage.success('YAML 解析成功')
  } catch (e) {
    ElMessage.error('YAML 格式错误')
  }
}

function addStep() {
  caseForm.value.steps.push({
    id: stepIdCounter++,
    type: 'aiTap',
    prompt: ''
  })
}

function removeStep(index) {
  caseForm.value.steps.splice(index, 1)
}

function onStepTypeChange(step) {
  // 清除之前的字段，保留基本字段
  const { id, type } = step
  Object.keys(step).forEach(key => {
    if (key !== 'id' && key !== 'type') {
      delete step[key]
    }
  })
  
  // 根据类型初始化字段
  switch (type) {
    case 'aiTap':
    case 'aiAssert':
    case 'aiQuery':
      step.prompt = ''
      break
    case 'aiWait':
      step.prompt = ''
      step.timeout = 10000
      break
    case 'aiInput':
      step.prompt = ''
      step.text = ''
      break
    case 'aiSwipe':
      step.prompt = ''
      step.direction = 'up'
      break
    case 'tap':
      step.x = 0
      step.y = 0
      break
    case 'swipe':
      step.startX = 0
      step.startY = 0
      step.endX = 0
      step.endY = 0
      break
    case 'input':
      step.text = ''
      break
    case 'sleep':
      step.duration = 1000
      break
    case 'launch':
      step.package = ''
      step.activity = ''
      break
    case 'screenshot':
      step.description = ''
      break
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
  // 将操作转为步骤
  const step = {
    id: stepIdCounter++,
    type: action.type,
    ...action
  }
  
  // 转换类型
  if (action.type === 'tap') {
    step.x = action.x
    step.y = action.y
  } else if (action.type === 'swipe') {
    step.startX = action.startX
    step.startY = action.startY
    step.endX = action.endX
    step.endY = action.endY
  } else if (action.type === 'input') {
    step.text = action.text
  }
  
  delete step.description
  caseForm.value.steps.push(step)
  
  ElMessage.success(`已添加步骤: ${action.description}`)
}

function onScreenshot(path) {
  ElMessage.success(`截图已保存: ${path}`)
}

async function saveCase() {
  if (!caseForm.value.name.trim()) {
    ElMessage.error('请输入用例名称')
    return
  }
  
  if (caseForm.value.steps.length === 0) {
    ElMessage.error('请添加至少一个步骤')
    return
  }
  
  saving.value = true
  
  try {
    const data = {
      name: caseForm.value.name,
      platform: caseForm.value.platform,
      description: caseForm.value.description,
      yaml_content: generatedYaml.value
    }
    
    if (isNew.value) {
      await caseApi.create(data)
      ElMessage.success('用例创建成功')
    } else {
      await caseApi.update(route.params.id, data)
      ElMessage.success('用例保存成功')
    }
    
    router.push('/cases')
  } catch (e) {
    ElMessage.error('保存失败')
    console.error(e)
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
.case-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #1a1a2e;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  h1 {
    font-size: 20px;
    margin: 0;
    color: #fff;
  }
}

.editor-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.mirror-panel {
  width: 360px;
  flex-shrink: 0;
}

.edit-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.info-card {
  background: #16213e;
  
  :deep(.el-card__header) {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
}

.steps-card {
  flex: 1;
  background: #16213e;
  display: flex;
  flex-direction: column;
  
  :deep(.el-card__body) {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.steps-actions {
  display: flex;
  gap: 8px;
}

.steps-list {
  min-height: 200px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
  }
  
  &.is-ai {
    border-left: 3px solid #409eff;
    background: rgba(64, 158, 255, 0.1);
  }
}

.drag-handle {
  cursor: move;
  color: rgba(255, 255, 255, 0.3);
  
  &:hover {
    color: rgba(255, 255, 255, 0.6);
  }
}

.step-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
}

.step-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.coord-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.no-steps {
  padding: 40px;
}

.yaml-card {
  background: #16213e;
  
  :deep(.el-card__body) {
    padding: 0;
  }
}

.yaml-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.yaml-content {
  max-height: 300px;
  overflow: auto;
}

.yaml-preview {
  margin: 0;
  padding: 16px;
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #a3e635;
  white-space: pre-wrap;
  word-break: break-all;
}

.yaml-editor {
  :deep(.el-textarea__inner) {
    font-family: 'Fira Code', 'Monaco', monospace;
    font-size: 13px;
    background: #0f0f23;
    color: #a3e635;
    border: none;
    border-radius: 0;
  }
}
</style>
