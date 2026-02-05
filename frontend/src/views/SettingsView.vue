<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>
    
    <el-tabs v-model="activeTab" class="settings-tabs">
      <el-tab-pane label="基础设置" name="basic">
        <el-form :model="basicSettings" label-width="120px" style="max-width: 600px;">
          <el-form-item label="平台名称">
            <el-input v-model="basicSettings.name" />
          </el-form-item>
          <el-form-item label="默认超时时间">
            <el-input-number v-model="basicSettings.timeout" :min="1000" :step="1000" />
            <span class="unit">毫秒</span>
          </el-form-item>
          <el-form-item label="截图质量">
            <el-slider v-model="basicSettings.quality" :min="10" :max="100" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary">保存设置</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <el-tab-pane label="Sonic 配置" name="sonic">
        <el-form :model="sonicSettings" label-width="120px" style="max-width: 600px;">
          <el-form-item label="Server 地址">
            <el-input v-model="sonicSettings.serverUrl" />
          </el-form-item>
          <el-form-item label="Agent Key">
            <el-input v-model="sonicSettings.agentKey" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="sonicSettings.username" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="sonicSettings.password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary">保存设置</el-button>
            <el-button @click="testConnection">测试连接</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
      
      <el-tab-pane label="AI 配置" name="ai">
        <el-alert 
          title="AI 模型配置说明" 
          type="info" 
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <p>执行用例时会自动使用「模型供应商」中配置的视觉模型。</p>
          <p>请在<router-link to="/llm" style="color: #409eff;">模型供应商</router-link>页面配置支持视觉的大模型（如 qwen-vl-max、gpt-4o 等）。</p>
        </el-alert>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('basic')

const basicSettings = reactive({
  name: 'XRun',
  timeout: 10000,
  quality: 80
})

const sonicSettings = reactive({
  serverUrl: 'http://113.249.104.59:3001',
  agentKey: 'f63cbbfd-da49-4c86-8ae7-b5820382c768',
  username: 'sonic',
  password: 'sonic'
})

function testConnection() {
  ElMessage.info('测试连接中...')
}
</script>

<style lang="scss" scoped>
.settings-page {
  min-height: calc(100vh - var(--header-height) - 32px);
  background: #fff;
  border-radius: 4px;
  padding: 16px;
}

.page-header {
  margin-bottom: 16px;
  
  h2 {
    font-size: 16px;
    font-weight: 500;
    margin: 0;
  }
}

.settings-tabs {
  :deep(.el-tabs__content) {
    padding: 16px 0;
  }
}

.unit {
  margin-left: 8px;
  color: var(--text-secondary);
}
</style>
