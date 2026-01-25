<template>
  <div class="demo-page">
    <DemoComponent />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import DemoComponent from '../components/demo.vue'

let tailwindScript = null

onMounted(() => {
  // 动态加载 Tailwind CSS，只在这个页面生效
  if (!document.getElementById('tailwind-cdn')) {
    tailwindScript = document.createElement('script')
    tailwindScript.id = 'tailwind-cdn'
    tailwindScript.src = 'https://cdn.tailwindcss.com'
    document.head.appendChild(tailwindScript)
  }
})

onUnmounted(() => {
  // 页面卸载时移除 Tailwind，避免影响其他页面
  if (tailwindScript && tailwindScript.parentNode) {
    tailwindScript.parentNode.removeChild(tailwindScript)
  }
})
</script>

<style scoped>
.demo-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: 0;
  padding: 0;
  overflow: hidden;
  z-index: 9999;
  background: #f9fafb;
}
</style>




