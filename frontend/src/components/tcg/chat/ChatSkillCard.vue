<template>
  <div class="skill-card">
    <div class="skill-header" @click="collapsed = !collapsed">
      <div class="left">
        <span class="gear-icon">&#9881;</span>
        <span class="skill-title">Skill 执行</span>
        <span class="skill-count-tag">{{ msg.skills?.length || 0 }} 个</span>
      </div>
      <div class="right">
        <span v-if="timeStr" class="skill-time">{{ timeStr }}</span>
        <span class="skill-arrow" :class="{ collapsed }">&#9660;</span>
      </div>
    </div>
    <div v-show="!collapsed" class="skill-body">
      <div class="skill-result" v-for="sk in (msg.skills || [])" :key="sk.key">
        <div class="result-header">
          <span class="result-icon">&#10047;</span>
          <span>{{ sk.icon }} {{ sk.name }}</span>
        </div>
        <div class="result-body">
          <div class="terminal-box">
            <div class="term-code">{{ sk.description }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

const collapsed = ref(false)

const timeStr = computed(() => {
  if (!props.msg.time) return ''
  const d = new Date(props.msg.time)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
})
</script>

<style scoped>
.skill-card {
  background: #fff;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.skill-header {
  background: #eff6ff;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #dbeafe;
  cursor: pointer;
  user-select: none;
}

.left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.gear-icon {
  color: #2563eb;
  font-size: 14px;
}

.skill-title {
  color: #1e3a8a;
  font-size: 13px;
  font-weight: 600;
}

.skill-count-tag {
  color: #059669;
  font-size: 12px;
  font-weight: 500;
}

.skill-time {
  color: #3b82f6;
  font-size: 12px;
}

.skill-arrow {
  color: #3b82f6;
  font-size: 10px;
  transition: transform 0.2s;
  display: inline-block;
}

.skill-arrow.collapsed {
  transform: rotate(-90deg);
}

.skill-body {
  padding: 12px;
  background: #fff;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.skill-result {
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  background: #faf5ff;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b21a8;
  font-weight: 500;
  border-bottom: 1px solid #f3e8ff;
}

.result-icon {
  font-size: 14px;
}

.result-body {
  padding: 12px;
  background: #fff;
}

.terminal-box {
  background: #1e1e2e;
  border-radius: 6px;
  padding: 12px;
  font-family: Consolas, Monaco, monospace;
  font-size: 11px;
  line-height: 1.6;
}

.term-code {
  color: #cdd6f4;
  white-space: pre-wrap;
}
</style>
