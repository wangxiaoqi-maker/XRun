import request, { skillApi } from '@/api'
export { skillApi }

const BASE = '/v2/tcg'

// --- 项目管理 ---
export const projectApi = {
  list: (params) => request.get(`${BASE}/projects`, { params }),
  create: (data) => request.post(`${BASE}/projects`, data),
  get: (id) => request.get(`${BASE}/projects/${id}`),
  update: (id, data) => request.put(`${BASE}/projects/${id}`, data),
  delete: (id) => request.delete(`${BASE}/projects/${id}`),
}

// --- 生成会话 ---
export const sessionApi = {
  create: (data) => request.post(`${BASE}/sessions`, data),
  get: (id) => request.get(`${BASE}/sessions/${id}`),
  list: (projectId) => request.get(`${BASE}/sessions`, { params: { project_id: projectId } }),
  start: (id) => request.post(`${BASE}/sessions/${id}/start`, null, { timeout: 120000 }),
  cancel: (id) => request.post(`${BASE}/sessions/${id}/cancel`),
  getTestPoints: (id) => request.get(`${BASE}/sessions/${id}/test-points`),
  confirmTestPoints: (id, data) => request.post(`${BASE}/sessions/${id}/test-points/confirm`, data, { timeout: 120000 }),
  rejectTestPoints: (id, data) => request.post(`${BASE}/sessions/${id}/test-points/reject`, data),
  supplementTestPoints: (id, data) => request.post(`${BASE}/sessions/${id}/test-points/supplement`, data, { timeout: 120000 }),
  // 手动添加测试点
  addTestPoint: (id, data) => request.post(`${BASE}/sessions/${id}/test-points/add`, data),
  // 更新测试点
  updateTestPoint: (sessionId, pointId, data) => request.put(`${BASE}/sessions/${sessionId}/test-points/${pointId}`, data),
  // 删除测试点
  deleteTestPoint: (sessionId, pointId) => request.delete(`${BASE}/sessions/${sessionId}/test-points/${pointId}`),
  reviewCases: (id, data) => request.post(`${BASE}/sessions/${id}/test-cases/review`, data),
  saveCases: (id) => request.post(`${BASE}/sessions/${id}/test-cases/save`),
  regenerateCases: (id, data) => request.post(`${BASE}/sessions/${id}/test-cases/regenerate`, data),
}

// --- 用例管理 ---
export const testCaseApi = {
  list: (params) => request.get(`${BASE}/test-cases`, { params }),
  get: (id) => request.get(`${BASE}/test-cases/${id}`),
  update: (id, data) => request.put(`${BASE}/test-cases/${id}`, data),
  delete: (id) => request.delete(`${BASE}/test-cases/${id}`),
  batchDelete: (caseIds) => request.post(`${BASE}/test-cases/batch-delete`, caseIds),
  batchSave: (data) => request.post(`${BASE}/test-cases/batch-save`, data),
  listTemplates: (projectId) => request.get(`${BASE}/export-templates`, { params: { project_id: projectId } }),
  exportCases: async (params) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const token = localStorage.getItem('xrun_token') || ''
    const response = await fetch(`${baseUrl}/api${BASE}/test-cases/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(params)
    })
    if (!response.ok) {
      throw new Error('Export failed')
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'test_cases.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    return true
  },
}

// --- 文件管理 ---
export const fileApi = {
  upload: (projectId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`${BASE}/files/upload?project_id=${projectId}`, formData)
  },
  list: (projectId) => request.get(`${BASE}/files`, { params: { project_id: projectId } }),
  delete: (id) => request.delete(`${BASE}/files/${id}`),
}

// --- 模块管理 ---
export const moduleApi = {
  list: (projectId) => request.get(`${BASE}/modules`, { params: { project_id: projectId } }),
  create: (data) => request.post(`${BASE}/modules`, data),
  rename: (id, name) => request.put(`${BASE}/modules/${id}`, { name }),
  delete: (id) => request.delete(`${BASE}/modules/${id}`),
}

// --- LLM 模型 ---
export const llmApi = {
  listModels: (modelType) => request.get('/llm/models', { params: modelType ? { model_type: modelType } : {} }),
}

// --- 用例执行 ---
export const executionApi = {
  create: (data) => request.post(`${BASE}/executions`, data),
  get: (id) => request.get(`${BASE}/executions/${id}`),
  list: (params) => request.get(`${BASE}/executions`, { params }),
  updateStep: (execId, stepNum, data) => request.put(`${BASE}/executions/${execId}/steps/${stepNum}`, data),
  complete: (execId, data) => request.put(`${BASE}/executions/${execId}/complete`, data || {}),
}

// --- 知识库 ---
export const knowledgeApi = {
  build: (projectId) => request.post(`${BASE}/knowledge/build`, null, { params: { project_id: projectId } }),
  stats: (projectId) => request.get(`${BASE}/knowledge/stats`, { params: { project_id: projectId } }),
  search: (projectId, query, topK = 10) => request.post(`${BASE}/knowledge/search`, null, { params: { project_id: projectId, query, top_k: topK } }),
  clear: (projectId) => request.delete(`${BASE}/knowledge/clear`, { params: { project_id: projectId } }),
}

// --- 对话 API (多智能体模式) ---
export const conversationApi = {
  create: (data) => request.post(`${BASE}/conversations`, data),
  list: (projectId) => request.get(`${BASE}/conversations`, { params: { project_id: projectId } }),
  delete: (convId) => request.delete(`${BASE}/conversations/${convId}`),
  getMessages: (convId) => request.get(`${BASE}/conversations/${convId}/messages`),
  sendMessage: (convId, data) => request.post(`${BASE}/conversations/${convId}/messages`, data, { timeout: 120000 }),
  getHistory: (convId) => request.get(`${BASE}/conversations/${convId}/history`),
  updateConfig: (convId, data) => request.put(`${BASE}/conversations/${convId}/config`, data),
  updateTitle: (convId, title) => request.put(`${BASE}/conversations/${convId}/title`, { title }),
}

// --- SSE 流 ---
export function createSSEStream(sessionId, token) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const url = `${baseUrl}/api${BASE}/sessions/${sessionId}/stream`
  const eventSource = new EventSource(`${url}?token=${token}`)
  return eventSource
}

export function connectSSE(sessionId, handlers = {}) {
  const token = localStorage.getItem('xrun_token') || ''
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const url = `${baseUrl}/api${BASE}/sessions/${sessionId}/stream?token=${encodeURIComponent(token)}`

  const eventSource = new EventSource(url)

  const eventTypes = ['progress', 'stage', 'thinking', 'error', 'test_points', 'test_cases', 'done', 'ping', 'skills', 'thinking_stream', 'thinking_done']
  eventTypes.forEach(type => {
    eventSource.addEventListener(type, (event) => {
      try {
        const data = JSON.parse(event.data)
        if (handlers[type]) handlers[type](data)
        if (handlers.onAny) handlers.onAny(type, data)
      } catch (e) {
        console.error(`SSE parse error (${type}):`, e)
      }
    })
  })

  eventSource.onerror = (e) => {
    if (handlers.onError) handlers.onError(e)
    eventSource.close()
  }

  return eventSource
}

/**
 * 连接对话级 SSE（多智能体模式）
 * 同时支持 agent_event（新格式）和旧格式事件
 */
export function connectConversationSSE(convId, handlers = {}) {
  const token = localStorage.getItem('xrun_token') || ''
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const url = `${baseUrl}/api${BASE}/conversations/${convId}/stream?token=${encodeURIComponent(token)}`

  const eventSource = new EventSource(url)

  eventSource.addEventListener('agent_event', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (handlers.onAgentEvent) handlers.onAgentEvent(data)
      if (handlers.onAny) handlers.onAny('agent_event', data)
    } catch (e) {
      console.error('SSE agent_event parse error:', e)
    }
  })

  const legacyTypes = ['progress', 'stage', 'thinking', 'error', 'test_points', 'test_cases',
    'done', 'ping', 'skills', 'thinking_stream', 'thinking_done', 'chat_response',
    'content_stream', 'content_done', 'usage']
  legacyTypes.forEach(type => {
    eventSource.addEventListener(type, (event) => {
      try {
        const data = JSON.parse(event.data)
        if (handlers[type]) handlers[type](data)
        if (handlers.onAny) handlers.onAny(type, data)
      } catch (e) {
        console.error(`SSE parse error (${type}):`, e)
      }
    })
  })

  eventSource.onerror = (e) => {
    if (handlers.onError) handlers.onError(e)
    eventSource.close()
  }

  return eventSource
}
