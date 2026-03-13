<template>
  <div class="chat-done">
    <span class="done-icon">&#9989;</span>
    <span class="done-text">{{ msg.content }}</span>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.chat-done {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #166534;
}

.done-icon {
  font-size: 16px;
  flex-shrink: 0;
}
</style>
