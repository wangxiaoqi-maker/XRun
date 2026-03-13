<template>
  <div class="chat-progress">
    <span class="progress-dot"></span>
    <span class="progress-text">{{ msg.content }}</span>
    <span v-if="msg.percent" class="progress-pct">{{ Math.round(msg.percent) }}%</span>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.chat-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  padding: 2px 0;
}

.progress-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366f1;
  flex-shrink: 0;
  animation: dot-pulse 1.2s infinite;
}

.progress-pct {
  font-weight: 700;
  color: #6366f1;
  font-size: 11px;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
