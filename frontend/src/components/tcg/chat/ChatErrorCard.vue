<template>
  <div class="chat-error-card">
    <div class="error-header">
      <span class="error-icon">&#9888;&#65039;</span>
      <span>错误</span>
    </div>
    <div class="error-body">{{ msg.content }}</div>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.chat-error-card {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  overflow: hidden;
}

.error-header {
  background: #fef2f2;
  color: #b91c1c;
  font-weight: 600;
  font-size: 13px;
  padding: 10px 14px;
  border-bottom: 1px solid #fecaca;
  display: flex;
  align-items: center;
  gap: 6px;
}

.error-icon {
  font-size: 14px;
}

.error-body {
  padding: 12px 14px;
  font-size: 13px;
  color: #991b1b;
  line-height: 1.5;
}
</style>
