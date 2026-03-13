<template>
  <div class="config-card">
    <div class="config-header">
      <span class="config-icon">&#9881;&#65039;</span>
      <span>生成配置</span>
    </div>
    <div class="config-body">
      <div class="cfg-row">
        <label>目标目录</label>
        <el-select
          :model-value="config.moduleName"
          @update:model-value="$emit('update:config', { ...config, moduleName: $event })"
          filterable allow-create default-first-option
          placeholder="选择或输入新目录" size="small" style="width: 100%;"
        >
          <el-option v-for="m in moduleOptions" :key="m.id" :label="m.fullPath" :value="m.name" />
        </el-select>
      </div>
      <div class="cfg-row">
        <label>补充说明</label>
        <el-input
          :model-value="config.userPrompt"
          @update:model-value="$emit('update:config', { ...config, userPrompt: $event })"
          type="textarea" :rows="2"
          placeholder="例：重点关注安全性..." size="small"
        />
      </div>
      <div class="cfg-actions">
        <button class="btn-gen" @click="$emit('start')" :disabled="generating">
          {{ generating ? '⏳ 生成中...' : '立即生成' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  msg: { type: Object, required: true },
  config: { type: Object, required: true },
  moduleOptions: { type: Array, default: () => [] },
  generating: { type: Boolean, default: false },
})

defineEmits(['start', 'update:config'])
</script>

<style scoped>
.config-card {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.config-header {
  background: #fef3c7;
  color: #92400e;
  font-weight: 600;
  font-size: 13px;
  padding: 10px 14px;
  border-bottom: 1px solid #fde68a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.config-icon {
  font-size: 14px;
}

.config-body {
  padding: 14px;
}

.cfg-row {
  margin-bottom: 12px;
}

.cfg-row:last-of-type {
  margin-bottom: 8px;
}

.cfg-row label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.cfg-actions {
  padding-top: 10px;
  border-top: 1px solid #fde68a;
}

.btn-gen {
  background: #f59e0b;
  color: white;
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-gen:hover { background: #d97706; }
.btn-gen:disabled { opacity: 0.7; cursor: not-allowed; }
</style>
