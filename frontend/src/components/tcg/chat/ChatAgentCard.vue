<template>
  <div class="agent-card" :class="msg._status">
    <div class="agent-header" @click="msg._collapsed = !msg._collapsed">
      <div class="left">
        <span class="agent-icon">{{ msg._agentIcon || '⚙' }}</span>
        <span class="agent-label">{{ msg._agentName }}</span>
        <span class="agent-status" :class="msg._status">{{ statusText }}</span>
      </div>
      <div class="right">
        <span v-if="msg._elapsed" class="agent-time">{{ msg._elapsed }}</span>
        <span class="agent-arrow">{{ msg._collapsed ? '▸' : '▾' }}</span>
      </div>
    </div>
    <div v-show="!msg._collapsed" class="agent-body">
      <div v-if="msg._thinking" class="thinking-section">
        <div class="section-title" @click="msg._thinkingCollapsed = !msg._thinkingCollapsed">
          <span>&#128161; 模型输出</span>
          <span class="section-toggle">{{ msg._thinkingCollapsed ? '▸' : '▾' }}</span>
        </div>
        <pre v-show="!msg._thinkingCollapsed" class="thinking-pre">{{ msg._thinking }}</pre>
      </div>
      <div v-if="msg._logs?.length" class="log-list">
        <div v-for="(log, li) in msg._logs" :key="li" class="log-line">{{ log }}</div>
      </div>
      <div v-if="msg._status === 'running' && !msg._thinking && !msg._logs?.length" class="loading-state">
        <span class="loading-dot"></span> 正在处理...
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

const statusText = computed(() => {
  const s = props.msg._status
  if (s === 'running') return '执行中...'
  if (s === 'completed') return '执行成功'
  return '执行失败'
})
</script>

<style scoped>
.agent-card {
  background: #fff;
  border: 1px solid #c7d2fe;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.agent-card.running { border-color: #93c5fd; }
.agent-card.completed { border-color: #86efac; }
.agent-card.failed { border-color: #fca5a5; }

.agent-header {
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  user-select: none;
}

.agent-card.running .agent-header { background: #eff6ff; }
.agent-card.completed .agent-header { background: #f0fdf4; }
.agent-card.failed .agent-header { background: #fef2f2; }

.left {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-icon { font-size: 15px; }

.agent-status {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 4px;
}

.agent-status.running { background: #dbeafe; color: #2563eb; }
.agent-status.completed { background: #dcfce7; color: #16a34a; }
.agent-status.failed { background: #fee2e2; color: #dc2626; }

.agent-time { font-size: 12px; color: #64748b; font-family: monospace; }
.agent-arrow { font-size: 11px; color: #94a3b8; }

.agent-body {
  padding: 12px 14px;
  font-size: 12px;
  color: #475569;
  max-height: 400px;
  overflow-y: auto;
}

.thinking-section { margin-bottom: 10px; }

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #6d28d9;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.section-toggle { font-size: 10px; color: #a78bfa; }

.thinking-pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 10px;
  margin: 6px 0 0;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.7;
  white-space: pre-wrap;
  font-family: Consolas, monospace;
  max-height: 240px;
  overflow-y: auto;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-line {
  font-size: 12px;
  color: #475569;
  padding: 2px 0;
  line-height: 1.5;
}

.log-line::before { content: '• '; color: #94a3b8; }

.loading-state {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.loading-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  animation: pulse-dot 1.2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
