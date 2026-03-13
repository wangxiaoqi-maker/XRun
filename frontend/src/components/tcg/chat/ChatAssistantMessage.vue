<template>
  <div class="chat-assistant-msg">
    <div class="assistant-bubble" :class="{ streaming: isStreaming }">
      <div v-if="isStreaming" class="stream-text">{{ props.msg.content }}<span class="typing-cursor"></span></div>
      <div v-else v-html="renderedHtml"></div>
    </div>
    <div v-if="props.msg._usage" class="usage-tag">
      <span>{{ props.msg._usage.input_tokens }} 输入</span>
      <span class="sep">|</span>
      <span>{{ props.msg._usage.output_tokens }} 输出</span>
      <span class="sep">|</span>
      <span>{{ props.msg._usage.total_tokens }} tokens</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

const isStreaming = computed(() => !!props.msg._streaming)

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
.assistant-bubble {
  color: var(--chat-text-primary, #1e293b);
  padding: 0;
  font-size: 14px;
  line-height: 1.75;
  max-width: 100%;
}

.stream-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.assistant-bubble :deep(h2.md-h),
.assistant-bubble :deep(h3.md-h),
.assistant-bubble :deep(h4.md-h) {
  margin: 12px 0 6px;
  font-weight: 600;
  color: #0f172a;
}

.assistant-bubble :deep(h2.md-h) { font-size: 16px; }
.assistant-bubble :deep(h3.md-h) { font-size: 15px; }
.assistant-bubble :deep(h4.md-h) { font-size: 14px; }

.assistant-bubble :deep(strong) { font-weight: 600; color: #1e293b; }

.assistant-bubble :deep(.md-list) { margin: 6px 0; padding-left: 20px; }
.assistant-bubble :deep(.md-list li) { margin: 3px 0; }

.assistant-bubble :deep(.md-inline-code) {
  background: #e0e7ff;
  color: #4338ca;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 13px;
  font-family: Consolas, monospace;
}

.assistant-bubble :deep(.md-code-block) {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 12px;
  border-radius: 6px;
  margin: 8px 0;
  font-size: 12px;
  line-height: 1.6;
  overflow-x: auto;
  font-family: Consolas, monospace;
}

.assistant-bubble :deep(.md-code-block code) {
  background: none;
  padding: 0;
  color: inherit;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: var(--chat-accent, #6366f1);
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.usage-tag {
  display: flex;
  gap: 2px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--chat-text-muted, #94a3b8);
}

.usage-tag .sep {
  color: #cbd5e1;
  margin: 0 3px;
}
</style>
