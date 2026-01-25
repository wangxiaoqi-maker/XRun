<template>
  <div class="placeholder-page">
    <el-empty description="该模块正在开发中，敬请期待">
      <template #image>
        <svg width="160" height="160" viewBox="0 0 160 160" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="20" y="40" width="120" height="80" rx="8" fill="#f5f5f5" stroke="#d9d9d9" stroke-width="2"/>
          <rect x="35" y="55" width="40" height="8" rx="2" fill="#d9d9d9"/>
          <rect x="35" y="70" width="90" height="6" rx="2" fill="#e8e8e8"/>
          <rect x="35" y="82" width="70" height="6" rx="2" fill="#e8e8e8"/>
          <rect x="35" y="94" width="50" height="6" rx="2" fill="#e8e8e8"/>
          <circle cx="130" cy="30" r="20" fill="#1890ff" opacity="0.1"/>
          <path d="M130 20v20M120 30h20" stroke="#1890ff" stroke-width="3" stroke-linecap="round"/>
        </svg>
      </template>
      <el-button type="primary" @click="goBack">返回上一页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.back()
}
</script>

<style lang="scss" scoped>
.placeholder-page {
  height: calc(100vh - var(--header-height) - 32px);
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff;
  border-radius: 4px;
}
</style>
