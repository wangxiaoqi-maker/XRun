<template>
  <div class="tp-card">
    <div class="tp-header">
      <span class="tp-icon">&#128721;</span>
      <span>测试大纲确认 (Human-in-the-loop)</span>
    </div>
    <div class="tp-body">
      <div class="tp-toolbar">
        <button class="btn-tool" @click="showAddForm = true">&#10133; 添加测试点</button>
        <button class="btn-tool" @click="showSupplement = true">&#128221; 补充语料重新分析</button>
      </div>

      <!-- 添加测试点表单 -->
      <div v-if="showAddForm" class="add-form">
        <input v-model="newPoint.title" placeholder="测试点标题" class="form-input" />
        <textarea v-model="newPoint.description" placeholder="测试点描述（可选）" class="form-textarea"></textarea>
        <div class="form-selects">
          <select v-model="newPoint.category" class="form-select">
            <option value="功能测试">功能测试</option>
            <option value="异常测试">异常测试</option>
            <option value="边界测试">边界测试</option>
            <option value="性能测试">性能测试</option>
            <option value="安全测试">安全测试</option>
          </select>
          <select v-model="newPoint.priority" class="form-select">
            <option value="P0">P0 - 最高</option>
            <option value="P1">P1 - 高</option>
            <option value="P2">P2 - 中</option>
            <option value="P3">P3 - 低</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="cancelAdd">取消</button>
          <button class="btn-add" @click="handleAdd" :disabled="!newPoint.title.trim()">添加</button>
        </div>
      </div>

      <!-- 补充语料弹窗 -->
      <div v-if="showSupplement" class="supplement-overlay">
        <div class="overlay-mask" @click="showSupplement = false"></div>
        <div class="overlay-content">
          <div class="overlay-title">&#128221; 补充语料/需求</div>
          <textarea v-model="supplementText" placeholder="请输入补充的需求描述、测试场景、特殊条件等..." class="supplement-textarea"></textarea>
          <div class="overlay-actions">
            <button class="btn-cancel" @click="showSupplement = false">取消</button>
            <button class="btn-supplement" @click="handleSupplement" :disabled="!supplementText.trim()">补充并重新分析</button>
          </div>
        </div>
      </div>

      <!-- 测试点列表 -->
      <div class="tp-list">
        <div v-for="tp in points" :key="tp.id" class="tp-item" :class="{ 'is-manual': tp.is_manual }">
          <label class="tp-label" :class="{ unselected: !isConfirmed(tp.id) }" @click.prevent="$emit('toggle', tp)">
            <input type="checkbox" class="tp-cb" :checked="isConfirmed(tp.id)" @click.stop.prevent="$emit('toggle', tp)" />
            <span class="tp-title">{{ tp.title }}</span>
            <span v-if="tp.is_manual" class="manual-tag">手动</span>
          </label>
          <div class="tp-actions">
            <button class="btn-icon" @click.stop="$emit('edit', tp)" title="编辑">&#9999;&#65039;</button>
            <button class="btn-icon" @click.stop="$emit('delete', tp)" title="删除">&#128465;&#65039;</button>
          </div>
        </div>
      </div>

      <div class="tp-footer">
        <button class="btn-ghost" @click="$emit('select-all')">全选</button>
        <button class="btn-confirm" @click="$emit('confirm')" :disabled="confirmedCount === 0">
          确认 {{ confirmedCount }} 个 → 生成用例
        </button>
      </div>

      <!-- 编辑弹窗 -->
      <div v-if="editingPoint" class="supplement-overlay">
        <div class="overlay-mask" @click="$emit('cancel-edit')"></div>
        <div class="overlay-content">
          <div class="overlay-title">&#9999;&#65039; 编辑测试点</div>
          <input :value="editingPoint.title" @input="$emit('update:editingPoint', { ...editingPoint, title: $event.target.value })" placeholder="测试点标题" class="form-input" />
          <textarea :value="editingPoint.description" @input="$emit('update:editingPoint', { ...editingPoint, description: $event.target.value })" placeholder="测试点描述" class="form-textarea"></textarea>
          <div class="form-selects">
            <select :value="editingPoint.category" @change="$emit('update:editingPoint', { ...editingPoint, category: $event.target.value })" class="form-select">
              <option value="功能测试">功能测试</option>
              <option value="异常测试">异常测试</option>
              <option value="边界测试">边界测试</option>
              <option value="性能测试">性能测试</option>
              <option value="安全测试">安全测试</option>
            </select>
            <select :value="editingPoint.priority" @change="$emit('update:editingPoint', { ...editingPoint, priority: $event.target.value })" class="form-select">
              <option value="P0">P0 - 最高</option>
              <option value="P1">P1 - 高</option>
              <option value="P2">P2 - 中</option>
              <option value="P3">P3 - 低</option>
            </select>
          </div>
          <div class="overlay-actions">
            <button class="btn-cancel" @click="$emit('cancel-edit')">取消</button>
            <button class="btn-add" @click="$emit('save-edit')">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
  points: { type: Array, default: () => [] },
  confirmedIds: { type: Set, default: () => new Set() },
  confirmedCount: { type: Number, default: 0 },
  editingPoint: { type: Object, default: null },
})

const emit = defineEmits([
  'toggle', 'confirm', 'select-all',
  'add', 'edit', 'delete', 'supplement',
  'save-edit', 'cancel-edit', 'update:editingPoint',
])

const showAddForm = ref(false)
const showSupplement = ref(false)
const supplementText = ref('')
const newPoint = ref({ title: '', description: '', category: '功能测试', priority: 'P1' })

function isConfirmed(id) {
  return props.confirmedIds.has(id)
}

function cancelAdd() {
  showAddForm.value = false
  newPoint.value = { title: '', description: '', category: '功能测试', priority: 'P1' }
}

function handleAdd() {
  if (!newPoint.value.title.trim()) return
  emit('add', { ...newPoint.value })
  cancelAdd()
}

function handleSupplement() {
  if (!supplementText.value.trim()) return
  emit('supplement', supplementText.value)
  supplementText.value = ''
  showSupplement.value = false
}
</script>

<style scoped>
.tp-card {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(251, 191, 36, 0.1);
}

.tp-header {
  background: #fef3c7;
  color: #92400e;
  font-weight: 600;
  font-size: 13px;
  padding: 12px 16px;
  border-bottom: 1px solid #fde68a;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tp-icon { font-size: 14px; }

.tp-body { padding: 16px; }

.tp-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #fde68a;
}

.btn-tool {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
}

.btn-tool:hover { background: #e5e7eb; }

/* 测试点列表 */
.tp-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tp-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.tp-label {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.7);
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  flex: 1;
}

.tp-label:focus-within { background: #fff; border-color: #fcd34d; }
.tp-label.unselected { opacity: 0.6; }

.tp-cb { width: 14px; height: 14px; accent-color: #f59e0b; cursor: pointer; }
.tp-title { flex: 1; font-size: 13px; color: #451a03; }

.tp-item.is-manual .tp-title { color: #7c3aed; font-weight: 500; }
.manual-tag { font-size: 10px; background: #ddd6fe; color: #7c3aed; padding: 1px 6px; border-radius: 4px; }

.tp-actions { display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s; }
.tp-item:hover .tp-actions { opacity: 1; }
.btn-icon { background: transparent; border: none; padding: 2px 4px; font-size: 12px; cursor: pointer; }

.tp-footer {
  padding: 12px 0 0;
  border-top: 1px solid #fde68a;
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-ghost {
  background: white;
  border: 1px solid #d1d5db;
  color: #4b5563;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.btn-confirm {
  background: #f59e0b;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-confirm:hover { background: #d97706; }
.btn-confirm:disabled { opacity: 0.6; cursor: not-allowed; }

/* 表单 */
.add-form {
  background: #faf5ff;
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-input {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.form-input:focus { border-color: #8b5cf6; }

.form-textarea {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  outline: none;
  min-height: 60px;
  resize: vertical;
}

.form-selects { display: flex; gap: 8px; }

.form-select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 12px;
  outline: none;
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; }

.btn-cancel {
  background: #f3f4f6;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
  border: none;
  cursor: pointer;
}

.btn-add {
  background: #8b5cf6;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  border: none;
  cursor: pointer;
}

.btn-add:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-supplement {
  background: #10b981;
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  border: none;
  cursor: pointer;
}

.btn-supplement:disabled { opacity: 0.5; cursor: not-allowed; }

/* 弹窗覆盖 */
.supplement-overlay { position: relative; z-index: 10; }
.overlay-mask { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.4); z-index: 1000; }

.overlay-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 12px;
  padding: 20px;
  width: 90%;
  max-width: 420px;
  z-index: 1001;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.overlay-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.overlay-actions { display: flex; gap: 8px; justify-content: flex-end; }

.supplement-textarea {
  width: 100%;
  min-height: 120px;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
}
</style>
