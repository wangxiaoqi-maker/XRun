<template>
  <!-- 元素框选 Overlay - 叠加在投屏画面上 -->
  <div class="element-overlay" ref="overlayRef" :style="overlayStyle">
    <!-- 元素框选 -->
    <div
      v-for="element in elements"
      :key="element.id"
      class="element-box"
      :class="{
        'is-hovered': hoveredId === element.id,
        'is-selected': selectedId === element.id
      }"
      :style="getElementStyle(element)"
      @mouseenter="onElementHover(element)"
      @mouseleave="onElementLeave()"
      @click="onElementClick(element)"
    >
      <!-- 元素标签 -->
      <div v-if="hoveredId === element.id || selectedId === element.id" class="element-label">
        <span class="label-index">{{ element.index || elements.indexOf(element) + 1 }}</span>
        <span class="label-name">{{ element.element_name || element.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // 元素列表
  elements: {
    type: Array,
    default: () => []
  },
  // 当前悬浮的元素 ID
  hoveredId: {
    type: [String, Number],
    default: null
  },
  // 当前选中的元素 ID
  selectedId: {
    type: [String, Number],
    default: null
  },
  // 是否正在扫描
  scanning: {
    type: Boolean,
    default: false
  },
  // 投屏容器尺寸（用于坐标转换）
  containerWidth: {
    type: Number,
    default: 300
  },
  containerHeight: {
    type: Number,
    default: 650
  },
  // 设备实际分辨率
  deviceWidth: {
    type: Number,
    default: 1080
  },
  deviceHeight: {
    type: Number,
    default: 2400
  },
  // 图片实际显示区域（处理 object-fit 偏移）
  imgRect: {
    type: Object,
    default: () => ({ left: 0, top: 0, width: 0, height: 0 })
  }
})

// overlay 精确匹配投屏画面的实际显示区域
const overlayStyle = computed(() => {
  const rect = props.imgRect
  
  console.log('[ElementOverlay] imgRect:', rect, '元素数量:', props.elements?.length)
  
  if (rect && rect.width > 0 && rect.height > 0) {
    const style = {
      position: 'absolute',
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`
    }
    console.log('[ElementOverlay] 应用样式:', style)
    return style
  }
  
  // 兜底：填满容器
  console.log('[ElementOverlay] imgRect 无效，使用 100%')
  return {
    position: 'absolute',
    left: '0',
    top: '0',
    width: '100%',
    height: '100%'
  }
})

const emit = defineEmits(['hover', 'leave', 'click'])

const overlayRef = ref(null)

/**
 * 解析 bbox 数据
 * 支持多种格式：数组、字符串、JSON 字符串
 * 支持像素坐标和百分比坐标
 */
function parseBbox(bbox) {
  if (!bbox) return null
  
  let parsed = null
  
  // 已经是数组
  if (Array.isArray(bbox)) {
    parsed = bbox.length === 4 ? bbox : null
  }
  // 字符串格式: "[10, 20, 15, 8]" 或 "10, 20, 15, 8"
  else if (typeof bbox === 'string') {
    try {
      // 尝试 JSON 解析
      const arr = JSON.parse(bbox)
      if (Array.isArray(arr) && arr.length === 4) {
        parsed = arr
      }
    } catch {
      // 尝试逗号分隔解析
      const parts = bbox.replace(/[\[\]]/g, '').split(',').map(s => parseFloat(s.trim()))
      if (parts.length === 4 && parts.every(n => !isNaN(n))) {
        parsed = parts
      }
    }
  }
  
  if (!parsed) return null
  
  // 检查是否是像素坐标（任何值 > 100）
  if (parsed.some(v => v > 100)) {
    // 假设是 [left, top, right, bottom] 像素格式
    // 转换为 [left%, top%, width%, height%] 百分比格式
    const deviceW = props.deviceWidth || 1080
    const deviceH = props.deviceHeight || 2400
    
    let [left, top, v3, v4] = parsed
    
    // 判断格式：如果 v3 > left 且 v4 > top，是 [left, top, right, bottom]
    let widthPx, heightPx
    if (v3 > left && v4 > top) {
      // [left, top, right, bottom] 格式
      widthPx = v3 - left
      heightPx = v4 - top
    } else {
      // [left, top, width, height] 像素格式
      widthPx = v3
      heightPx = v4
    }
    
    return [
      (left / deviceW) * 100,
      (top / deviceH) * 100,
      (widthPx / deviceW) * 100,
      (heightPx / deviceH) * 100
    ]
  }
  
  // 已经是百分比格式
  return parsed
}

/**
 * 获取元素框选样式
 * 支持多种格式：
 * 1. bbox 百分比格式: [left%, top%, width%, height%]
 * 2. bounds 像素格式: { startX, startY, endX, endY } 或 "[x1,y1][x2,y2]"
 * 3. position_area 语义位置: "顶部"、"底部"、"中央" 等（估算）
 */
function getElementStyle(element) {
  // 解析 bbox（支持字符串和数组格式）
  const bbox = parseBbox(element.bbox)
  if (bbox) {
    const [left, top, width, height] = bbox
    return {
      left: `${left}%`,
      top: `${top}%`,
      width: `${width}%`,
      height: `${height}%`
    }
  }
  
  // 像素坐标格式 (从 UI Hierarchy 获取)
  if (element.bounds || (element.startX !== undefined)) {
    let startX, startY, endX, endY
    
    if (typeof element.bounds === 'string') {
      // 解析 "[x1,y1][x2,y2]" 格式
      const match = element.bounds.match(/\[(\d+),(\d+)\]\[(\d+),(\d+)\]/)
      if (match) {
        startX = parseInt(match[1])
        startY = parseInt(match[2])
        endX = parseInt(match[3])
        endY = parseInt(match[4])
      }
    } else {
      startX = element.startX || element.x || 0
      startY = element.startY || element.y || 0
      endX = element.endX || (startX + (element.width || 100))
      endY = element.endY || (startY + (element.height || 50))
    }
    
    if (startX !== undefined) {
      // 转换为百分比
      const left = (startX / props.deviceWidth) * 100
      const top = (startY / props.deviceHeight) * 100
      const width = ((endX - startX) / props.deviceWidth) * 100
      const height = ((endY - startY) / props.deviceHeight) * 100
      
      return {
        left: `${left}%`,
        top: `${top}%`,
        width: `${width}%`,
        height: `${height}%`
      }
    }
  }
  
  // 基于 position_area 估算位置（用于没有精确坐标的元素）
  if (element.position_area) {
    return estimatePositionFromArea(element.position_area, element.element_type)
  }
  
  // 默认隐藏
  return { display: 'none' }
}

/**
 * 根据语义位置描述估算框选区域
 */
function estimatePositionFromArea(area, elementType) {
  // 位置映射表：[left%, top%, width%, height%]
  const areaMap = {
    '顶部': [10, 2, 80, 8],
    '顶部左': [5, 2, 30, 8],
    '顶部右': [65, 2, 30, 8],
    '顶部中': [25, 2, 50, 8],
    '中央': [10, 40, 80, 20],
    '中部': [10, 35, 80, 30],
    '底部': [10, 90, 80, 8],
    '底部左': [5, 90, 30, 8],
    '底部右': [65, 90, 30, 8],
    '底部中': [25, 90, 50, 8],
    '左侧': [2, 30, 25, 40],
    '右侧': [73, 30, 25, 40],
    '导航栏': [0, 92, 100, 8],
    '搜索区': [5, 5, 90, 7],
    '列表区': [5, 15, 90, 75]
  }
  
  // 尝试匹配位置描述
  for (const [key, value] of Object.entries(areaMap)) {
    if (area.includes(key)) {
      return {
        left: `${value[0]}%`,
        top: `${value[1]}%`,
        width: `${value[2]}%`,
        height: `${value[3]}%`,
        opacity: 0.6 // 估算位置用半透明显示
      }
    }
  }
  
  // 无法识别则隐藏
  return { display: 'none' }
}

function onElementHover(element) {
  emit('hover', element.id)
}

function onElementLeave() {
  emit('leave')
}

function onElementClick(element) {
  emit('click', element)
}
</script>

<style lang="scss" scoped>
.element-overlay {
  /* position, left, top, width, height 由 overlayStyle 动态设置 */
  pointer-events: none;
  z-index: 10;
  overflow: hidden;
}

// 元素框选
.element-box {
  position: absolute;
  border: 2px solid rgba(96, 165, 250, 0.4);
  border-radius: 3px;
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover,
  &.is-hovered {
    border-color: rgba(99, 102, 241, 0.8);
    background: rgba(99, 102, 241, 0.15);
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    z-index: 20;
  }
  
  &.is-selected {
    border-color: #22c55e;
    background: rgba(34, 197, 94, 0.15);
    box-shadow: 0 0 12px rgba(34, 197, 94, 0.4);
    z-index: 21;
  }
}

// 元素标签
.element-label {
  position: absolute;
  top: -24px;
  left: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(99, 102, 241, 0.95);
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 30;
  
  .label-index {
    opacity: 0.7;
  }
  
  .label-name {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
