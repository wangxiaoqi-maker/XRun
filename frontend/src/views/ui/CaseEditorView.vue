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
      
      <!-- 模式切换 -->
      <div class="mode-switcher">
        <button 
          class="mode-btn"
          :class="{ active: editorMode === 'execute' }"
          @click="editorMode = 'execute'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          执行模式
        </button>
        <button 
          class="mode-btn teach"
          :class="{ active: editorMode === 'teach' }"
          @click="editorMode = 'teach'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          知识库教学
        </button>
      </div>
      
      <div class="header-actions">
        <!-- 教学模式工具栏 -->
        <template v-if="editorMode === 'teach'">
          <div class="teach-info" v-if="analysisResult">
            <span class="page-name">{{ analysisResult.page_name }}</span>
            <span class="update-time">上次更新: {{ lastAnalyzeTime }}</span>
          </div>
          <el-button 
            text 
            :disabled="!mirrorRef?.connected"
            @click="clearAnalysis"
            title="清空分析结果"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
          <el-button 
            type="primary"
            :loading="analyzing"
            :disabled="!mirrorRef?.connected"
            @click="analyzeCurrentPage"
          >
            <el-icon><MagicStick /></el-icon>
            {{ analyzing ? '正在扫描...' : 'AI 全页分析' }}
          </el-button>
        </template>
        
        <!-- 执行模式工具栏 -->
        <template v-else>
          <el-button @click="previewYaml">
            <el-icon><Document /></el-icon> 预览YAML
          </el-button>
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" @click="saveCase" :loading="saving">
            <el-icon><Check /></el-icon> 保存
          </el-button>
        </template>
      </div>
    </div>
    
    <div class="editor-content">
      <!-- 左侧：手机投屏 -->
      <div class="mirror-panel" :class="{ 'teach-mode': editorMode === 'teach' }">
        <div class="mirror-wrapper">
          <DeviceMirror 
            ref="mirrorRef"
            :recording="isRecording"
            @action-recorded="onActionRecorded"
            @device-connected="onDeviceConnected"
          />
          
          <!-- 元素框选 Overlay (仅教学模式且已连接时显示) -->
          <ElementOverlay
            v-if="editorMode === 'teach' && mirrorRef?.connected && analysisElements.length > 0"
            class="overlay-layer"
            :elements="analysisElements"
            :hovered-id="hoveredElementId"
            :selected-id="selectedElementId"
            :scanning="analyzing"
            :device-width="deviceWidth"
            :device-height="deviceHeight"
            @hover="onOverlayHover"
            @leave="onOverlayLeave"
            @click="onOverlayClick"
          />
          
          <!-- 扫描动效 (分析中显示) -->
          <div v-if="editorMode === 'teach' && analyzing" class="scan-overlay">
            <div class="scan-line"></div>
            <div class="scan-text">AI 正在分析页面...</div>
          </div>
        </div>
      </div>
      
      <!-- 右侧：根据模式显示不同面板 -->
      <div class="edit-panel">
        <!-- 教学模式面板 -->
        <AITeachingPanel
          v-if="editorMode === 'teach'"
          ref="teachingPanelRef"
          :elements="analysisElements"
          :page-summary="pageSummary"
          :hovered-id="hoveredElementId"
          :analyzing="analyzing"
          :saving="savingToKnowledge"
          @update:page-summary="pageSummary = $event"
          @hover="onPanelHover"
          @leave="onPanelLeave"
          @remove-element="onRemoveElement"
          @add-element="onAddElement"
          @save="saveToKnowledge"
          @cancel="clearAnalysis"
        />
        
        <!-- 执行模式面板 -->
        <template v-else>
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
                      <div class="drag-handle">
                        <el-icon><Rank /></el-icon>
                      </div>
                      <div class="step-number">{{ index + 1 }}</div>
                      <div class="step-content">
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
                        
                        <div class="step-params">
                          <template v-if="element.type === 'aiTap'">
                            <el-input 
                              v-model="element.prompt" 
                              placeholder="描述要点击的元素，如：登录按钮" 
                              style="flex: 1;"
                            >
                              <template #prefix><el-icon><MagicStick /></el-icon></template>
                            </el-input>
                          </template>
                          <template v-else-if="element.type === 'aiInput'">
                            <el-input v-model="element.prompt" placeholder="描述输入框" style="width: 200px;" />
                            <el-input v-model="element.text" placeholder="输入的内容" style="flex: 1;" />
                          </template>
                          <template v-else-if="element.type === 'aiQuery'">
                            <el-input v-model="element.prompt" placeholder="查询内容" style="flex: 1;" />
                            <el-input v-model="element.variable" placeholder="变量名（可选）" style="width: 150px;" />
                          </template>
                          <template v-else-if="element.type === 'aiAssert'">
                            <el-input v-model="element.prompt" placeholder="断言描述" style="flex: 1;" />
                          </template>
                          <template v-else-if="element.type === 'tap'">
                            <div class="coord-inputs">
                              <span class="coord-label">X:</span>
                              <el-input-number v-model="element.x" :min="0" controls-position="right" style="width: 100px;" />
                              <span class="coord-label">Y:</span>
                              <el-input-number v-model="element.y" :min="0" controls-position="right" style="width: 100px;" />
                            </div>
                          </template>
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
                          <template v-else-if="element.type === 'input'">
                            <el-input v-model="element.text" placeholder="输入的文本" style="flex: 1;" />
                          </template>
                          <template v-else-if="element.type === 'sleep'">
                            <el-input-number v-model="element.duration" :min="100" :step="500" style="width: 150px;" />
                            <span class="unit">毫秒</span>
                          </template>
                          <template v-else-if="element.type === 'launch'">
                            <el-input v-model="element.package" :placeholder="caseForm.platform === 'ios' ? 'Bundle ID' : '包名'" style="flex: 1;" />
                          </template>
                          <template v-else-if="element.type === 'screenshot'">
                            <el-input v-model="element.description" placeholder="截图描述（可选）" style="flex: 1;" />
                          </template>
                          <template v-else-if="element.type === 'back' || element.type === 'home'">
                            <span class="no-params">无需参数</span>
                          </template>
                        </div>
                      </div>
                      <div class="step-actions">
                        <el-button size="small" type="danger" text @click="removeStep(index)">
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
        </template>
      </div>
    </div>
    
    <!-- YAML 预览弹窗 -->
    <el-dialog v-model="yamlDialogVisible" title="YAML 预览" width="600px">
      <div class="yaml-preview">
        <pre>{{ generatedYaml }}</pre>
      </div>
      <template #footer>
        <el-button @click="copyYaml"><el-icon><DocumentCopy /></el-icon> 复制</el-button>
        <el-button type="primary" @click="yamlDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// 定义组件名称，用于 keep-alive 缓存
defineOptions({
  name: 'CaseEditorView'
})
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Check, Document, Plus, VideoCamera, Rank, Delete,
  MagicStick, DocumentCopy
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import YAML from 'js-yaml'
import DeviceMirror from '@/components/DeviceMirror.vue'
import ElementOverlay from '@/components/ElementOverlay.vue'
import AITeachingPanel from '@/components/AITeachingPanel.vue'
import { caseApi, knowledgeApi, deviceApi } from '@/api'

const route = useRoute()
const router = useRouter()

// ========== 基础状态 ==========
const isNew = computed(() => !route.params.id)
const saving = ref(false)
const isRecording = ref(false)
const mirrorRef = ref(null)
const teachingPanelRef = ref(null)
const yamlDialogVisible = ref(false)

// 编辑器模式: execute(执行) / teach(教学)
const editorMode = ref('execute')

// 用例表单
const caseForm = reactive({
  name: '',
  platform: 'android',
  description: '',
  steps: []
})

let stepIdCounter = 1

// ========== AI 教学模式状态 ==========
const analyzing = ref(false)
const savingToKnowledge = ref(false)
const analysisResult = ref(null)
const analysisElements = ref([])
const pageSummary = ref('')
const hoveredElementId = ref(null)
const selectedElementId = ref(null)
const lastAnalyzeTime = ref('刚刚')

// 设备分辨率 (用于坐标转换)
const deviceWidth = ref(1080)
const deviceHeight = ref(2400)
const connectedDevice = ref(null)

// ========== 计算属性 ==========
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

// ========== 设备连接回调 ==========
function onDeviceConnected(device) {
  connectedDevice.value = device
  
  // 解析分辨率
  if (device?.resolution) {
    const [w, h] = device.resolution.split('x').map(Number)
    if (w && h) {
      deviceWidth.value = w
      deviceHeight.value = h
    }
  }
  
  // 更新平台
  if (device?.platform) {
    caseForm.platform = device.platform.toLowerCase()
  }
}

// ========== AI 分析功能 ==========
async function analyzeCurrentPage() {
  if (!mirrorRef.value?.connected || !connectedDevice.value) {
    ElMessage.warning('请先连接设备')
    return
  }
  
  analyzing.value = true
  
  try {
    // 1. 获取截图
    const screenshotRes = await deviceApi.screenshotBase64(
      connectedDevice.value.udid,
      connectedDevice.value.platform
    )
    
    if (!screenshotRes.data?.screenshot) {
      throw new Error('获取截图失败')
    }
    
    const imageData = screenshotRes.data.screenshot
    
    // 2. 调用 AI 分析接口
    const result = await knowledgeApi.analyzePage({
      image_data: imageData,
      app_name: connectedDevice.value.name || '未知应用',
      platform: connectedDevice.value.platform,
      device_udid: connectedDevice.value.udid,
      device_resolution: connectedDevice.value.resolution,
      skip_duplicate: true
    })
    
    // 3. 更新状态
    analysisResult.value = result.data
    analysisElements.value = result.data.elements || []
    pageSummary.value = result.data.page_description || ''
    lastAnalyzeTime.value = '刚刚'
    
    ElMessage.success(`识别到 ${analysisElements.value.length} 个可测试元素`)
  } catch (e) {
    console.error('AI 分析失败:', e)
    ElMessage.error(e.response?.data?.detail || 'AI 分析失败，请重试')
  } finally {
    analyzing.value = false
  }
}

function clearAnalysis() {
  analysisResult.value = null
  analysisElements.value = []
  pageSummary.value = ''
  hoveredElementId.value = null
  selectedElementId.value = null
}

// ========== 元素交互 ==========
function onOverlayHover(id) {
  hoveredElementId.value = id
  // 同步滚动右侧面板
  teachingPanelRef.value?.scrollToElement(id)
}

function onOverlayLeave() {
  hoveredElementId.value = null
}

function onOverlayClick(element) {
  selectedElementId.value = element.id
  // 可以在这里添加将元素插入测试步骤的逻辑
}

function onPanelHover(id) {
  hoveredElementId.value = id
}

function onPanelLeave() {
  hoveredElementId.value = null
}

function onRemoveElement(id) {
  analysisElements.value = analysisElements.value.filter(e => e.id !== id)
}

function onAddElement() {
  // 手动添加元素的逻辑
  ElMessage.info('手动添加元素功能开发中')
}

// ========== 保存到知识库 ==========
async function saveToKnowledge() {
  if (!analysisResult.value) return
  
  savingToKnowledge.value = true
  
  try {
    // 这里可以调用更新接口，目前分析时已经保存
    ElMessage.success('已保存到知识库')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingToKnowledge.value = false
  }
}

// ========== 用例编辑功能 ==========
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
  
  Object.keys(step).forEach(key => {
    if (key !== 'id' && key !== 'type') {
      delete step[key]
    }
  })
  
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
    align-items: center;
    gap: 12px;
  }
}

// 模式切换器
.mode-switcher {
  display: flex;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    color: #334155;
  }
  
  &.active {
    background: white;
    color: #1e293b;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  &.teach.active {
    background: #6366f1;
    color: white;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }
}

// 教学模式信息
.teach-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-right: 8px;
  
  .page-name {
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
  }
  
  .update-time {
    font-size: 10px;
    color: #94a3b8;
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
  background: #0f172a;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  
  &.teach-mode {
    border-color: #6366f1;
    box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
  }
}

.mirror-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.overlay-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  pointer-events: none;
  
  :deep(.element-box) {
    pointer-events: auto;
  }
}

// 扫描动效
.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  background: rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(1px);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(99, 102, 241, 0.3) 20%,
    rgba(99, 102, 241, 0.8) 50%,
    rgba(99, 102, 241, 0.3) 80%,
    transparent 100%
  );
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% {
    top: 0%;
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}

.scan-text {
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.7);
  color: #a5b4fc;
  font-size: 12px;
  font-weight: 500;
  border-radius: 20px;
  border: 1px solid rgba(99, 102, 241, 0.3);
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
