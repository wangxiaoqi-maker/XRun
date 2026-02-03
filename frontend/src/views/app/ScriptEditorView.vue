<template>
  <div class="editor-page">
    <!-- 顶部工具栏 -->
    <!-- 顶部工具栏 - 新的整合布局 -->
    <div class="editor-header">
      <!-- 左侧：设备状态栏 (与下方设备面板对齐) -->
      <div class="header-device-portion">
        <template v-if="mirrorRef?.selectedDevice">
          <div class="device-info-group">
             <span class="device-name-title">{{ mirrorRef?.selectedDevice?.name || mirrorRef?.selectedDevice?.model }}</span>
             <span class="fps-tag" v-if="mirrorRef?.fps > 0">{{ mirrorRef?.fps }} FPS</span>
          </div>
          
          <div class="device-ctrl-group">
             <span class="mode-box">{{ mirrorRef?.screenMode?.toUpperCase() || 'SCRCPY' }}</span>
             <el-button link type="primary" size="small" @click="mirrorRef?.toggleScreenMode">切换</el-button>
             <el-button link type="danger" size="small" @click="mirrorRef?.disconnect">断开</el-button>
          </div>
        </template>
        <template v-else>
           <div class="device-status-dot disconnected"></div>
           <span class="device-name-title text-gray">未连接设备</span>
        </template>
      </div>

      <!-- 右侧：脚本信息与操作 -->
      <div class="header-script-portion">
        <!-- 执行模式内容 -->
        <template v-if="editorMode === 'execute'">
          <div class="script-meta">
             <div class="script-icon-box">
               <el-icon><Document /></el-icon>
             </div>
             <div class="script-text-group">
               <span class="script-title">{{ scriptName }}</span>
               <span class="script-subtitle">Last edited just now</span>
             </div>
          </div>
          <div class="header-actions">
            <el-button @click="saveScript" class="header-btn" plain size="default">保存</el-button>
            <el-button type="primary" @click="runScript" :loading="isRunning" class="header-btn run-btn" size="default">
              {{ isRunning ? 'Running...' : 'Run' }}
            </el-button>
          </div>
        </template>
        
        <!-- 教学模式内容 -->
        <template v-else>
          <div class="teach-info" v-if="analysisResult">
            <span class="page-name">{{ analysisResult.page_name }}</span>
            <span class="update-time">上次更新: {{ lastAnalyzeTime }}</span>
          </div>
          <div class="header-actions">
            <!-- 当前模型显示 -->
            <div v-if="currentModelName" class="current-model-badge">
              <el-icon :size="12"><Cpu /></el-icon>
              <span>{{ currentModelName }}</span>
            </div>
            <el-button text :disabled="!mirrorRef?.connected" @click="clearAnalysis" title="清空">
              <el-icon><Delete /></el-icon>
            </el-button>
            <el-button 
              type="primary"
              :loading="analyzing"
              :disabled="!mirrorRef?.connected"
              @click="analyzeCurrentPage"
              class="ai-analyze-btn"
            >
              <el-icon v-if="!analyzing"><MagicStick /></el-icon>
              {{ analyzing ? '正在扫描...' : 'AI 全页分析' }}
            </el-button>
          </div>
        </template>
        
        <!-- 模式切换（右侧） -->
        <div class="mode-switcher">
          <el-tooltip content="执行模式" placement="bottom">
            <div 
              class="mode-item" 
              :class="{ active: editorMode === 'execute' }"
              @click="switchMode('execute')"
            >
              <el-icon :size="16"><VideoPlay /></el-icon>
            </div>
          </el-tooltip>
          <el-tooltip content="知识库教学" placement="bottom">
            <div 
              class="mode-item teach" 
              :class="{ active: editorMode === 'teach' }"
              @click="switchMode('teach')"
            >
              <el-icon :size="16"><MagicStick /></el-icon>
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>
    
    <!-- 主体内容 -->
    <div class="editor-body">
      <!-- 左侧：设备投屏 -->
      <div class="device-panel">
        <DeviceMirror 
          ref="mirrorRef"
          :recording="isRecording"
          :hide-header="true"
          @action-recorded="onActionRecorded"
          @device-connected="onDeviceConnected"
        >
          <!-- 元素框选 Overlay (仅教学模式 + 有分析结果) -->
          <template #overlay="{ deviceWidth: dw, deviceHeight: dh, imgRect }">
            <ElementOverlay
              v-if="editorMode === 'teach' && mirrorRef?.connected && analysisElements.length > 0"
              class="element-overlay-layer"
              :elements="analysisElements"
              :hovered-id="hoveredElementId"
              :selected-id="selectedElementId"
              :device-width="dw"
              :device-height="dh"
              :img-rect="imgRect"
              @hover="hoveredElementId = $event"
              @leave="hoveredElementId = null"
              @click="selectedElementId = $event.id"
            />
          </template>
        </DeviceMirror>
        
        <!-- 扫描动效 (仅教学模式 + 分析中) -->
        <div v-if="editorMode === 'teach' && analyzing" class="scan-overlay">
          <div class="scan-line"></div>
          <div class="scan-text">AI 正在分析页面...</div>
        </div>
      </div>
      
      <!-- 右侧：步骤编辑器 / 教学面板 -->
      <div class="steps-panel">
        <!-- 教学模式面板 -->
        <AITeachingPanel
          v-if="editorMode === 'teach'"
          ref="teachingPanelRef"
          :elements="analysisElements"
          :page-summary="pageSummary"
          :hovered-id="hoveredElementId"
          :analyzing="analyzing"
          :saving="savingToKnowledge"
          :processing-time="analysisResult?.processing_time || 0"
          :usage="analysisResult?.usage || {}"
          :screenshot="analysisScreenshot"
          :current-model-name="currentModelName"
          :exploration-enabled="explorationEnabled"
          :exploration-stats="explorationStats"
          :current-page-id="currentPageId"
          @update:page-summary="pageSummary = $event"
          @hover="hoveredElementId = $event"
          @leave="hoveredElementId = null"
          @remove-element="onRemoveElement"
          @add-element="onAddElement"
          @save="saveToKnowledge"
          @cancel="clearAnalysis"
          @element-click="onElementClickForExploration"
        />
        
        <!-- 执行模式步骤列表 -->
        <div v-else class="steps-container">
          <div class="steps-wrapper">
            
            <draggable 
              v-model="steps" 
              item-key="id"
              handle=".step-index" 
              animation="200"
              class="steps-list-area"
              ghost-class="ghost-card"
            >
              <template #item="{ element: step, index }">
                <div 
                  class="step-row"
                  :class="[
                    { active: activeIndex === index },
                    step.status === 'running' ? 'status-running' : '',
                    step.status === 'success' ? 'status-success' : ''
                  ]"
                  @click="activeIndex = index"
                >
                  <!-- Left Colored Strip -->
                  <div class="status-strip" v-if="['running', 'success'].includes(step.status)"></div>

                  <!-- 1. Index (Drag Handle) -->
                  <div class="step-index">{{ (index + 1).toString().padStart(2, '0') }}</div>
                  
                  <!-- 2. Action Tag -->
                  <div class="step-tag">
                    <span class="tag-badge" :class="step.action">{{ step.actionLabel }}</span>
                  </div>
                  
                  <!-- 3. Content -->
                  <div class="step-content">
                    <!-- Target with label -->
                    <template v-if="step.target">
                      <span class="param-label">{{ getParamLabel(step.action) }}</span>
                      <span class="target-text">{{ step.target }}</span>
                    </template>
                    
                    <!-- Value (Gray pill) -->
                    <span class="value-pill" v-if="step.value">{{ step.value }}</span>
                    
                     <!-- Scheme URL display -->
                    <span class="value-pill" v-if="['schemeUrl', 'schemeRouter'].includes(step.action) && step.url">
                       {{ step.url }}
                    </span>
                    
                     <el-icon class="config-icon" @click.stop="editStep(index)"><Setting /></el-icon>
                  </div>
                  
                  <!-- 4. Status (Right side) -->
                  <div class="step-status-area">
                    <!-- Running -->
                    <div v-if="step.status === 'running'" class="status-box running">
                        <span>执行中</span>
                        <div class="spinner-ring"></div>
                    </div>
                    
                    <!-- Success -->
                    <div v-else-if="step.status === 'success'" class="status-box success">
                        <span class="duration-text">{{ formatDuration(step.duration) }}</span>
                        <div class="check-circle"><el-icon><Check /></el-icon></div>
                    </div>
                    
                    <!-- Pending -->
                    <div v-else class="status-box pending">
                        <span>等待执行</span>
                    </div>
                    
                    <!-- Hover Actions -->
                    <div class="hover-actions">
                        <el-button type="danger" link @click.stop="deleteStep(index)">
                            <el-icon><Delete /></el-icon>
                        </el-button>
                    </div>
                  </div>
                </div>
              </template>
            </draggable>
            
            <!-- 智能步骤输入 -->
            <div class="add-step-wrapper">
              <SmartStepInput @add-step="onSmartAddStep" />
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- AI 分析配置弹窗 -->
  <el-dialog 
    v-model="showAnalyzeConfig" 
    title="AI 页面分析配置" 
    width="480px"
    :close-on-click-modal="false"
  >
    <el-form label-width="80px" :disabled="analyzing">
      <el-form-item label="选择应用" required>
        <el-select 
          v-model="analyzeConfig.appId" 
          placeholder="请选择应用"
          style="width: 100%"
          :loading="loadingApps"
        >
          <el-option 
            v-for="app in appList" 
            :key="app.id" 
            :label="app.name"
            :value="app.id"
          >
            <div style="display: flex; align-items: center; gap: 8px;">
              <img 
                v-if="app.icon_url" 
                :src="app.icon_url" 
                style="width: 20px; height: 20px; border-radius: 4px;"
              />
              <span>{{ app.name }}</span>
              <el-tag size="small" type="info">{{ app.platform }}</el-tag>
            </div>
          </el-option>
        </el-select>
        <div class="form-tip">选择当前分析的应用，用于关联页面和元素</div>
      </el-form-item>
      <el-form-item label="视觉模型">
        <el-select 
          v-model="analyzeConfig.modelId" 
          placeholder="选择模型（可选）"
          style="width: 100%"
          clearable
          :loading="loadingModels"
          @change="onModelChange"
        >
          <el-option 
            v-for="model in visionModels" 
            :key="model.id" 
            :label="`${model.provider?.name || '未知'} / ${model.name}`"
            :value="model.id"
          >
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>{{ model.name }}</span>
              <span style="color: #999; font-size: 12px;">{{ model.provider?.name }}</span>
            </div>
          </el-option>
        </el-select>
        <div class="form-tip">不选择则使用默认模型（qwen-vl）</div>
      </el-form-item>
      <el-form-item label="页面描述">
        <el-input 
          v-model="analyzeConfig.contextHint" 
          type="textarea"
          :rows="3"
          placeholder="可选。描述当前页面的上下文，帮助 AI 更准确识别，如：&#10;• 这是微信支付首页&#10;• 用户已登录状态&#10;• 这是订单确认页面"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAnalyzeConfig = false">取消</el-button>
      <el-button type="primary" @click="doAnalyze" :loading="analyzing" :disabled="!analyzeConfig.appId">
        开始分析
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, nextTick, watchEffect, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// 定义组件名称，用于 keep-alive 缓存
defineOptions({
  name: 'ScriptEditorView'
})
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, VideoPlay, Check, Minus, Setting, Delete, Plus, Loading, Camera,
  SwitchButton, CircleClose, Document, ChatLineSquare, MagicStick, Cpu
} from '@element-plus/icons-vue'
import Draggable from 'vuedraggable'
import DeviceMirror from '@/components/DeviceMirror.vue'
import ElementOverlay from '@/components/ElementOverlay.vue'
import AITeachingPanel from '@/components/AITeachingPanel.vue'
import SmartStepInput from '@/components/SmartStepInput.vue'
import { deviceApi, knowledgeApi, llmApi, explorationApi, appApi } from '@/api'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

const route = useRoute()
const router = useRouter()

const scriptName = ref('微信支付流程自动化')
const isSaved = ref(true)
const isRecording = ref(false)
const isRunning = ref(false)
const activeIndex = ref(-1)
const mirrorRef = ref(null)
const teachingPanelRef = ref(null)

// 编辑器模式: execute(执行) / teach(教学)
const editorMode = ref('execute')

function switchMode(mode) {
  editorMode.value = mode
}

// 脚本步骤数据
const steps = ref([])

// ========== AI 教学模式状态 ==========
const analyzing = ref(false)
const savingToKnowledge = ref(false)
const analysisResult = ref(null)
const analysisElements = ref([])
const analysisScreenshot = ref('') // 保存分析时的截图 base64
const pageSummary = ref('')
const hoveredElementId = ref(null)
const selectedElementId = ref(null)
const lastAnalyzeTime = ref('刚刚')
const deviceWidth = ref(1080)
const deviceHeight = ref(2400)
const connectedDevice = ref(null)

// ========== 知识图谱探索状态 ==========
const explorationEnabled = ref(true)  // 是否启用探索模式
const explorationSession = ref(null)  // 当前探索会话
const currentPageId = ref(null)       // 当前页面 ID
const explorationStats = ref({        // 探索统计
  pages_discovered: 0,
  transitions_count: 0
})
const appGraph = ref(null)            // App 知识图谱

// AI 分析配置弹窗
const showAnalyzeConfig = ref(false)
const analyzeConfig = ref({
  appId: '',
  providerId: '',
  modelId: '',
  contextHint: ''
})
const visionModels = ref([])  // 支持视觉的模型列表
const loadingModels = ref(false)
const appList = ref([])  // 应用列表
const loadingApps = ref(false)

// 当前选中的模型名称
const currentModelName = computed(() => {
  if (!analyzeConfig.value.modelId) return ''
  const model = visionModels.value.find(m => m.id === analyzeConfig.value.modelId)
  return model?.name || model?.model_id || ''
})

const actionOptions = [
  { value: '点击 (Click)', action: 'click' },
  { value: '输入 (Input)', action: 'input' },
  { value: '滑动 (Swipe)', action: 'swipe' },
  { value: '等待 (Wait)', action: 'wait' },
  { value: '检查 (Assert)', action: 'assert' },
  { value: 'Scheme URL', action: 'schemeUrl' },
  { value: 'Scheme Router', action: 'schemeRouter' },
]

// Inline Form State
const showInlineAdd = ref(false)
const inlineFormInput = ref(null)
const inlineForm = ref({ action: 'click', target: '', value: '', url: '' })
const editingIndex = ref(-1)

function goBack() { router.push('/ui/scripts') }
function saveScript() { isSaved.value = true; ElMessage.success('保存成功') }
function toggleRecord() { isRecording.value = !isRecording.value }
function screenshot() { /* Implement screenshot */ }
function onActionRecorded(action) { console.log("Recorded", action) }
async function onDeviceConnected(device) { 
  connectedDevice.value = device
  ElMessage.success('设备已连接')
  if (device?.resolution) {
    const [w, h] = device.resolution.split('x').map(Number)
    if (w && h) { deviceWidth.value = w; deviceHeight.value = h }
  }
  
  // 启动探索会话
  if (explorationEnabled.value && device) {
    await startExplorationSession(device)
  }
}

// 启动探索会话
async function startExplorationSession(device) {
  try {
    // 获取 app_id（基于应用名称）
    const appName = device.name || '未知应用'
    
    const res = await explorationApi.startExploration({
      app_id: appName,  // 这里使用应用名称作为临时 ID
      device_udid: device.udid,
      mode: 'manual'
    })
    
    if (res.data.success) {
      explorationSession.value = {
        session_id: res.data.session_id,
        app_id: appName
      }
      console.log('[探索] 探索会话已开始:', res.data.session_id)
    }
  } catch (e) {
    console.error('[探索] 启动探索会话失败:', e)
  }
}

// 结束探索会话
async function endExplorationSession() {
  if (!explorationSession.value?.session_id) return
  
  try {
    const res = await explorationApi.endExploration(explorationSession.value.session_id)
    if (res.data.success) {
      console.log('[探索] 探索会话已结束:', res.data)
      explorationStats.value = {
        pages_discovered: res.data.pages_discovered || 0,
        transitions_count: res.data.transitions_count || 0
      }
    }
    explorationSession.value = null
    currentPageId.value = null
  } catch (e) {
    console.error('[探索] 结束探索会话失败:', e)
  }
}

// 更新探索会话的当前页面
async function updateExplorationCurrentPage(pageId) {
  if (!explorationSession.value?.session_id || !pageId) return
  
  try {
    await explorationApi.updateCurrentPage(explorationSession.value.session_id, pageId)
    console.log('[探索] 更新当前页面:', pageId)
  } catch (e) {
    console.error('[探索] 更新当前页面失败:', e)
  }
}

// 记录页面跳转（当用户点击元素后页面发生变化时调用）
async function recordPageTransition(triggerElement, actionType = 'click') {
  if (!explorationSession.value?.session_id || !currentPageId.value) {
    console.log('[探索] 未开启探索会话或当前页面未知，跳过跳转记录')
    return null
  }
  
  try {
    // 获取新页面截图
    const wdaPort = mirrorRef.value?.wdaPort || 0
    const screenshotRes = await deviceApi.screenshotBase64(
      connectedDevice.value.udid,
      connectedDevice.value.platform,
      wdaPort
    )
    
    if (!screenshotRes.data?.screenshot) {
      console.error('[探索] 获取跳转后截图失败')
      return null
    }
    
    // 记录跳转
    const res = await explorationApi.recordTransition({
      session_id: explorationSession.value.session_id,
      trigger_element: {
        id: triggerElement.id,
        name: triggerElement.element_name || triggerElement.name,
        midscene_locator: triggerElement.midscene_locator
      },
      action_type: actionType,
      to_page_screenshot: screenshotRes.data.screenshot,
      model_id: analyzeConfig.value.modelId || undefined
    })
    
    if (res.data.success) {
      console.log('[探索] 跳转记录成功:', res.data)
      
      // 更新统计
      if (res.data.session_stats) {
        explorationStats.value = res.data.session_stats
      }
      
      // 更新当前页面
      if (res.data.to_page?.id) {
        currentPageId.value = res.data.to_page.id
      }
      
      // 提示用户
      if (res.data.is_new_page) {
        ElMessage.success(`发现新页面: ${res.data.to_page?.name || '未知页面'}`)
      }
      
      return res.data
    }
    
    return null
  } catch (e) {
    console.error('[探索] 记录跳转失败:', e)
    return null
  }
}

// 加载 App 知识图谱
async function loadAppGraph() {
  if (!explorationSession.value?.app_id) return
  
  try {
    const res = await explorationApi.getAppGraph(explorationSession.value.app_id)
    if (res.data.success) {
      appGraph.value = res.data.data
      console.log('[探索] 加载知识图谱:', appGraph.value)
    }
  } catch (e) {
    console.error('[探索] 加载知识图谱失败:', e)
  }
}

// ========== AI 教学模式方法 ==========

// 加载支持视觉的模型
async function loadVisionModels() {
  loadingModels.value = true
  try {
    const res = await llmApi.listModels({ include_disabled: false })
    // 过滤出支持视觉的模型
    visionModels.value = (res.data.models || []).filter(m => m.supports_vision)
    // 如果有模型，默认选择第一个
    if (visionModels.value.length > 0 && !analyzeConfig.value.modelId) {
      const first = visionModels.value[0]
      analyzeConfig.value.providerId = first.provider_id
      analyzeConfig.value.modelId = first.id
    }
  } catch (e) {
    console.error('加载模型列表失败:', e)
  } finally {
    loadingModels.value = false
  }
}

// 加载应用列表（按当前项目筛选）
async function loadAppList() {
  loadingApps.value = true
  try {
    const params = {}
    if (projectStore.currentProject?.id) {
      params.project_id = projectStore.currentProject.id
    }
    const res = await appApi.list(params)
    appList.value = res.data || []
    // 如果有应用且未选择，默认选第一个
    if (appList.value.length > 0 && !analyzeConfig.value.appId) {
      analyzeConfig.value.appId = appList.value[0].id
    }
  } catch (e) {
    console.error('加载应用列表失败:', e)
  } finally {
    loadingApps.value = false
  }
}

// 打开分析配置弹窗
function openAnalyzeConfig() {
  if (!mirrorRef.value?.connected || !connectedDevice.value) {
    ElMessage.warning('请先连接设备')
    return
  }
  loadVisionModels()
  loadAppList()
  showAnalyzeConfig.value = true
}

// 执行 AI 分析
async function doAnalyze() {
  showAnalyzeConfig.value = false
  analyzing.value = true
  try {
    // 获取 WDA 端口（iOS 设备需要）
    const wdaPort = mirrorRef.value?.wdaPort || 0
    console.log('[AI分析] 截图参数:', connectedDevice.value.udid, connectedDevice.value.platform, 'wdaPort:', wdaPort)
    
    const screenshotRes = await deviceApi.screenshotBase64(connectedDevice.value.udid, connectedDevice.value.platform, wdaPort)
    if (!screenshotRes.data?.screenshot) throw new Error('获取截图失败')
    
    // 保存截图用于元素切图显示
    analysisScreenshot.value = screenshotRes.data.screenshot
    
    // 获取选中的应用信息
    const selectedApp = appList.value.find(a => a.id === analyzeConfig.value.appId)
    
    const requestData = {
      image_data: screenshotRes.data.screenshot,
      app_id: analyzeConfig.value.appId || undefined,
      project_id: projectStore.currentProject?.id || undefined,
      app_name: selectedApp?.name || connectedDevice.value.name || '未知应用',
      platform: selectedApp?.platform || connectedDevice.value.platform,
      device_udid: connectedDevice.value.udid,
      device_resolution: connectedDevice.value.resolution,
      skip_duplicate: false,
      context_hint: analyzeConfig.value.contextHint || undefined,
      provider_id: analyzeConfig.value.providerId || undefined,
      model_id: analyzeConfig.value.modelId || undefined
    }
    
    const result = await knowledgeApi.analyzePage(requestData)
    
    analysisResult.value = result.data
    analysisElements.value = result.data.elements || []
    pageSummary.value = result.data.page_description || ''
    lastAnalyzeTime.value = '刚刚'
    
    // 更新探索会话的当前页面
    if (explorationSession.value?.session_id && result.data.page_id) {
      currentPageId.value = result.data.page_id
      await updateExplorationCurrentPage(result.data.page_id)
    }
    
    ElMessage.success(`识别到 ${analysisElements.value.length} 个可测试元素`)
  } catch (e) {
    console.error('AI 分析失败:', e)
    ElMessage.error(e.response?.data?.detail || 'AI 分析失败，请重试')
  } finally {
    analyzing.value = false
  }
}

// 模型选择变化
function onModelChange(modelId) {
  if (modelId) {
    const model = visionModels.value.find(m => m.id === modelId)
    if (model) {
      analyzeConfig.value.providerId = model.provider_id
    }
  } else {
    analyzeConfig.value.providerId = ''
  }
}

// 兼容旧的直接调用
async function analyzeCurrentPage() {
  openAnalyzeConfig()
}

function clearAnalysis() {
  analysisResult.value = null
  analysisElements.value = []
  pageSummary.value = ''
  hoveredElementId.value = null
  selectedElementId.value = null
}

function onRemoveElement(id) {
  analysisElements.value = analysisElements.value.filter(e => e.id !== id)
}

// 元素点击处理（用于探索模式）
async function onElementClickForExploration(element) {
  if (!explorationEnabled.value || !explorationSession.value) return
  
  console.log('[探索] 元素被点击:', element.element_name || element.name)
  
  // 在设备上执行点击操作
  if (connectedDevice.value && element.bbox) {
    try {
      // 计算点击坐标（bbox 是百分比，需要转换为像素）
      const bbox = element.bbox
      const centerX = ((bbox[0] + bbox[2] / 2) / 100) * deviceWidth.value
      const centerY = ((bbox[1] + bbox[3] / 2) / 100) * deviceHeight.value
      
      // 执行点击
      if (connectedDevice.value.platform === 'ios') {
        await deviceApi.iosNativeTap(connectedDevice.value.udid, centerX, centerY)
      } else {
        await deviceApi.tap(connectedDevice.value.udid, centerX, centerY, connectedDevice.value.platform)
      }
      
      // 等待页面稳定
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // 记录跳转
      await recordPageTransition(element, 'click')
      
    } catch (e) {
      console.error('[探索] 点击元素失败:', e)
    }
  }
}

function onAddElement() {
  ElMessage.info('手动添加元素功能开发中')
}

async function saveToKnowledge() {
  if (!analysisResult.value) {
    ElMessage.warning('请先进行 AI 分析')
    return
  }
  
  // 如果已保存过，提示用户
  if (analysisResult.value.is_saved) {
    ElMessage.info('该分析结果已保存到知识库')
    return
  }
  
  savingToKnowledge.value = true
  try {
    const res = await knowledgeApi.saveToKnowledgeBase(analysisResult.value)
    if (res.data?.success) {
      ElMessage.success(res.data.message || '已保存到知识库')
      // 更新状态，标记已保存
      analysisResult.value.is_saved = true
      analysisResult.value.page_id = res.data.page_id
    } else {
      ElMessage.warning(res.data?.message || '保存失败')
    }
  } catch (e) {
    console.error('保存到知识库失败:', e)
    ElMessage.error(e.response?.data?.detail || '保存到知识库失败')
  } finally {
    savingToKnowledge.value = false
  }
}

function formatDuration(ms) {
    if (ms >= 1000) return (ms / 1000).toFixed(1) + 's';
    return ms + 'ms';
}

// Run Script
// Run Script
async function runScript() {
    if(isRunning.value) return;
    if(!steps.value.length) {
        ElMessage.warning('请先添加步骤')
        return
    }
    
    isRunning.value = true;
    ElMessage.info('开始执行脚本...')
    
    // 重置状态
    steps.value.forEach(s => {
        s.status = 'pending'
        s.duration = 0
    })
    
    try {
        for (let i = 0; i < steps.value.length; i++) {
            const step = steps.value[i]
            step.status = 'running'
            
            const startTime = performance.now() // 精准计时
            
            try {
                // 根据类型执行
                switch (step.action) {
                    case 'schemeUrl':
                    case 'schemeRouter':
                        if (!step.url) throw new Error('Scheme URL 为空')
                        
                        // 获取当前 WDA 端口 (从 DeviceMirror 组件)
                        let wdaUrl = undefined
                        if (mirrorRef.value && mirrorRef.value.wdaPort > 0) {
                            wdaUrl = `http://localhost:${mirrorRef.value.wdaPort}`
                            console.log('Using WDA URL:', wdaUrl)
                        } else {
                            console.warn('未获取到 WDA 端口，尝试使用默认 http://localhost:8100')
                        }
                        
                        await deviceApi.iosSchemeJump(step.url, wdaUrl)
                        // 硬性等待 2s (User Request)
                        console.log('   Wait 2s after jump...')
                        await new Promise(r => setTimeout(r, 2000))
                        break
                        
                    case 'wait':
                        // 解析时长 (支持 '3s', '3000ms' 或纯数字)
                        let ms = 1000
                        const val = String(step.target || step.value)
                        if (val.includes('s') && !val.includes('ms')) {
                             ms = parseFloat(val) * 1000
                        } else {
                             ms = parseInt(val) || 1000
                        }
                        await new Promise(r => setTimeout(r, ms))
                        break
                        
                    default:
                        // 其他暂时模拟成功 (后续对接更多 API)
                        console.warn('暂未实现的步骤类型:', step.action)
                        await new Promise(r => setTimeout(r, 500))
                        break
                }
                
                step.status = 'success'
            } catch (e) {
                console.error(`步骤 ${i+1} 执行失败:`, e)
                step.status = 'error'
                ElMessage.error(`步骤 ${i+1} 执行失败: ${e.message}`)
                // 可以选择 break 中断执行
                // break 
            } finally {
                const endTime = performance.now()
                step.duration = Math.round(endTime - startTime)
            }
            
            // 步骤间微小间隔
            await new Promise(r => setTimeout(r, 100))
        }
        ElMessage.success('执行完成')
    } catch (e) {
        ElMessage.error('执行异常: ' + e.message)
    } finally {
        isRunning.value = false
    }
}

// Inline Form Logic
function toggleInlineAdd() {
    if (showInlineAdd.value) {
        cancelInlineAdd()
    } else {
        resetInlineForm()
        showInlineAdd.value = true
        nextTick(() => { inlineFormInput.value?.focus() })
    }
}

function resetInlineForm() {
    inlineForm.value = { action: 'click', target: '', value: '', url: '' }
    editingIndex.value = -1
}

function onActionChange() {}

function cancelInlineAdd() {
    showInlineAdd.value = false
    resetInlineForm()
}

function confirmInlineAdd() {
    const actionObj = actionOptions.find(o => o.action === inlineForm.value.action)
    const newStep = {
        id: Date.now(),
        action: inlineForm.value.action,
        actionLabel: actionObj ? actionObj.value.split(' ')[0] : '自定义',
        target: inlineForm.value.target,
        value: inlineForm.value.value,
        url: inlineForm.value.url,
        status: 'pending',
        duration: 0
    }

    if (editingIndex.value > -1) {
        steps.value[editingIndex.value] = { ...steps.value[editingIndex.value], ...newStep }
    } else {
        steps.value.push(newStep)
    }
    cancelInlineAdd()
    isSaved.value = false
}

// 智能步骤输入处理
function onSmartAddStep(stepData) {
    const newStep = {
        id: Date.now(),
        action: stepData.action,
        actionLabel: stepData.actionLabel,
        target: stepData.prompt,
        value: '',
        midsceneCommand: stepData.midsceneCommand,
        status: 'pending',
        duration: 0
    }
    steps.value.push(newStep)
    isSaved.value = false
}

// 根据动作类型获取参数标签
function getParamLabel(action) {
    const labels = {
        click: '目标',
        input: '内容',
        swipe: '方向',
        wait: '时长',
        launch: '应用',
        schemeUrl: 'URL',
        schemeRouter: '路由',
        ai_act: '指令',
        ai_query: '查询',
        ai_assert: '断言',
        screenshot: '名称',
        back: '',
        home: ''
    }
    return labels[action] || '参数'
}

function editStep(index) {
    const step = steps.value[index]
    inlineForm.value = {
        action: step.action,
        target: step.target,
        value: step.value,
        url: step.url || ''
    }
    editingIndex.value = index
    showInlineAdd.value = true
}

function deleteStep(index) {
    steps.value.splice(index, 1)
    isSaved.value = false
}

watchEffect(() => {
  if (mirrorRef.value?.fps !== undefined) {
    console.log('Parent[ScriptEditorView]: mirrorRef.fps =', mirrorRef.value.fps)
  }
})
</script>

<style lang="scss" scoped>
/* Reset */
button { outline: none; }

/* Full Page Layout - 填满父容器，强制固定高度 */
.editor-page {
  background: #f8fafc;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 15px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  /* 关键：强制高度约束 */
  min-height: 0;
  max-height: 100%;
}

/* Header */
/* Editor Header - 重构后的顶部栏 */
.editor-header {
  height: 56px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: stretch;
  padding: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  z-index: 10;
}

/* 左侧设备状态部分 - 直接与设备面板对齐 */
.header-device-portion {
  width: 340px;
  min-width: 340px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between; /* 两端对齐：信息左，控制右 */
  padding: 0 12px;
  border-right: 1px solid #f1f5f9;
  background: #fff;
}

.device-info-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-name-title {
  font-weight: 700; /* 加粗 */
  font-size: 14px;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fps-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 4px;
  background: #ecfdf5;
  color: #10b981; /* 绿色 */
  /* 只在大于0时显示，避免显示 0 FPS */
  display: inline-flex;
}

.device-ctrl-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-box {
  font-size: 11px;
  border: 1px solid #e2e8f0;
  padding: 0 4px;
  border-radius: 2px;
  color: #94a3b8;
  height: 20px;
  line-height: 18px;
}

/* 覆盖 el-button link 样式，使其更紧凑 */
.device-ctrl-group .el-button {
  font-size: 12px;
  font-weight: 500;
  padding: 0 4px;
}

.device-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
}
/* 右侧脚本部分 */
.header-script-portion {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 16px;
  justify-content: flex-end; /* 内容靠右 */
  gap: 16px;
  background: #fcfcfc;
}

.script-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-right: auto; /* 把自己推到左边，后面的元素靠右 */
}

.script-icon-box {
  width: 36px;
  height: 36px;
  background: #eff6ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  font-size: 18px;
}

.script-text-group {
  display: flex;
  flex-direction: column;
}

.script-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.script-subtitle {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-btn {
  font-weight: 500;
  border-radius: 6px;
}

.run-btn {
  padding-left: 20px; 
  padding-right: 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  color: #fff;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.editor-body {
  flex: 1;
  display: flex;
  padding: 0;
  gap: 0;
  overflow: hidden;
  min-height: 0;
  height: 0; /* 关键：配合 flex:1 强制固定高度 */
}

/* Device Panel - 左侧面板，完全固定高度 */
.device-panel {
  width: 340px; 
  min-width: 340px;
  max-width: 340px;
  flex-shrink: 0;
  flex-grow: 0;
  padding: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  border-radius: 0 0 0 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  /* 关键：使用绝对定位方式固定高度 */
  align-self: stretch;

  /* device-mirror 填满父容器 */
  :deep(.device-mirror) {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 0;
    height: 100%;
    overflow: hidden;
  }
  
  /* 未连接时的 phone-frame：保持固定尺寸，不拉伸 */
  :deep(.phone-frame:not(.phone-frame--connected)) {
    flex: none !important;
    width: 220px !important;
    height: auto !important;
  }
  
  /* 连接后：device-mirror 从顶部开始 */
  :deep(.device-mirror.is-active) {
    justify-content: flex-start;
  }

  /* 连接后：phone-frame 填满 */
  :deep(.phone-frame--connected) {
    flex: 1;
    width: 100%;
    min-height: 0;
    margin: 0 !important;
    background: transparent !important;
    overflow: hidden;
  }
  
  /* 连接后的屏幕区域 */
  :deep(.phone-frame--connected .phone-screen) {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent !important;
    overflow: hidden;
  }
  
  /* 投屏图片 - 保持比例，不变形 */
  :deep(.mirror-screen) {
    width: auto;
    height: 100%;
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }
}

/* 右侧面板 - 独立滚动，不影响左侧 */
.steps-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  min-width: 0; /* 防止内容撑开 */
  background: #f8fafc;
  padding: 16px;
  border-radius: 0 0 8px 0;
  
  /* AITeachingPanel 样式覆盖 */
  :deep(.ai-teaching-panel) {
    height: calc(100% + 32px);
    margin: -16px;
    padding: 16px;
    padding-bottom: 0;
  }
  
  :deep(.panel-footer) {
    margin-bottom: 0;
  }
}

.steps-container {
    flex: 1;
    min-height: 0; /* 关键：允许 flex 子元素收缩 */
    overflow-y: auto;
    padding-right: 16px;
}

/* 包装器也需要约束 */
.steps-wrapper {
    display: flex;
    flex-direction: column;
}

.steps-list-area {
    display: flex;
    flex-direction: column;
    gap: 16px; 
}

/* Step Card Styles */
.step-row {
    position: relative;
    display: flex;
    align-items: center;
    height: 48px;
    padding: 0 24px;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    border-left: 3px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: all 0.2s;
    cursor: default;
    
    &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border-color: #d1d5db;
        border-left-color: #d1d5db;
        .hover-actions, .config-icon { opacity: 1; }
    }
    
    /* 执行中 - 左边蓝色 */
    &.status-running {
        border-left-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.12);
    }
    
    /* 执行成功 - 左边绿色 */
    &.status-success {
        border-left-color: #10b981;
    }
}

/* Left Colored Strip: 已废弃，改用 border-left */
.status-strip {
    display: none;
}

/* Index */
.step-index {
    font-family: 'MonoLisa', 'SF Mono', monospace;
    font-size: 13px;
    color: #94a3b8; /* Lighter Gray */
    width: 48px; 
    font-weight: 500;
}

/* Action Tag */
.step-tag { min-width: 70px; display: flex; align-items: center; }
.tag-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
}
/* Tag Colors */
.wait { background: #f3f4f6; color: #4b5563; }
.swipe { background: #fff7ed; color: #c2410c; }
.click { background: #eff6ff; color: #2563eb; }
.input { background: #f5f3ff; color: #7c3aed; }
.assert { background: #ecfdf5; color: #059669; }
.schemeUrl, .schemeRouter { background: #eef2ff; color: #4338ca; }
.screenshot { background: #fef3c7; color: #92400e; }
.ai_act, .ai_query, .ai_assert { background: #e0e7ff; color: #4338ca; }
.launch { background: #fce7f3; color: #be185d; }
.home, .back { background: #f3f4f6; color: #374151; }

/* Content */
.step-content {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-left: 12px;
    
    .param-label {
        background: #f1f5f9;
        color: #64748b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
        white-space: nowrap;
    }
    .target-text { font-weight: 500; color: #334155; font-size: 14px; }
    .value-pill {
        background: #f8fafc;
        color: #64748b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'SF Mono', monospace;
        border: 1px solid #e2e8f0;
    }
    .config-icon { margin-left: auto; color: #cbd5e1; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
}

/* Status */
.step-status-area {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-width: 120px;
    font-size: 13px;
    
    .pending { color: #cbd5e1; font-weight: 400; font-size: 12px; }
    
    .running { color: #3b82f6; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .spinner-ring {
        width: 14px; height: 14px;
        border: 2px solid #3b82f6; border-top-color: transparent; border-radius: 50%;
        animation: rotate 1s linear infinite;
    }
    
    .success {
        display: flex; align-items: center; gap: 8px;
        .duration-text { color: #94a3b8; font-size: 12px; font-family: 'SF Mono', monospace; }
        .check-circle { 
            width: 16px; height: 16px; background: #10b981; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-size: 10px;
        }
    }
    
    .hover-actions { margin-left:12px; opacity: 0; transition: opacity 0.2s; }
}

@keyframes rotate { to { transform: rotate(360deg); } }

/* Inline Form */
.add-step-wrapper { margin-top: 16px; }

.add-trigger-btn {
    height: 56px;
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    &:hover { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }
}

.inline-add-form {
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    .form-row { display: flex; gap: 16px; margin-bottom: 20px; }
    .form-footer { display: flex; gap: 12px; }
}

/* ========== 教学模式新增样式 ========== */

/* 模式切换器 - 右侧图标按钮组 */
.mode-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid #e2e8f0;
}

.mode-item {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s;
  
  &:hover {
    background: #f1f5f9;
    color: #64748b;
  }
  
  &.active {
    background: #10b981; /* 绿色 */
    color: #fff;
    box-shadow: 0 2px 6px rgba(16, 185, 129, 0.3);
  }
  
  &.teach.active {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: #fff;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
  }
}

/* 教学模式信息 */
.teach-info {
  display: flex;
  flex-direction: column;
  margin-right: auto; /* 把自己推到左边 */
  .page-name { font-size: 14px; font-weight: 600; color: #1e293b; }
  .update-time { font-size: 11px; color: #94a3b8; }
}

/* 当前模型徽章 */
.current-model-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 11px;
  color: #64748b;
  margin-right: 8px;
  
  .el-icon {
    color: #6366f1;
  }
}

/* AI 分析按钮 */
.ai-analyze-btn {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  border: none !important;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
  &:hover { 
    background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  }
}

/* 元素框选层 */
// ElementOverlay 在 DeviceMirror slot 中，样式由组件自身控制
.element-overlay-layer {
  position: absolute;
  inset: 0;
  z-index: 10;
}

/* 扫描动效 */
.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  background: rgba(15, 23, 42, 0.4);
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
  background: linear-gradient(90deg, transparent 0%, rgba(99, 102, 241, 0.3) 20%, rgba(99, 102, 241, 0.8) 50%, rgba(99, 102, 241, 0.3) 80%, transparent 100%);
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { top: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
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

/* AI 配置弹窗 */
.form-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}
</style>
