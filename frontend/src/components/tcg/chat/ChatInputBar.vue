<template>
  <div class="chat-input-bar">
    <!-- 图片预览条 -->
    <div v-if="imageFiles.length" class="image-bar">
      <div v-for="f in imageFiles" :key="f.uid" class="image-chip">
        <img :src="f.preview" alt="" class="image-thumb" />
        <span class="img-rm" @click="$emit('remove-file', f)">&times;</span>
      </div>
    </div>

    <!-- 文件预览条 -->
    <div v-if="docFiles.length" class="file-bar">
      <span v-for="f in docFiles" :key="f.uid" class="file-chip">
        &#128196; {{ f.name }}
        <span class="file-rm" @click="$emit('remove-file', f)">&times;</span>
      </span>
    </div>

    <!-- 输入行 -->
    <div class="input-row">
      <button class="attach-btn" title="上传文件/图片" @click="fileInputRef?.click()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>

      <div class="input-wrapper">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          placeholder="请输入消息，可粘贴或上传图片..."
          @keydown.enter.ctrl="handleSend"
          @keydown.enter.exact.prevent="handleSend"
          @input="autoResize"
          @paste="onPaste"
        ></textarea>
      </div>

      <button v-if="generating" class="action-btn stop-btn" @click="$emit('cancel')" title="终止生成">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <rect x="3" y="3" width="10" height="10" rx="2"/>
        </svg>
      </button>
      <button v-else class="action-btn send-btn" @click="handleSend" :disabled="!canSend" title="发送">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M1.5 1.5l13 6.5-13 6.5V9l8-1-8-1V1.5z"/>
        </svg>
      </button>
    </div>

    <input ref="fileInputRef" type="file" style="display:none" multiple
      accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.gif,.webp" @change="onFilesSelected" />
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

const IMAGE_RE = /\.(png|jpe?g|gif|webp)$/i

const props = defineProps({
  generating: { type: Boolean, default: false },
  pendingFiles: { type: Array, default: () => [] },
})

const emit = defineEmits(['send', 'cancel', 'upload', 'remove-file', 'files-selected'])

const inputText = ref('')
const textareaRef = ref(null)
const fileInputRef = ref(null)

const imageFiles = computed(() => props.pendingFiles.filter(f => IMAGE_RE.test(f.name)))
const docFiles = computed(() => props.pendingFiles.filter(f => !IMAGE_RE.test(f.name)))
const canSend = computed(() => inputText.value.trim() || props.pendingFiles.length > 0)

function handleSend() {
  if (!canSend.value) return
  emit('send', inputText.value)
  inputText.value = ''
  nextTick(() => autoResize())
}

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function onFilesSelected(e) {
  emit('files-selected', e)
}

function onPaste(e) {
  const items = e.clipboardData?.items
  if (!items) return
  const imageItems = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) imageItems.push(file)
    }
  }
  if (imageItems.length > 0) {
    e.preventDefault()
    emit('files-selected', { target: { files: imageItems } })
  }
}

defineExpose({
  triggerUpload() { fileInputRef.value?.click() },
  focus() { textareaRef.value?.focus() },
})
</script>

<style scoped>
.chat-input-bar {
  border-top: 1px solid #e5e7eb;
  background: #fff;
  flex-shrink: 0;
  padding: 12px 16px;
}

.image-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.image-chip {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.img-rm {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 12px;
  line-height: 18px;
  text-align: center;
  cursor: pointer;
}

.img-rm:hover { background: #ef4444; }

.file-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.file-chip {
  font-size: 11px;
  background: #f3f4f6;
  color: #6366f1;
  padding: 3px 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.file-rm {
  cursor: pointer;
  color: #94a3b8;
  font-size: 13px;
  line-height: 1;
}

.file-rm:hover { color: #ef4444; }

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.attach-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #f3f4f6;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.attach-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.input-wrapper {
  flex: 1;
  min-width: 0;
}

.input-wrapper textarea {
  width: 100%;
  min-height: 40px;
  max-height: 120px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 9px 16px;
  font-size: 13px;
  resize: none;
  outline: none;
  box-sizing: border-box;
  font-family: inherit;
  line-height: 1.5;
  background: #f8f9fb;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input-wrapper textarea:focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
  background: #fff;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.send-btn {
  background: #8b5cf6;
  color: #fff;
}

.send-btn:hover { background: #7c3aed; }
.send-btn:disabled { background: #d1d5db; cursor: not-allowed; }

.stop-btn {
  background: #ef4444;
  color: #fff;
  animation: pulse-stop 1.5s infinite;
}

.stop-btn:hover { background: #dc2626; }

@keyframes pulse-stop {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
}
</style>
