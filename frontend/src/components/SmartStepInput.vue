<template>
  <div class="smart-step-input" :class="{ 'has-action': selectedAction }">
    <!-- 已选择的动作标签 -->
    <div v-if="selectedAction" class="action-tag" :class="selectedAction.id" @click="clearAction">
      <span class="tag-text">{{ selectedAction.label }}</span>
      <span class="tag-close">×</span>
    </div>
    
    <input
      ref="inputRef"
      v-model="inputText"
      class="step-input"
      :placeholder="placeholder"
      @input="onInput"
      @keydown.down.prevent="navigate(1)"
      @keydown.up.prevent="navigate(-1)"
      @keydown.enter.prevent="onEnter"
      @keydown.escape="closeSuggestions"
      @keydown.backspace="onBackspace"
      @focus="onFocus"
      @blur="onBlur"
    />
    
    <!-- 联想下拉列表 -->
    <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-dropdown">
      <div
        v-for="(item, index) in suggestions"
        :key="item.id"
        class="suggestion-item"
        :class="{ active: highlightIndex === index }"
        @mousedown.prevent="selectItem(item)"
        @mouseenter="highlightIndex = index"
      >
        {{ item.label }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

const emit = defineEmits(['add-step'])

// 状态
const inputRef = ref(null)
const inputText = ref('')
const highlightIndex = ref(0)
const showSuggestions = ref(false)
const selectedAction = ref(null)

// 动作列表
const actions = [
  { id: 'click', label: '点击', keywords: ['点击', 'click', 'tap'] },
  { id: 'input', label: '输入', keywords: ['输入', 'input', '填写'] },
  { id: 'swipe', label: '滑动', keywords: ['滑动', 'swipe', 'scroll'] },
  { id: 'screenshot', label: '截图', keywords: ['截图', 'screenshot'] },
  { id: 'ai_act', label: 'AI操作', keywords: ['ai', '操作', 'action'] },
  { id: 'ai_query', label: 'AI查询', keywords: ['ai', '查询', 'query'] },
  { id: 'ai_assert', label: 'AI断言', keywords: ['ai', '断言', 'assert'] },
  { id: 'wait', label: '等待', keywords: ['等待', 'wait', 'sleep'] },
  { id: 'launch', label: '启动', keywords: ['启动', 'launch', 'open'] },
  { id: 'back', label: '返回', keywords: ['返回', 'back'] },
  { id: 'home', label: '主屏', keywords: ['主屏', 'home'] },
  { id: 'schemeUrl', label: 'Scheme跳转', keywords: ['scheme', 'url', '跳转', 'deeplink'] },
  { id: 'schemeRouter', label: 'Scheme路由', keywords: ['scheme', 'router', '路由'] },
]

// 计算 placeholder
const placeholder = computed(() => {
  if (selectedAction.value) {
    return `输入 ${selectedAction.value.label} 的参数...`
  }
  return '输入操作类型（如：点击、输入、AI 操作...）'
})

// 联想建议
const suggestions = computed(() => {
  if (selectedAction.value) return [] // 已选择动作，不显示联想
  
  const query = inputText.value.toLowerCase().trim()
  if (!query) return actions // 空输入显示全部
  
  return actions.filter(action => {
    if (action.label.toLowerCase().includes(query)) return true
    if (action.id.toLowerCase().includes(query)) return true
    if (action.keywords.some(k => k.toLowerCase().includes(query))) return true
    return false
  })
})

// 输入处理
function onInput() {
  showSuggestions.value = true
  highlightIndex.value = 0
}

// 聚焦
function onFocus() {
  if (!selectedAction.value && inputText.value === '') {
    showSuggestions.value = true
  }
}

// 失焦
function onBlur() {
  setTimeout(() => {
    showSuggestions.value = false
  }, 150)
}

// 方向键导航
function navigate(dir) {
  if (!showSuggestions.value || suggestions.value.length === 0) return
  
  highlightIndex.value = (highlightIndex.value + dir + suggestions.value.length) % suggestions.value.length
}

// 回车处理
function onEnter() {
  // 如果有联想列表且显示中，选择当前高亮项
  if (showSuggestions.value && suggestions.value.length > 0) {
    selectItem(suggestions.value[highlightIndex.value])
    return
  }
  
  // 如果已选择动作，提交步骤
  if (selectedAction.value && inputText.value.trim()) {
    submitStep()
  }
}

// 选择联想项
function selectItem(item) {
  selectedAction.value = item
  inputText.value = ''
  showSuggestions.value = false
  highlightIndex.value = 0
  
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 提交步骤
function submitStep() {
  if (!selectedAction.value) return
  
  emit('add-step', {
    action: selectedAction.value.id,
    actionLabel: selectedAction.value.label,
    prompt: inputText.value.trim(),
    midsceneCommand: generateCommand()
  })
  
  // 重置
  selectedAction.value = null
  inputText.value = ''
  
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 生成命令
function generateCommand() {
  const action = selectedAction.value
  const prompt = inputText.value.trim()
  
  switch (action.id) {
    case 'ai_act': return `aiAct('${prompt}')`
    case 'ai_query': return `aiQuery('${prompt}')`
    case 'ai_assert': return `aiAssert('${prompt}')`
    case 'click': return `aiAct('点击 ${prompt}')`
    case 'input': return `aiAct('输入 ${prompt}')`
    case 'swipe': return `aiAct('滑动 ${prompt}')`
    case 'wait': return `sleep(${parseInt(prompt) || 1000})`
    case 'launch': return `launch('${prompt}')`
    case 'schemeUrl': return `schemeUrl('${prompt}')`
    case 'schemeRouter': return `schemeRouter('${prompt}')`
    case 'screenshot': return `screenshot()`
    case 'back': return `back()`
    case 'home': return `home()`
    default: return `${action.id}('${prompt}')`
  }
}

// 关闭联想
function closeSuggestions() {
  showSuggestions.value = false
  if (selectedAction.value) {
    selectedAction.value = null
    inputText.value = ''
  }
}

// 清除已选动作
function clearAction() {
  selectedAction.value = null
  inputText.value = ''
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 退格键处理
function onBackspace() {
  if (inputText.value === '' && selectedAction.value) {
    selectedAction.value = null
  }
}
</script>

<style scoped>
.smart-step-input {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 0 12px;
  height: 48px;
  transition: all 0.2s;
}

.smart-step-input:focus-within {
  border-style: solid;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 动作标签 */
.action-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  flex-shrink: 0;
  margin-right: 8px;
  transition: opacity 0.15s;
}

.action-tag:hover {
  opacity: 0.85;
}

/* 标签颜色 */
.action-tag.click { background: #eff6ff; color: #2563eb; }
.action-tag.input { background: #f5f3ff; color: #7c3aed; }
.action-tag.swipe { background: #fff7ed; color: #c2410c; }
.action-tag.wait { background: #f3f4f6; color: #4b5563; }
.action-tag.screenshot { background: #fef3c7; color: #92400e; }
.action-tag.ai_act, .action-tag.ai_query, .action-tag.ai_assert { background: #e0e7ff; color: #4338ca; }
.action-tag.launch { background: #fce7f3; color: #be185d; }
.action-tag.home, .action-tag.back { background: #f3f4f6; color: #374151; }
.action-tag.schemeUrl, .action-tag.schemeRouter { background: #eef2ff; color: #4338ca; }

.tag-close {
  font-size: 14px;
  opacity: 0.6;
}

.tag-close:hover {
  opacity: 1;
}

.step-input {
  flex: 1;
  height: 100%;
  border: none;
  font-size: 14px;
  color: #1e293b;
  background: transparent;
  outline: none;
}

.step-input::placeholder {
  color: #94a3b8;
}

/* 联想下拉 */
.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  max-height: 320px;
  overflow-y: auto;
  z-index: 100;
}

.suggestion-item {
  padding: 12px 16px;
  font-size: 14px;
  color: #334155;
  cursor: pointer;
  transition: background 0.1s;
}

.suggestion-item:first-child {
  border-radius: 10px 10px 0 0;
}

.suggestion-item:last-child {
  border-radius: 0 0 10px 10px;
}

.suggestion-item:hover,
.suggestion-item.active {
  background: #eff6ff;
  color: #1d4ed8;
}

/* 滚动条 */
.suggestions-dropdown::-webkit-scrollbar {
  width: 6px;
}

.suggestions-dropdown::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
</style>
