<template>
  <div class="ai-teaching-panel">
    <!-- 分析中状态 - 工具调用日志风格 -->
    <div v-if="analyzing" class="analyzing-state">
      <div class="analysis-log">
        <!-- 步骤1: 截图获取 -->
        <div class="log-section">
          <div class="log-title">获取当前页面截图</div>
          <div class="log-card done">
            <div class="card-left">
              <span class="card-icon done">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </span>
              <span class="card-action">截图获取</span>
              <span class="card-status">完成</span>
              <span class="card-tag">local</span>
            </div>
            <div class="card-right">
              <span class="card-time">0.5s</span>
            </div>
          </div>
        </div>
        
        <!-- 步骤2: 调用视觉模型 -->
        <div class="log-section">
          <div class="log-title">调用视觉大模型分析页面元素</div>
          <div class="log-card active">
            <div class="card-left">
              <span class="card-icon loading">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
                </svg>
              </span>
              <span class="card-action">AI 视觉分析</span>
              <span class="card-status running">执行中...</span>
              <span class="card-tag">{{ currentModelName || 'vision' }}</span>
            </div>
            <div class="card-right">
              <span class="card-time counting">{{ analysisTimer }}s</span>
            </div>
          </div>
        </div>
        
        <!-- 步骤3: 元素解析 (待执行) -->
        <div class="log-section pending">
          <div class="log-title">解析识别结果，提取元素信息</div>
          <div class="log-card pending">
            <div class="card-left">
              <span class="card-icon pending">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                </svg>
              </span>
              <span class="card-action">元素解析</span>
              <span class="card-status">等待中</span>
            </div>
          </div>
        </div>
        
        <!-- 步骤4: 坐标计算 (待执行) -->
        <div class="log-section pending">
          <div class="log-title">计算元素位置坐标</div>
          <div class="log-card pending">
            <div class="card-left">
              <span class="card-icon pending">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                </svg>
              </span>
              <span class="card-action">坐标计算</span>
              <span class="card-status">等待中</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-else-if="!elements.length" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 21l-6-6m6 6v-4.5m0 4.5h-4.5M3 16.5V21m0 0h4.5M3 21l6-6M21 7.5V3m0 0h-4.5M21 3l-6 6M3 7.5V3m0 0h4.5M3 3l6 6"/>
        </svg>
      </div>
      <p class="empty-title">知识库暂无当前页面数据</p>
      <p class="empty-desc">点击右上角「AI 全页分析」按钮开始扫描</p>
    </div>
    
    <!-- 分析结果 -->
    <div v-else class="result-container">
      <!-- 页面摘要 -->
      <div class="page-summary">
        <div class="summary-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14 2z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <div class="summary-content">
          <label class="summary-label">PAGE SUMMARY & CONTEXT</label>
          <textarea 
            v-model="localPageSummary"
            rows="2"
            class="summary-textarea"
            placeholder="请输入页面描述..."
            @input="onSummaryChange"
          ></textarea>
        </div>
      </div>
      
      <!-- 元素列表 -->
      <div class="elements-grid">
        <div 
          v-for="(element, index) in elements"
          :key="element.id"
          :id="'element-card-' + element.id"
          class="element-card"
          :class="{ 'is-hovered': hoveredId === element.id }"
          @mouseenter="onElementHover(element.id)"
          @mouseleave="onElementLeave()"
        >
          <!-- 卡片头部 -->
          <div class="card-header">
            <!-- 元素缩略图 -->
            <div class="element-thumb">
              <img 
                v-if="getElementCrop(element)" 
                :src="getElementCrop(element)" 
                class="thumb-image"
                :alt="element.element_name"
              />
              <div v-else class="thumb-placeholder">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21 15 16 10 5 21"/>
                </svg>
              </div>
            </div>
            
            <!-- 元素信息 -->
            <div class="element-info">
              <div class="info-top">
                <input 
                  v-model="element.element_name"
                  class="element-name-input"
                  @change="onElementChange(element)"
                />
                <span class="confidence-badge">{{ element.confidence_score || 95 }}%</span>
              </div>
              
              <div class="element-tags">
                <span 
                  class="type-tag"
                  :class="getTypeClass(element.element_type)"
                >
                  {{ element.element_type || 'Button' }}
                </span>
                <span v-if="element.text_content" class="text-tag">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 7V4h16v3M9 20h6M12 4v16"/>
                  </svg>
                  {{ element.text_content }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 视觉描述 -->
          <div class="card-body">
            <label class="desc-label">VISUAL CONTEXT</label>
            <textarea 
              v-model="element.description"
              rows="2"
              class="desc-textarea"
              @change="onElementChange(element)"
            ></textarea>
            
            <!-- 操作按钮 -->
            <div class="card-actions">
              <!-- 探索按钮：点击元素并记录跳转 -->
              <button 
                v-if="explorationEnabled && currentPageId" 
                class="action-btn explore" 
                title="点击并探索跳转"
                @click="onExploreElement(element)"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="11" cy="11" r="8"/>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                  <line x1="11" y1="8" x2="11" y2="14"/>
                  <line x1="8" y1="11" x2="14" y2="11"/>
                </svg>
              </button>
              <button class="action-btn" title="重新生成">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                </svg>
              </button>
              <button class="action-btn delete" title="删除" @click="onRemoveElement(element.id)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        <!-- 添加元素卡片 -->
        <div class="add-element-card" @click="$emit('add-element')">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span>手动添加元素</span>
        </div>
      </div>
    </div>
    
    <!-- 底部操作栏 -->
    <div v-if="elements.length > 0" class="panel-footer">
      <div class="footer-left">
        <div class="element-count">
          已识别 <span class="count-num">{{ elements.length }}</span> 个元素
        </div>
        <div class="footer-stats">
          <span v-if="processingTime" class="stat-item time">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            本次耗时: {{ processingTime.toFixed(1) }}s
          </span>
          <span v-if="usage?.total_tokens" class="stat-item tokens">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
            本次消耗: {{ formatTokens(usage.total_tokens) }}
          </span>
          <span class="stat-item storage">预计存储: {{ estimatedStorage }}KB</span>
          <!-- 探索模式统计 -->
          <span v-if="explorationEnabled && explorationStats.pages_discovered > 0" class="stat-item exploration">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            图谱: {{ explorationStats.pages_discovered }}页 / {{ explorationStats.transitions_count }}跳转
          </span>
        </div>
      </div>
      <div class="footer-right">
        <button class="btn-secondary" @click="$emit('cancel')">取消变更</button>
        <button class="btn-primary" @click="onSave" :disabled="saving">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
            <polyline points="17 21 17 13 7 13 7 21"></polyline>
            <polyline points="7 3 7 8 15 8"></polyline>
          </svg>
          {{ saving ? '保存中...' : '保存到知识库' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  elements: {
    type: Array,
    default: () => []
  },
  pageSummary: {
    type: String,
    default: ''
  },
  hoveredId: {
    type: [String, Number],
    default: null
  },
  analyzing: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  },
  processingTime: {
    type: Number,
    default: 0
  },
  usage: {
    type: Object,
    default: () => ({})
  },
  screenshot: {
    type: String,
    default: ''
  },
  currentModelName: {
    type: String,
    default: ''
  },
  // 探索模式相关
  explorationEnabled: {
    type: Boolean,
    default: true
  },
  explorationStats: {
    type: Object,
    default: () => ({ pages_discovered: 0, transitions_count: 0 })
  },
  currentPageId: {
    type: String,
    default: null
  }
})

// 分析计时器
const analysisTimer = ref(0)
let timerInterval = null

watch(() => props.analyzing, (isAnalyzing) => {
  if (isAnalyzing) {
    // 开始计时
    analysisTimer.value = 0
    timerInterval = setInterval(() => {
      analysisTimer.value++
    }, 1000)
  } else {
    // 停止计时
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})

const emit = defineEmits([
  'update:pageSummary',
  'update:elements',
  'hover',
  'leave',
  'remove-element',
  'add-element',
  'save',
  'cancel',
  'element-click'  // 探索模式：元素点击事件
])

const localPageSummary = ref(props.pageSummary)

watch(() => props.pageSummary, (val) => {
  localPageSummary.value = val
})

// 截图图片对象和尺寸
const screenshotImage = ref(null)
const imageSize = ref({ width: 0, height: 0 })

// 加载截图
watch(() => props.screenshot, (newVal) => {
  if (newVal) {
    const img = new Image()
    img.onload = () => {
      screenshotImage.value = img
      imageSize.value = { width: img.width, height: img.height }
    }
    img.src = `data:image/png;base64,${newVal}`
  } else {
    screenshotImage.value = null
  }
}, { immediate: true })

// 元素切图缓存
const elementCrops = ref({})

// 生成所有元素的切图
watch([screenshotImage, () => props.elements], () => {
  if (!screenshotImage.value || !props.elements.length) {
    elementCrops.value = {}
    return
  }
  
  const img = screenshotImage.value
  const crops = {}
  
  for (const element of props.elements) {
    if (!element.bbox || !element.id) continue
    
    const bbox = Array.isArray(element.bbox) ? element.bbox : null
    if (!bbox || bbox.length !== 4) continue
    
    // bbox 格式: [left%, top%, width%, height%]
    const [leftPct, topPct, widthPct, heightPct] = bbox
    
    // 转换为像素坐标
    const x = Math.round((leftPct / 100) * img.width)
    const y = Math.round((topPct / 100) * img.height)
    const w = Math.round((widthPct / 100) * img.width)
    const h = Math.round((heightPct / 100) * img.height)
    
    // 边界检查
    if (w <= 0 || h <= 0 || x < 0 || y < 0) continue
    
    try {
      const canvas = document.createElement('canvas')
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, x, y, w, h, 0, 0, w, h)
      crops[element.id] = canvas.toDataURL('image/png')
    } catch (e) {
      // 忽略裁剪失败
    }
  }
  
  elementCrops.value = crops
}, { immediate: true })

// 获取元素切图 URL
function getElementCrop(element) {
  return elementCrops.value[element.id] || null
}

// 预估存储大小
const estimatedStorage = computed(() => {
  return Math.round(props.elements.length * 2.5)
})

// 格式化 token 数量（超过1000显示为 xK）
function formatTokens(tokens) {
  if (!tokens) return '0'
  if (tokens >= 1000) {
    return (tokens / 1000).toFixed(1) + 'K'
  }
  return tokens.toString()
}

function getTypeClass(type) {
  const typeMap = {
    'button': 'type-button',
    'icon_button': 'type-button',
    'text_input': 'type-input',
    'input': 'type-input',
    'icon': 'type-icon',
    'text': 'type-text',
    'link': 'type-link',
    'tab': 'type-tab'
  }
  return typeMap[type?.toLowerCase()] || 'type-default'
}

function onSummaryChange() {
  emit('update:pageSummary', localPageSummary.value)
}

function onElementHover(id) {
  emit('hover', id)
}

function onElementLeave() {
  emit('leave')
}

function onElementChange(element) {
  // 通知父组件元素已修改
}

function onRemoveElement(id) {
  emit('remove-element', id)
}

function onExploreElement(element) {
  // 触发探索：点击元素并记录跳转
  emit('element-click', element)
}

function onSave() {
  emit('save')
}

// 滚动到指定元素卡片
function scrollToElement(id) {
  const el = document.getElementById('element-card-' + id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

defineExpose({
  scrollToElement
})
</script>

<style lang="scss" scoped>
.ai-teaching-panel {
  height: calc(100% + 32px); /* 补偿父容器的 padding */
  margin: -16px; /* 抵消父容器 steps-panel 的 padding */
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  overflow: hidden;
  padding: 16px;
  padding-bottom: 0;
}

// 分析中状态 - 工具调用日志风格
.analyzing-state {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.analysis-log {
  .log-section {
    margin-bottom: 16px;
    
    &.pending {
      opacity: 0.5;
    }
  }
  
  .log-title {
    font-size: 14px;
    color: #1e293b;
    margin-bottom: 8px;
    font-weight: 500;
  }
  
  .log-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    transition: all 0.2s;
    
    &.active {
      border-color: #6366f1;
      background: #fafaff;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    &.done {
      border-color: #10b981;
      background: #f0fdf4;
    }
    
    &.pending {
      background: #f8fafc;
      border-style: dashed;
    }
  }
  
  .card-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .card-icon {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &.done {
      background: #dcfce7;
      color: #10b981;
    }
    
    &.loading {
      background: #eef2ff;
      color: #6366f1;
      
      svg {
        animation: spin 1s linear infinite;
      }
    }
    
    &.pending {
      background: #f1f5f9;
      color: #94a3b8;
    }
  }
  
  .card-action {
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
  }
  
  .card-status {
    font-size: 12px;
    color: #64748b;
    
    &.running {
      color: #6366f1;
    }
  }
  
  .card-tag {
    font-size: 11px;
    padding: 2px 8px;
    background: #dbeafe;
    color: #3b82f6;
    border-radius: 10px;
    font-weight: 500;
  }
  
  .card-right {
    display: flex;
    align-items: center;
  }
  
  .card-time {
    font-size: 12px;
    color: #94a3b8;
    font-family: monospace;
    
    &.counting {
      color: #6366f1;
      font-weight: 600;
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// 空状态
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  
  .empty-icon {
    width: 80px;
    height: 80px;
    background: #e2e8f0;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    margin-bottom: 20px;
  }
  
  .empty-title {
    font-size: 16px;
    font-weight: 500;
    color: #64748b;
    margin: 0 0 8px;
  }
  
  .empty-desc {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

// 结果容器 - 可滚动区域
.result-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 8px; /* 为滚动条留出空间 */
  margin-right: -8px;
  
  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
    &:hover {
      background: #94a3b8;
    }
  }
}

// 页面摘要
.page-summary {
  background: white;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
  
  .summary-icon {
    width: 40px;
    height: 40px;
    background: #eef2ff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6366f1;
    flex-shrink: 0;
  }
  
  .summary-content {
    flex: 1;
    min-width: 0;
  }
  
  .summary-label {
    display: block;
    font-size: 10px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
  }
  
  .summary-textarea {
    width: 100%;
    border: none;
    background: transparent;
    font-size: 13px;
    color: #334155;
    resize: none;
    outline: none;
    line-height: 1.5;
    
    &::placeholder {
      color: #cbd5e1;
    }
  }
}

// 元素网格
.elements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

// 元素卡片
.element-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.2s;
  
  &:hover {
    border-color: #a5b4fc;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  }
  
  &.is-hovered {
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  }
}

.card-header {
  padding: 12px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(to bottom, white, #fafbfc);
}

.element-thumb {
  width: 48px;
  height: 48px;
  background: #e2e8f0;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  overflow: hidden;
  flex-shrink: 0;
  
  .thumb-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  
  .thumb-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
  }
}

.element-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.info-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.element-name-input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  outline: none;
  padding: 0;
  
  &:hover {
    color: #6366f1;
  }
  
  &:focus {
    color: #6366f1;
  }
}

.confidence-badge {
  font-size: 9px;
  font-family: 'Monaco', monospace;
  padding: 2px 6px;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 10px;
  flex-shrink: 0;
}

.element-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.type-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid;
  
  &.type-button {
    background: #eff6ff;
    color: #3b82f6;
    border-color: #bfdbfe;
  }
  
  &.type-input {
    background: #f0fdf4;
    color: #22c55e;
    border-color: #bbf7d0;
  }
  
  &.type-icon {
    background: #fff7ed;
    color: #f97316;
    border-color: #fed7aa;
  }
  
  &.type-text {
    background: #f8fafc;
    color: #64748b;
    border-color: #e2e8f0;
  }
  
  &.type-default {
    background: #f8fafc;
    color: #64748b;
    border-color: #e2e8f0;
  }
}

.text-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-body {
  padding: 12px;
  position: relative;
  
  .desc-label {
    display: block;
    font-size: 9px;
    font-weight: 600;
    color: #cbd5e1;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  
  .desc-textarea {
    width: 100%;
    border: 1px solid transparent;
    background: #f8fafc;
    font-size: 12px;
    color: #475569;
    border-radius: 6px;
    padding: 8px;
    resize: none;
    outline: none;
    transition: all 0.2s;
    line-height: 1.5;
    
    &:hover {
      background: white;
      border-color: #e2e8f0;
    }
    
    &:focus {
      background: white;
      border-color: #a5b4fc;
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
    }
  }
}

.card-actions {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  background: white;
  padding-left: 8px;
  border-radius: 4px;
  
  .element-card:hover & {
    opacity: 1;
  }
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #94a3b8;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  
  &:hover {
    background: #f1f5f9;
    color: #6366f1;
  }
  
  &.delete:hover {
    background: #fef2f2;
    color: #ef4444;
  }
  
  &.explore {
    color: #10b981;
    
    &:hover {
      background: #ecfdf5;
      color: #059669;
    }
  }
}

// 添加元素卡片
.add-element-card {
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  min-height: 120px;
  margin-bottom: 10px; /* 与底部栏的间距 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    border-color: #a5b4fc;
    color: #6366f1;
    background: rgba(99, 102, 241, 0.02);
  }
  
  span {
    font-size: 12px;
    font-weight: 500;
  }
}

// 底部操作栏 - 固定在底部，左右延伸到边缘
.panel-footer {
  height: 48px; /* 固定高度，与左侧对齐 */
  padding: 0 16px;
  margin: auto -16px 0 -16px; /* margin-top: auto 贴底，左右延伸 */
  background: white;
  border: 1px solid #e2e8f0;
  border-left: none;
  border-right: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.element-count {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 6px 12px;
  border-radius: 20px;
  
  .count-num {
    color: #6366f1;
    font-weight: 600;
  }
}

.footer-stats {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #475569;
  font-weight: 500;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 12px;
  
  svg {
    opacity: 0.7;
  }
  
  &.time {
    color: #6366f1;
    background: #eef2ff;
  }
  
  &.tokens {
    color: #059669;
    background: #ecfdf5;
  }
  
  &.storage {
    color: #94a3b8;
    background: transparent;
    font-weight: 400;
    padding: 0;
  }
  
  &.exploration {
    color: #8b5cf6;
    background: #f5f3ff;
  }
}

.footer-right {
  display: flex;
  gap: 12px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid #e2e8f0;
  background: white;
  color: #475569;
  font-size: 12px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: #f8fafc;
  }
}

.btn-primary {
  padding: 8px 20px;
  border: none;
  background: #6366f1;
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  
  &:hover {
    background: #4f46e5;
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
  }
  
  &:active {
    transform: scale(0.98);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}
</style>
