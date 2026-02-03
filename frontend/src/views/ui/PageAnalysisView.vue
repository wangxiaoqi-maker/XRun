<template>
  <div class="page-analysis">
    <!-- 顶部工具栏 -->
    <div class="analysis-header">
      <!-- 左侧：返回 + 设备状态 -->
      <div class="header-left">
        <el-button text @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="divider"></div>
        <template v-if="mirrorRef?.selectedDevice">
          <div class="device-status connected"></div>
          <span class="device-name">{{ mirrorRef?.selectedDevice?.name || mirrorRef?.selectedDevice?.model }}</span>
          <el-button text type="danger" size="small" @click="disconnectDevice" class="disconnect-btn">
            断开
          </el-button>
        </template>
        <template v-else>
          <div class="device-status disconnected"></div>
          <span class="device-name text-muted">未连接设备</span>
        </template>
      </div>
      
      <!-- 右侧：操作按钮 -->
      <div class="header-right">
        <!-- 当前模型 -->
        <div v-if="currentModelName" class="model-badge">
          <span>{{ currentModelName }}</span>
        </div>
        
        <el-button text :disabled="!mirrorRef?.connected || !analysisElements.length" @click="clearAnalysis" title="清空">
          <el-icon><Delete /></el-icon>
        </el-button>
        
        <el-button 
          type="primary"
          :loading="analyzing"
          :disabled="!mirrorRef?.connected"
          @click="openAnalyzeConfig"
          class="analyze-btn"
        >
          <el-icon v-if="!analyzing"><MagicStick /></el-icon>
          {{ analyzing ? '分析中...' : 'AI 分析' }}
        </el-button>
      </div>
    </div>
    
    <!-- 主体内容 -->
    <div class="analysis-body">
      <!-- 左侧：设备投屏 -->
      <div class="device-panel">
        <DeviceMirror 
          ref="mirrorRef"
          :hide-header="true"
          @device-connected="onDeviceConnected"
        >
          <!-- 元素框选 Overlay -->
          <template #overlay="{ deviceWidth: dw, deviceHeight: dh, imgRect }">
            <ElementOverlay
              v-if="mirrorRef?.connected && analysisElements.length > 0"
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
        
        <!-- 扫描动效 -->
        <div v-if="analyzing" class="scan-overlay">
          <div class="scan-line"></div>
          <div class="scan-text">AI 正在分析页面...</div>
        </div>
      </div>
      
      <!-- 右侧：AI 分析面板 -->
      <div class="result-panel">
        <AITeachingPanel
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
          :is-saved="analysisResult?.is_saved"
          @update:page-summary="pageSummary = $event"
          @hover="hoveredElementId = $event"
          @leave="hoveredElementId = null"
          @remove-element="onRemoveElement"
          @save="saveToKnowledge"
          @cancel="clearAnalysis"
        />
      </div>
    </div>
    
    <!-- AI 分析配置弹窗 -->
    <el-dialog 
      v-model="showAnalyzeDialog" 
      title="AI 分析配置" 
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form label-position="top">
        <el-form-item label="选择应用" required>
          <el-select 
            v-model="analyzeConfig.appId" 
            placeholder="请选择被测应用" 
            style="width: 100%"
            filterable
            @change="onAppChange"
          >
            <el-option
              v-for="app in appList"
              :key="app.id"
              :label="`${app.name}${app.name_en ? ' (' + app.name_en + ')' : ''}`"
              :value="app.id"
            >
              <span style="display: flex; align-items: center; gap: 8px;">
                <span v-if="app.icon_url" style="width: 20px; height: 20px; border-radius: 4px; overflow: hidden;">
                  <img :src="app.icon_url" style="width: 100%; height: 100%; object-fit: cover;" />
                </span>
                <span v-else style="width: 20px; height: 20px; border-radius: 4px; background: #184BFA; color: white; display: flex; align-items: center; justify-content: center; font-size: 12px;">
                  {{ app.name?.charAt(0) }}
                </span>
                <span>{{ app.name }}{{ app.name_en ? ' (' + app.name_en + ')' : '' }}</span>
              </span>
            </el-option>
          </el-select>
          <div class="form-tip">分析的页面将关联到此应用</div>
        </el-form-item>
        <el-form-item label="选择视觉模型">
          <el-select v-model="analyzeConfig.modelId" placeholder="选择模型" style="width: 100%">
            <el-option
              v-for="model in visionModels"
              :key="model.id"
              :label="`${model.name} (${model.provider?.name || '未知供应商'})`"
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属模块（可选）">
          <el-select 
            v-model="analyzeConfig.moduleId" 
            placeholder="选择业务模块" 
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="module in moduleList"
              :key="module.id"
              :label="module.module_name"
              :value="module.id"
            />
          </el-select>
          <div class="form-tip">将页面归类到指定模块，便于管理</div>
        </el-form-item>
        <el-form-item label="页面标题（可选）">
          <el-input
            v-model="analyzeConfig.pageTitle"
            placeholder="如不填写，将由 AI 自动识别"
          />
          <div class="form-tip">手动指定页面标题，AI 将使用该名称</div>
        </el-form-item>
        <el-form-item label="页面上下文提示（可选）">
          <el-input
            v-model="analyzeConfig.contextHint"
            type="textarea"
            :rows="2"
            placeholder="例如：这是从首页点击财富Tab后跳转的页面"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAnalyzeDialog = false">取消</el-button>
        <el-button type="primary" :loading="analyzing" @click="startAnalyze" :disabled="!analyzeConfig.appId">
          开始分析
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Delete, MagicStick, Cpu } from '@element-plus/icons-vue'
import DeviceMirror from '@/components/DeviceMirror.vue'
import ElementOverlay from '@/components/ElementOverlay.vue'
import AITeachingPanel from '@/components/AITeachingPanel.vue'
import { knowledgeApi, deviceApi, llmApi, appApi } from '@/api'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()

defineOptions({ name: 'PageAnalysisView' })

const router = useRouter()
const route = useRoute()

// 组件引用
const mirrorRef = ref(null)
const teachingPanelRef = ref(null)

// 状态
const connectedDevice = ref(null)
const deviceWidth = ref(1080)
const deviceHeight = ref(2400)

// 分析状态
const analyzing = ref(false)
const savingToKnowledge = ref(false)
const analysisResult = ref(null)
const analysisElements = ref([])
const analysisScreenshot = ref('')
const pageSummary = ref('')

// 交互状态
const hoveredElementId = ref(null)
const selectedElementId = ref(null)

// 模型配置
const visionModels = ref([])
const showAnalyzeDialog = ref(false)
const analyzeConfig = ref({
  providerId: '',
  modelId: '',
  pageTitle: '',
  contextHint: '',
  appId: '',
  moduleId: ''
})

// 应用列表
const appList = ref([])

// 模块列表
const moduleList = ref([])

// 计算当前模型名称
const currentModelName = computed(() => {
  if (!analyzeConfig.value.modelId) return ''
  const model = visionModels.value.find(m => m.id === analyzeConfig.value.modelId)
  return model?.name || ''
})

// 设备连接
function onDeviceConnected(device) {
  connectedDevice.value = device
  ElMessage.success('设备已连接')
  if (device?.resolution) {
    const [w, h] = device.resolution.split('x').map(Number)
    if (w && h) {
      deviceWidth.value = w
      deviceHeight.value = h
    }
  }
}

// 加载视觉模型列表
async function loadVisionModels() {
  try {
    const res = await llmApi.listModels({ include_disabled: false })
    visionModels.value = (res.data.models || []).filter(m => m.supports_vision)
    if (visionModels.value.length > 0 && !analyzeConfig.value.modelId) {
      const first = visionModels.value[0]
      analyzeConfig.value.providerId = first.provider_id
      analyzeConfig.value.modelId = first.id
    }
  } catch (e) {
    console.error('加载模型列表失败:', e)
  }
}

// 加载应用列表（按当前项目筛选）
async function loadAppList() {
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
      // 加载该应用的模块
      loadModuleList(appList.value[0].id)
    }
  } catch (e) {
    console.error('加载应用列表失败:', e)
  }
}

// 加载模块列表
async function loadModuleList(appId) {
  if (!appId) {
    moduleList.value = []
    return
  }
  try {
    const res = await knowledgeApi.getModuleTree(appId)
    moduleList.value = res.data?.modules || []
  } catch (e) {
    console.error('加载模块列表失败:', e)
    moduleList.value = []
  }
}

// 切换应用时加载模块
function onAppChange(appId) {
  analyzeConfig.value.moduleId = ''
  loadModuleList(appId)
}

// 打开分析配置弹窗
function openAnalyzeConfig() {
  showAnalyzeDialog.value = true
}

// 开始分析
async function startAnalyze() {
  if (!mirrorRef.value?.connected || !connectedDevice.value) {
    ElMessage.warning('请先连接设备')
    return
  }
  
  showAnalyzeDialog.value = false
  analyzing.value = true
  
  try {
    // 获取截图
    const wdaPort = mirrorRef.value?.wdaPort || 0
    const screenshotRes = await deviceApi.screenshotBase64(
      connectedDevice.value.udid,
      connectedDevice.value.platform,
      wdaPort
    )
    
    if (!screenshotRes.data?.screenshot) {
      throw new Error('获取截图失败')
    }
    
    analysisScreenshot.value = screenshotRes.data.screenshot
    
    // 调用 AI 分析
    const selectedModel = visionModels.value.find(m => m.id === analyzeConfig.value.modelId)
    const selectedApp = appList.value.find(a => a.id === analyzeConfig.value.appId)
    
    const result = await knowledgeApi.analyzePage({
      image_data: screenshotRes.data.screenshot,
      app_id: analyzeConfig.value.appId,
      project_id: projectStore.currentProject?.id || undefined,
      app_name: selectedApp?.name || connectedDevice.value.name || '未知应用',
      platform: selectedApp?.platform || connectedDevice.value.platform,
      device_udid: connectedDevice.value.udid,
      device_resolution: connectedDevice.value.resolution,
      context_hint: analyzeConfig.value.contextHint || undefined,
      skip_duplicate: false,
      provider_id: selectedModel?.provider_id || undefined,
      model_id: analyzeConfig.value.modelId || undefined
    })
    
    analysisResult.value = result.data
    analysisElements.value = result.data.elements || []
    pageSummary.value = result.data.page_description || ''
    
    // 添加模块 ID（用于保存时关联）
    if (analyzeConfig.value.moduleId) {
      analysisResult.value.module_id = analyzeConfig.value.moduleId
      if (analysisResult.value.save_meta) {
        analysisResult.value.save_meta.module_id = analyzeConfig.value.moduleId
      }
    }
    
    // 如果用户指定了页面标题，覆盖 AI 识别的结果
    if (analyzeConfig.value.pageTitle) {
      analysisResult.value.page_name = analyzeConfig.value.pageTitle
      if (analysisResult.value.save_meta) {
        analysisResult.value.save_meta.raw_result.page_name = analyzeConfig.value.pageTitle
      }
    }
    
    ElMessage.success(`分析完成，发现 ${analysisElements.value.length} 个元素`)
  } catch (e) {
    console.error('AI 分析失败:', e)
    ElMessage.error(e.response?.data?.detail || 'AI 分析失败')
  } finally {
    analyzing.value = false
  }
}

// 清空分析结果
function clearAnalysis() {
  analysisResult.value = null
  analysisElements.value = []
  analysisScreenshot.value = ''
  pageSummary.value = ''
  hoveredElementId.value = null
  selectedElementId.value = null
}

// 移除元素
function onRemoveElement(id) {
  analysisElements.value = analysisElements.value.filter(e => e.id !== id)
}

// 保存到知识库
async function saveToKnowledge() {
  if (!analysisResult.value) {
    ElMessage.warning('请先进行 AI 分析')
    return
  }
  
  if (analysisResult.value.is_saved) {
    ElMessage.info('该分析结果已保存到知识库')
    return
  }
  
  savingToKnowledge.value = true
  try {
    const res = await knowledgeApi.saveToKnowledgeBase(analysisResult.value)
    if (res.data?.success !== false) {
      ElMessage.success(res.data.message || '已保存到知识库')
      analysisResult.value.is_saved = true
      analysisResult.value.page_id = res.data.page_id
      
      // 保存成功后跳转到详情页
      setTimeout(() => {
        router.push(`/ui/knowledge/${res.data.page_id}`)
      }, 1000)
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

// 断开设备连接
function disconnectDevice() {
  if (mirrorRef.value) {
    mirrorRef.value.disconnect()
  }
}

// 返回列表并关闭当前标签页
function goBack() {
  // 先断开设备
  disconnectDevice()
  // 跳转回列表
  router.push('/ui/knowledge')
}

onMounted(() => {
  loadVisionModels()
  loadAppList()
})
</script>

<style scoped>
.page-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶部工具栏 */
.analysis-header {
  height: 52px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  font-size: 14px;
  color: #64748b;
}

.back-btn:hover {
  color: #3b82f6;
}

.divider {
  width: 1px;
  height: 20px;
  background: #e2e8f0;
}

.device-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.device-status.connected {
  background: #10b981;
}

.device-status.disconnected {
  background: #94a3b8;
}

.device-name {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.device-name.text-muted {
  color: #94a3b8;
}

.fps-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 4px;
  color: #64748b;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  color: #64748b;
}

.analyze-btn {
  min-width: 130px;
}

/* 主体内容 */
.analysis-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧设备面板 - 与 ScriptEditorView 保持一致 */
.device-panel {
  width: 340px;
  min-width: 340px;
  max-width: 340px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  position: relative;
}

/* 扫描动效 */
.scan-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 10;
}

.scan-line {
  width: 60%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  animation: scan 2s ease-in-out infinite;
}

@keyframes scan {
  0%, 100% { transform: translateY(-80px); opacity: 0; }
  50% { transform: translateY(80px); opacity: 1; }
}

.scan-text {
  margin-top: 16px;
  color: #3b82f6;
  font-size: 14px;
  font-weight: 500;
}

/* 右侧结果面板 - 与 ScriptEditorView 的 steps-panel 保持一致 */
.result-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  overflow: hidden;
}

/* 确保底部操作栏可见 */
.result-panel :deep(.ai-teaching-panel) {
  height: 100%;
  margin: 0;
  padding: 16px;
  padding-bottom: 0;
}

.result-panel :deep(.panel-footer) {
  margin-left: -16px;
  margin-right: -16px;
  margin-bottom: 0;
  border-bottom: none;
}

/* 断开按钮样式 */
.disconnect-btn {
  margin-left: 8px;
  font-size: 12px;
}

/* 表单提示 */
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
