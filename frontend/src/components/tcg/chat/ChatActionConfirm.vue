<template>
  <div class="action-confirm">
    <div class="confirm-content" v-html="renderedHtml"></div>
    <div class="action-buttons">
      <button
        v-for="act in (msg.actions || [])"
        :key="act.id"
        class="action-btn"
        :class="act.style || 'default'"
        @click="$emit('action', msg, act)"
        :disabled="msg._acted"
      >{{ act.label }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

defineEmits(['action'])

const renderedHtml = computed(() => renderMarkdown(props.msg.content))

function renderMarkdown(text) {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="md-code-block"><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/^### (.+)$/gm, '<h4 class="md-h">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="md-h">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 class="md-h">$1</h2>')
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul class="md-list">$&</ul>')
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  html = html.replace(/\n/g, '<br>')
  return html
}
</script>

<style scoped>
.action-confirm {
  background: #f8fafc;
  color: #1e293b;
  padding: 14px 18px;
  border-radius: 12px 12px 12px 4px;
  font-size: 14px;
  line-height: 1.75;
  border: 1px solid #e2e8f0;
  max-width: 95%;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.action-btn {
  padding: 7px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid #e2e8f0;
}

.action-btn.primary {
  background: #8b5cf6;
  color: #fff;
  border-color: #8b5cf6;
}

.action-btn.primary:hover { background: #7c3aed; }

.action-btn.default {
  background: #fff;
  color: #475569;
}

.action-btn.default:hover {
  background: #f8fafc;
  border-color: #c4b5fd;
  color: #6d28d9;
}

.action-btn.outline {
  background: transparent;
  color: #64748b;
  border: 1px dashed #d1d5db;
}

.action-btn.outline:hover {
  border-color: #94a3b8;
  color: #334155;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
