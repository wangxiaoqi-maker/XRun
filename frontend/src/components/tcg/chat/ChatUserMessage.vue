<template>
  <div class="chat-user-msg">
    <div class="user-bubble">
      <div v-if="images.length" class="user-images">
        <img v-for="(url, i) in images" :key="i" :src="url" class="user-image" @click="previewImage(url)" />
      </div>
      <span v-if="msg.content">{{ msg.content }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
})

const images = computed(() => props.msg._images || [])

function previewImage(url) {
  window.open(url, '_blank')
}
</script>

<style scoped>
.chat-user-msg {
  display: flex;
  justify-content: flex-end;
}

.user-bubble {
  background: #f4f3fb;
  color: #334155;
  padding: 12px 16px;
  border-radius: 16px 16px 4px 16px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 85%;
  word-break: break-word;
}

.user-images {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.user-image {
  max-width: 200px;
  max-height: 160px;
  border-radius: 8px;
  object-fit: contain;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  transition: transform 0.15s;
}

.user-image:hover {
  transform: scale(1.02);
}
</style>
