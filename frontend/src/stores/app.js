/**
 * 应用状态管理
 * 用于知识库模块选择当前应用
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { knowledgeApi } from '@/api'

const CURRENT_APP_KEY = 'xrun_current_app'

export const useAppStore = defineStore('app', () => {
  // 状态
  const apps = ref([])
  const currentApp = ref(JSON.parse(localStorage.getItem(CURRENT_APP_KEY) || 'null'))
  const loading = ref(false)
  
  // 计算属性
  const hasApp = computed(() => !!currentApp.value)
  const appName = computed(() => currentApp.value?.app_name || '选择应用')
  
  // 方法
  async function loadApps() {
    loading.value = true
    try {
      const res = await knowledgeApi.getApps()
      apps.value = res.data || []
      
      // 如果当前应用不在列表中，清除选择
      if (currentApp.value) {
        const exists = apps.value.find(a => a.id === currentApp.value.id)
        if (!exists) {
          currentApp.value = null
          localStorage.removeItem(CURRENT_APP_KEY)
        }
      }
      
      // 如果没有选择应用且有可用应用，自动选择第一个
      if (!currentApp.value && apps.value.length > 0) {
        selectApp(apps.value[0])
      }
    } catch (e) {
      console.error('加载应用列表失败:', e)
    } finally {
      loading.value = false
    }
  }
  
  function selectApp(app) {
    currentApp.value = app
    localStorage.setItem(CURRENT_APP_KEY, JSON.stringify(app))
  }
  
  function clearApp() {
    currentApp.value = null
    localStorage.removeItem(CURRENT_APP_KEY)
  }
  
  return {
    apps,
    currentApp,
    loading,
    hasApp,
    appName,
    loadApps,
    selectApp,
    clearApp
  }
})
