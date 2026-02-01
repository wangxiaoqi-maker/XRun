/**
 * 项目状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/api'

const CURRENT_PROJECT_KEY = 'xrun_current_project'

export const useProjectStore = defineStore('project', () => {
  // 状态
  const projects = ref([])
  const currentProject = ref(JSON.parse(localStorage.getItem(CURRENT_PROJECT_KEY) || 'null'))
  const loading = ref(false)
  
  // 计算属性
  const hasProject = computed(() => !!currentProject.value)
  const projectName = computed(() => currentProject.value?.name || '选择项目')
  const projectCode = computed(() => currentProject.value?.code || '')
  const projectIcon = computed(() => currentProject.value?.icon || '📁')
  const projectColor = computed(() => currentProject.value?.color || '#184BFA')
  
  // 方法
  async function loadProjects() {
    loading.value = true
    try {
      const res = await projectApi.list()
      projects.value = res.data
      
      // 如果当前项目不在列表中，清除选择
      if (currentProject.value) {
        const exists = projects.value.find(p => p.id === currentProject.value.id)
        if (!exists) {
          currentProject.value = null
          localStorage.removeItem(CURRENT_PROJECT_KEY)
        }
      }
      
      // 如果没有选择项目且有可用项目，自动选择第一个
      if (!currentProject.value && projects.value.length > 0) {
        selectProject(projects.value[0])
      }
    } catch (e) {
      console.error('加载项目列表失败:', e)
    } finally {
      loading.value = false
    }
  }
  
  function selectProject(project) {
    currentProject.value = project
    localStorage.setItem(CURRENT_PROJECT_KEY, JSON.stringify(project))
  }
  
  function clearProject() {
    currentProject.value = null
    localStorage.removeItem(CURRENT_PROJECT_KEY)
  }
  
  async function createProject(data) {
    const res = await projectApi.create(data)
    projects.value.unshift(res.data)
    return res.data
  }
  
  async function updateProject(id, data) {
    const res = await projectApi.update(id, data)
    const idx = projects.value.findIndex(p => p.id === id)
    if (idx > -1) {
      projects.value[idx] = res.data
    }
    // 如果更新的是当前项目，同步更新
    if (currentProject.value?.id === id) {
      currentProject.value = res.data
      localStorage.setItem(CURRENT_PROJECT_KEY, JSON.stringify(res.data))
    }
    return res.data
  }
  
  async function deleteProject(id) {
    await projectApi.delete(id)
    projects.value = projects.value.filter(p => p.id !== id)
    // 如果删除的是当前项目，清除选择
    if (currentProject.value?.id === id) {
      clearProject()
      // 自动选择第一个
      if (projects.value.length > 0) {
        selectProject(projects.value[0])
      }
    }
  }
  
  return {
    projects,
    currentProject,
    loading,
    hasProject,
    projectName,
    projectCode,
    projectIcon,
    projectColor,
    loadProjects,
    selectProject,
    clearProject,
    createProject,
    updateProject,
    deleteProject
  }
})
