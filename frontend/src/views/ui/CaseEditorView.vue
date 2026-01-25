<template>
  <div class="case-editor">
    <!-- 顶部操作栏 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h1>{{ isNew ? '新建用例' : '编辑用例' }}</h1>
        <el-tag v-if="!isNew" size="small" type="info">ID: {{ route.params.id }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button @click="previewYaml">
          <el-icon><Document /></el-icon> 预览YAML
        </el-button>
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" @click="saveCase" :loading="saving">
          <el-icon><Check /></el-icon> 保存
        </el-button>
      </div>
    </div>
    
    <div class="editor-content">
      <!-- 左侧：手机投屏 -->
      <div class="mirror-panel">
        <DeviceMirror 
          ref="mirrorRef"
          :recording="isRecording"
          @action-recorded="onActionRecorded"
        />
      </div>
      
      <!-- 右侧：用例编辑 -->
      <div class="edit-panel">
        <!-- 基本信息 -->
        <div class="panel-card">
          <div class="card-header">
            <span class="title">基本信息</span>
          </div>
          <div class="card-body">
            <el-form :model="caseForm" label-width="80px" size="default">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="用例名称" required>
                    <el-input v-model="caseForm.name" placeholder="请输入用例名称" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="平台">
                    <el-radio-group v-model="caseForm.platform">
                      <el-radio value="android">Android</el-radio>
                      <el-radio value="ios">iOS</el-radio>
                    </el-radio-group>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="描述">
                <el-input 
                  v-model="caseForm.description" 
                  type="textarea" 
                  :rows="2"
                  placeholder="用例描述（可选）" 
                />
              </el-form-item>
            </el-form>
          </div>
        </div>
        
        <!-- 步骤编辑 -->
        <div class="panel-card flex-1">
          <div class="card-header">
            <span class="title">测试步骤</span>
            <div class="header-actions">
              <el-button size="small" @click="addStep">
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
          <div class="card-body steps-body">
            <div class="steps-list" v-if="caseForm.steps.length > 0">
              <draggable 
                v-model="caseForm.steps" 
                item-key="id"
                handle=".drag-handle"
                animation="200"
              >
                <template #item="{ element, index }">
                  <div class="step-item" :class="{ 'is-ai': element.type.startsWith('ai') }">
                    <!-- 拖拽手柄 -->
                    <div class="drag-handle">
                      <el-icon><Rank /></el-icon>
                    </div>
                    
                    <!-- 步骤序号 -->
                    <div class="step-number">{{ index + 1 }}</div>
                    
                    <!-- 步骤内容 -->
                    <div class="step-content">
                      <!-- 操作类型选择 - 参考用户截图样式 -->
                      <el-select 
                        v-model="element.type" 
                        size="default" 
                        style="width: 150px;"
                        @change="onStepTypeChange(element)"
                      >
                        <el-option-group label="基础操作">
                          <el-option value="tap" label="点击 (Click)" />
                          <el-option value="input" label="输入 (Input)" />
                          <el-option value="swipe" label="滑动 (Swipe)" />
                          <el-option value="screenshot" label="截图 (Screenshot)" />
                        </el-option-group>
                        <el-option-group label="AI 操作">
                          <el-option value="aiTap" label="AI 操作 (AI Action)" />
                          <el-option value="aiQuery" label="AI 查询 (AI Query)" />
                          <el-option value="aiAssert" label="AI 断言 (AI Assert)" />
                        </el-option-group>
                        <el-option-group label="系统操作">
                          <el-option value="back" label="返回 (Back)" />
                          <el-option value="home" label="Home 键" />
                          <el-option value="sleep" label="等待 (Wait)" />
                          <el-option value="launch" label="启动应用 (Launch)" />
                        </el-option-group>
                      </el-select>
                      
                      <!-- 根据类型显示不同的参数输入 -->
                      <div class="step-params">
                        <!-- AI 操作 -->
                        <template v-if="element.type === 'aiTap'">
                          <el-input 
                            v-model="element.prompt" 
                            placeholder="描述要点击的元素，如：登录按钮、输入框" 
                            style="flex: 1;"
                          >
                            <template #prefix>
                              <el-icon><MagicStick /></el-icon>
                            </template>
                          </el-input>
                        </template>
                        
                        <!-- AI 输入 -->
                        <template v-else-if="element.type === 'aiInput'">
                          <el-input 
                            v-model="element.prompt" 
                            placeholder="描述输入框" 
                            style="width: 200px;"
                          />
                          <el-input 
                            v-model="element.text" 
                            placeholder="输入的内容" 
                            style="flex: 1;"
                          />
                        </template>
                        
                        <!-- AI 查询 -->
                        <template v-else-if="element.type === 'aiQuery'">
                          <el-input 
                            v-model="element.prompt" 
                            placeholder="查询内容，如：获取页面标题" 
                            style="flex: 1;"
                          />
                          <el-input 
                            v-model="element.variable" 
                            placeholder="存储变量名（可选）" 
                            style="width: 150px;"
                          />
                        </template>
                        
                        <!-- AI 断言 -->
                        <template v-else-if="element.type === 'aiAssert'">
                          <el-input 
                            v-model="element.prompt" 
                            placeholder="断言描述，如：页面显示登录成功" 
                            style="flex: 1;"
                          />
                        </template>
                        
                        <!-- 坐标点击 -->
                        <template v-else-if="element.type === 'tap'">
                          <div class="coord-inputs">
                            <span class="coord-label">X:</span>
                            <el-input-number v-model="element.x" :min="0" controls-position="right" style="width: 100px;" />
                            <span class="coord-label">Y:</span>
                            <el-input-number v-model="element.y" :min="0" controls-position="right" style="width: 100px;" />
                          </div>
                        </template>
                        
                        <!-- 滑动 -->
                        <template v-else-if="element.type === 'swipe'">
                          <div class="coord-inputs">
                            <span class="coord-label">起点:</span>
                            <el-input-number v-model="element.startX" :min="0" style="width: 80px;" />
                            <el-input-number v-model="element.startY" :min="0" style="width: 80px;" />
                            <span class="coord-label">→ 终点:</span>
                            <el-input-number v-model="element.endX" :min="0" style="width: 80px;" />
                            <el-input-number v-model="element.endY" :min="0" style="width: 80px;" />
                          </div>
                        </template>
                        
                        <!-- 输入文本 -->
                        <template v-else-if="element.type === 'input'">
                          <el-input 
                            v-model="element.text" 
                            placeholder="输入的文本内容" 
                            style="flex: 1;"
                          />
                        </template>
                        
                        <!-- 等待 -->
                        <template v-else-if="element.type === 'sleep'">
                          <el-input-number 
                            v-model="element.duration" 
                            :min="100" 
                            :step="500"
                            style="width: 150px;"
                          />
                          <span class="unit">毫秒</span>
                        </template>
                        
                        <!-- 启动应用 -->
                        <template v-else-if="element.type === 'launch'">
                          <el-input 
                            v-model="element.package" 
                            :placeholder="caseForm.platform === 'ios' ? 'Bundle ID' : '包名'" 
                            style="flex: 1;"
                          />
                        </template>
                        
                        <!-- 截图 -->
                        <template v-else-if="element.type === 'screenshot'">
                          <el-input 
                            v-model="element.description" 
                            placeholder="截图描述（可选）" 
                            style="flex: 1;"
                          />
                        </template>
                        
                        <!-- 返回/Home -->
                        <template v-else-if="element.type === 'back' || element.type === 'home'">
                          <span class="no-params">无需参数</span>
                        </template>
                      </div>
                    </div>
                    
                    <!-- 删除按钮 -->
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
            </div>
            
            <el-empty v-else description="暂无步骤，点击上方按钮添加" :image-size="80" />
          </div>
        </div>
      </div>
    </div>
    
    <!-- YAML 预览弹窗 -->
    <el-dialog v-model="yamlDialogVisible" title="YAML 预览" width="600px">
      <div class="yaml-preview">
        <pre>{{ generatedYaml }}</pre>
      </div>
      <template #footer>
        <el-button @click="copyYaml">
          <el-icon><DocumentCopy /></el-icon> 复制
        </el-button>
        <el-button type="primary" @click="yamlDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Check, Document, Plus, VideoCamera, Rank, Delete,
  MagicStick, DocumentCopy
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import YAML from 'js-yaml'
import DeviceMirror from '@/components/DeviceMirror.vue'
import { caseApi } from '@/api'

const route = useRoute()
const router = useRouter()

const isNew = computed(() => !route.params.id)
const saving = ref(false)
const isRecording = ref(false)
const mirrorRef = ref(null)
const yamlDialogVisible = ref(false)

const caseForm = reactive({
  name: '',
  platform: 'android',
  description: '',
  steps: []
})

let stepIdCounter = 1

// 生成的 YAML
const generatedYaml = computed(() => {
  const yamlObj = {
    name: caseForm.name,
    platform: caseForm.platform,
    description: caseForm.description,
    steps: caseForm.steps.map(step => {
      const { id, ...rest } = step
      return rest
    })
  }
  return YAML.dump(yamlObj, { lineWidth: -1 })
})

function goBack() {
  router.push('/ui/cases')
}

async function loadCase() {
  try {
    const res = await caseApi.get(route.params.id)
    const data = res.data
    
    caseForm.name = data.name
    caseForm.platform = data.platform
    caseForm.description = data.description || ''
    
    if (data.yaml_content) {
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
      caseForm.steps = parsed.steps.map(step => ({
        id: stepIdCounter++,
        ...step
      }))
    }
  } catch (e) {
    console.error('YAML 解析失败', e)
  }
}

function addStep() {
  caseForm.steps.push({
    id: stepIdCounter++,
    type: 'aiTap',
    prompt: ''
  })
}

function removeStep(index) {
  caseForm.steps.splice(index, 1)
}

function onStepTypeChange(step) {
  const { id, type } = step
  
  // 清除旧字段
  Object.keys(step).forEach(key => {
    if (key !== 'id' && key !== 'type') {
      delete step[key]
    }
  })
  
  // 初始化新字段
  switch (type) {
    case 'aiTap':
    case 'aiAssert':
      step.prompt = ''
      break
    case 'aiQuery':
      step.prompt = ''
      step.variable = ''
      break
    case 'aiInput':
      step.prompt = ''
      step.text = ''
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
  const step = {
    id: stepIdCounter++,
    type: action.type,
    ...action
  }
  delete step.description
  caseForm.steps.push(step)
  ElMessage.success(`已添加步骤: ${action.description}`)
}

function previewYaml() {
  yamlDialogVisible.value = true
}

function copyYaml() {
  navigator.clipboard.writeText(generatedYaml.value)
  ElMessage.success('已复制到剪贴板')
}

async function saveCase() {
  if (!caseForm.name.trim()) {
    ElMessage.error('请输入用例名称')
    return
  }
  
  if (caseForm.steps.length === 0) {
    ElMessage.error('请添加至少一个步骤')
    return
  }
  
  saving.value = true
  
  try {
    const data = {
      name: caseForm.name,
      platform: caseForm.platform,
      description: caseForm.description,
      yaml_content: generatedYaml.value
    }
    
    if (isNew.value) {
      await caseApi.create(data)
      ElMessage.success('用例创建成功')
    } else {
      await caseApi.update(route.params.id, data)
      ElMessage.success('用例保存成功')
    }
    
    router.push('/ui/cases')
  } catch (e) {
    ElMessage.error('保存失败')
    console.error(e)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (!isNew.value) {
    loadCase()
  }
})
</script>

<style lang="scss" scoped>
.case-editor {
  height: calc(100vh - var(--header-height) - 40px);
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h1 {
      font-size: 20px;
      font-weight: 600;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.editor-content {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
}

.mirror-panel {
  width: 380px;
  flex-shrink: 0;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.edit-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.panel-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  
  &.flex-1 {
    flex: 1;
    overflow: hidden;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    
    .title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .header-actions {
      display: flex;
      gap: 8px;
    }
  }
  
  .card-body {
    padding: 20px;
    
    &.steps-body {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
    }
  }
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s;
  
  &:hover {
    border-color: var(--border-color);
  }
  
  &.is-ai {
    border-left: 3px solid var(--primary-color);
    background: rgba(24, 144, 255, 0.04);
  }
}

.drag-handle {
  cursor: move;
  color: var(--text-muted);
  padding: 4px;
  
  &:hover {
    color: var(--text-secondary);
  }
}

.step-number {
  width: 28px;
  height: 28px;
  background: var(--primary-color);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.step-params {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.coord-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .coord-label {
    font-size: 13px;
    color: var(--text-muted);
    font-weight: 500;
  }
}

.unit {
  font-size: 13px;
  color: var(--text-muted);
}

.no-params {
  font-size: 13px;
  color: var(--text-muted);
  font-style: italic;
}

.step-actions {
  flex-shrink: 0;
}

.yaml-preview {
  background: #1e1e1e;
  border-radius: 8px;
  padding: 16px;
  max-height: 400px;
  overflow: auto;
  
  pre {
    margin: 0;
    font-family: 'Fira Code', 'Monaco', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #a3e635;
    white-space: pre-wrap;
  }
}
</style>






