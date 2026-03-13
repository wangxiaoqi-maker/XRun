<template>
  <div class="stage-card">
    <div class="stage-header">
      <span class="stage-icon">&#128203;</span>
      <span>{{ msg.content }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
})
</script>

<style scoped>
.stage-card {
  background: #fff;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.stage-header {
  background: #eff6ff;
  color: #1e40af;
  font-weight: 600;
  font-size: 13px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.stage-icon {
  font-size: 14px;
}
</style>
