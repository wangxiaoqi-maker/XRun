<template>
  <div class="ai-teaching-panel">
    <!-- 空状态 -->
    <div v-if="!elements.length && !analyzing" class="empty-state">
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
              <div class="thumb-placeholder">
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
        <div class="storage-hint">预计消耗向量存储: {{ estimatedStorage }}KB</div>
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
import { ref, computed, watch } from 'vue'

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
  'cancel'
])

const localPageSummary = ref(props.pageSummary)

watch(() => props.pageSummary, (val) => {
  localPageSummary.value = val
})

// 预估存储大小
const estimatedStorage = computed(() => {
  return Math.round(props.elements.length * 2.5)
})

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
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  overflow: hidden;
  padding: 16px;
  padding-bottom: 0;
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
}

// 添加元素卡片
.add-element-card {
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  min-height: 120px;
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

// 底部操作栏 - 固定在底部
.panel-footer {
  padding: 12px 16px;
  margin: 0 -16px; /* 抵消父容器的 padding */
  background: white;
  border-top: 1px solid #e2e8f0;
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

.storage-hint {
  font-size: 10px;
  color: #94a3b8;
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
