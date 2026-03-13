<template>
  <div class="thinking-card">
    <div class="thinking-header" @click="collapsed = !collapsed">
      <div class="left">
        <span class="thinking-icon" :class="{ pulsing: isStreaming }">&#128161;</span>
        <span class="thinking-title">深度思考</span>
        <span class="thinking-tag" :class="statusClass">{{ statusText }}</span>
      </div>
      <div class="right">
        <span v-if="duration" class="thinking-time">{{ duration }}</span>
        <span class="thinking-arrow" :class="{ collapsed }">&#9660;</span>
      </div>
    </div>
    <div v-show="!collapsed" class="thinking-body">
      <div v-if="msg.type === 'thinking' && msg.content" class="thinking-summary">{{ msg.content }}</div>
      <pre v-if="msg.type === 'thinking' && msg.detail" class="thinking-pre">{{ msg.detail }}</pre>
      <pre v-if="msg.type === 'reasoning'" class="thinking-pre">{{ msg.content }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

const collapsed = ref(false)

const isStreaming = computed(() => props.msg.type === 'reasoning' && props.msg._streaming)

const statusClass = computed(() => isStreaming.value ? 'streaming' : 'done')

const statusText = computed(() => {
  if (props.msg.type === 'reasoning') return isStreaming.value ? '思考中...' : '思考完成'
  return '已完成'
})

const duration = computed(() => props.msg._duration || '')
</script>

<style scoped>
.thinking-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.thinking-header {
  background: #fafafa;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.thinking-icon {
  font-size: 14px;
}

.thinking-icon.pulsing {
  animation: pulse-brain 1.5s ease-in-out infinite;
}

.thinking-tag {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 4px;
}

.thinking-tag.streaming {
  background: #fef3c7;
  color: #92400e;
}

.thinking-tag.done {
  background: #f3f4f6;
  color: #6b7280;
}

.thinking-time {
  font-size: 12px;
  color: #94a3b8;
  font-family: monospace;
}

.thinking-arrow {
  font-size: 10px;
  color: #9ca3af;
  transition: transform 0.2s;
  display: inline-block;
}

.thinking-arrow.collapsed {
  transform: rotate(-90deg);
}

.thinking-body {
  padding: 12px 14px;
  border-top: 1px solid #e5e7eb;
}

.thinking-summary {
  font-size: 13px;
  font-weight: 600;
  color: #6d28d9;
  margin-bottom: 8px;
}

.thinking-pre {
  background: #1e1e2e;
  color: #cdd6f4;
  border-radius: 6px;
  padding: 12px;
  margin: 0;
  font-size: 11px;
  line-height: 1.8;
  white-space: pre-wrap;
  font-family: Consolas, monospace;
  max-height: 280px;
  overflow-y: auto;
}

@keyframes pulse-brain {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; transform: scale(1.1); }
}
</style>
