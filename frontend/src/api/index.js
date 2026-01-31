import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// ===== 设备 API =====
export const deviceApi = {
  // 获取设备列表
  list: () => api.get('/devices'),
  listAndroid: () => api.get('/devices/android'),
  listIOS: () => api.get('/devices/ios'),
  get: (udid) => api.get(`/devices/${udid}`),

  // 设备操作
  occupy: (udid) => api.post(`/devices/${udid}/occupy`),
  release: (udid) => api.post(`/devices/${udid}/release`),

  // 截图
  screenshot: (udid, platform) => api.get(`/devices/${udid}/screenshot?platform=${platform}`, { responseType: 'blob' }),
  screenshotBase64: (udid, platform, wdaPort = 0) => api.get(`/devices/${udid}/screenshot-base64?platform=${platform}&wda_port=${wdaPort}`),

  // 设备控制
  tap: (udid, x, y, platform) => api.post(`/devices/${udid}/tap?x=${x}&y=${y}&platform=${platform}`),
  swipe: (udid, startX, startY, endX, endY, duration, platform) =>
    api.post(`/devices/${udid}/swipe?start_x=${startX}&start_y=${startY}&end_x=${endX}&end_y=${endY}&duration=${duration}&platform=${platform}`),
  input: (udid, text, platform) => api.post(`/devices/${udid}/input?text=${encodeURIComponent(text)}&platform=${platform}`),
  back: (udid, platform) => api.post(`/devices/${udid}/back?platform=${platform}`),
  home: (udid, platform) => api.post(`/devices/${udid}/home?platform=${platform}`),
  launch: (udid, packageName, activity, platform) =>
    api.post(`/devices/${udid}/launch?package=${encodeURIComponent(packageName)}&activity=${activity || ''}&platform=${platform}`),

  // WebSocket 投屏
  connectMirror: (udid, platform) => {
    const wsUrl = `ws://${window.location.host}/api/devices/${udid}/mirror?platform=${platform}`
    return new WebSocket(wsUrl)
  },

  // Sonic Agent Proxies
  connectAgentTerminal: (udid) => {
    const wsUrl = `ws://${window.location.host}/api/devices/${udid}/agent/terminal`
    return new WebSocket(wsUrl)
  },

  connectAgentGeneral: (udid) => {
    const wsUrl = `ws://${window.location.host}/api/devices/${udid}/agent/general`
    return new WebSocket(wsUrl)
  },

  // ===== iOS 原生设备 API =====

  // 获取原生 iOS 设备列表 (tidevice)
  listIOSNative: () => api.get('/devices/ios/native'),

  // 启动 WDA
  startIOSWda: (udid) => api.post(`/devices/ios/native/${udid}/start-wda`),

  // iOS 原生投屏 WebSocket
  connectIOSNativeMirror: (udid) => {
    const wsUrl = `ws://${window.location.host}/api/devices/ios/native/${udid}/mirror`
    return new WebSocket(wsUrl)
  },

  // iOS 原生设备事件 WebSocket
  connectIOSDeviceEvents: () => {
    const wsUrl = `ws://${window.location.host}/api/devices/ws/ios-events`
    return new WebSocket(wsUrl)
  },

  // iOS 原生控制
  iosNativeTap: (udid, x, y) => api.post(`/devices/ios/native/${udid}/tap?x=${x}&y=${y}`),
  iosNativeSwipe: (udid, fromX, fromY, toX, toY, duration = 0.3) =>
    api.post(`/devices/ios/native/${udid}/swipe?from_x=${fromX}&from_y=${fromY}&to_x=${toX}&to_y=${toY}&duration=${duration}`),
  iosNativeHome: (udid) => api.post(`/devices/ios/native/${udid}/home`),

  // iOS MJPEG 流 URL
  getIOSMjpegUrl: (udid) => `/api/devices/ios/native/${udid}/mjpeg`,

  // iOS Scheme 跳转
  iosSchemeJump: (url, wdaUrl) => api.post('/devices/ios/native/scheme-jump', null, { params: { url, wda_url: wdaUrl } })
}

// ===== 用例 API =====
export const caseApi = {
  list: (params) => api.get('/cases', { params }),
  get: (id) => api.get(`/cases/${id}`),
  create: (data) => api.post('/cases', data),
  update: (id, data) => api.put(`/cases/${id}`, data),
  delete: (id) => api.delete(`/cases/${id}`),
  duplicate: (id) => api.post(`/cases/${id}/duplicate`),
  validateYaml: (yamlContent) => api.post('/cases/validate-yaml', { yaml_content: yamlContent }),
  fromSteps: (data) => api.post('/cases/from-steps', data)
}

// ===== 执行 API =====
export const executionApi = {
  run: (caseId, deviceId) => api.post('/execution/run', { case_id: caseId, device_id: deviceId }),
  list: (params) => api.get('/execution', { params }),
  get: (id) => api.get(`/execution/${id}`),

  // WebSocket 日志
  connectLogs: (executionId) => {
    const wsUrl = `ws://${window.location.host}/api/execution/${executionId}/logs`
    return new WebSocket(wsUrl)
  }
}

// ===== AI 配置 API =====
export const aiConfigApi = {
  list: () => api.get('/ai-config'),
  get: (id) => api.get(`/ai-config/${id}`),
  create: (data) => api.post('/ai-config', data),
  update: (id, data) => api.put(`/ai-config/${id}`, data),
  delete: (id) => api.delete(`/ai-config/${id}`),
  activate: (id) => api.post(`/ai-config/${id}/activate`),
  getActive: () => api.get('/ai-config/active/current'),
  test: (data) => api.post('/ai-config/test', data)
}

// ===== AI 知识库 API =====
export const knowledgeApi = {
  // 分析页面截图（视觉模型处理较慢，超时设为 5 分钟）
  analyzePage: (data) => api.post('/ai/analyze-page', data, { timeout: 300000 }),
  
  // 语义搜索元素
  searchElements: (data) => api.post('/ai/search-elements', data),
  
  // 获取应用列表
  getApps: (params) => api.get('/ai/apps', { params }),
  
  // 获取页面列表
  getPages: (params) => api.get('/ai/pages', { params }),
  
  // 获取页面元素
  getPageElements: (pageId, params) => api.get(`/ai/pages/${pageId}/elements`, { params }),
  
  // 获取统计信息
  getStats: () => api.get('/ai/stats'),
  
  // 删除页面
  deletePage: (pageId) => api.delete(`/ai/pages/${pageId}`),
  
  // 删除应用
  deleteApp: (appId) => api.delete(`/ai/apps/${appId}`)
}

// ===== 知识图谱探索 API =====
export const explorationApi = {
  // 开始探索会话
  startExploration: (data) => api.post('/knowledge/exploration/start', data),
  
  // 结束探索会话
  endExploration: (sessionId) => api.post('/knowledge/exploration/end', { session_id: sessionId }),
  
  // 记录页面跳转（视觉模型处理较慢，超时设为 5 分钟）
  recordTransition: (data) => api.post('/knowledge/exploration/record-transition', data, { timeout: 300000 }),
  
  // 更新当前页面
  updateCurrentPage: (sessionId, pageId) => api.post('/knowledge/exploration/update-current-page', {
    session_id: sessionId,
    page_id: pageId
  }),
  
  // 获取 App 知识图谱
  getAppGraph: (appId) => api.get(`/knowledge/exploration/graph/${appId}`),
  
  // 查找路径
  findPath: (appId, fromPage, toPage) => api.post('/knowledge/exploration/find-path', {
    app_id: appId,
    from_page: fromPage,
    to_page: toPage
  }),
  
  // 获取页面跳转关系
  getPageTransitions: (pageId) => api.get(`/knowledge/exploration/page/${pageId}/transitions`),
  
  // 获取活跃会话列表
  listSessions: () => api.get('/knowledge/exploration/sessions')
}

// ===== LLM 配置 API =====
export const llmApi = {
  // 供应商管理
  listProviders: (includeDisabled = false) => api.get(`/llm/providers?include_disabled=${includeDisabled}`),
  getProvider: (id, includeKey = false) => api.get(`/llm/providers/${id}?include_key=${includeKey}`),
  createProvider: (data) => api.post('/llm/providers', data),
  updateProvider: (id, data) => api.put(`/llm/providers/${id}`, data),
  deleteProvider: (id) => api.delete(`/llm/providers/${id}`),
  
  // 模型管理
  listModels: (params) => api.get('/llm/models', { params }),
  createModel: (data) => api.post('/llm/models', data),
  updateModel: (id, data) => api.put(`/llm/models/${id}`, data),
  deleteModel: (id) => api.delete(`/llm/models/${id}`),
  
  // 用量统计
  getUsageStats: (hours = 24, providerId) => api.get('/llm/usage/stats', { params: { hours, provider_id: providerId } }),
  getUsageTrend: (hours = 24, interval = 'hour') => api.get('/llm/usage/trend', { params: { hours, interval } }),
  getUsageByModel: (hours = 24, detailed = false) => api.get('/llm/usage/by-model', { params: { hours, detailed } })
}

// ===== 系统 API =====
export const systemApi = {
  health: () => api.get('/health'),
  info: () => api.get('/')
}

export default api
