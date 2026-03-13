import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { projectApi } from '@/api/tcg'

export const useTcgProjectStore = defineStore('tcgProject', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  const total = ref(0)

  async function fetchProjects(page = 1, pageSize = 20) {
    loading.value = true
    try {
      const res = await projectApi.list({ page, page_size: pageSize })
      const data = res.data || res
      projects.value = data.items || []
      total.value = data.total || 0
    } finally {
      loading.value = false
    }
  }

  async function createProject(data) {
    const res = await projectApi.create(data)
    await fetchProjects()
    return res.data || res
  }

  async function deleteProject(id) {
    await projectApi.delete(id)
    await fetchProjects()
  }

  async function setCurrentProject(project) {
    currentProject.value = project
  }

  return {
    projects,
    currentProject,
    loading,
    total,
    fetchProjects,
    createProject,
    deleteProject,
    setCurrentProject,
  }
})
