import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器 - 自动添加 Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('xrun_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 跳转登录
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('xrun_token')
      localStorage.removeItem('xrun_user')
      // 如果不在登录页，跳转到登录
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ===== 认证 API =====
export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  // 管理员
  listUsers: (params) => api.get('/auth/users', { params }),
  deleteUser: (userId) => api.delete(`/auth/users/${userId}`)
}

// ===== 项目 API =====
export const projectApi = {
  list: () => api.get('/projects'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  // 成员管理
  listMembers: (projectId) => api.get(`/projects/${projectId}/members`),
  addMember: (projectId, userId, role = 'member') => 
    api.post(`/projects/${projectId}/members`, { user_id: userId, role }),
  removeMember: (projectId, userId) => api.delete(`/projects/${projectId}/members/${userId}`),
  updateMemberRole: (projectId, userId, role) => 
    api.put(`/projects/${projectId}/members/${userId}`, { role }),
  getAvailableUsers: (projectId) => api.get(`/projects/${projectId}/available-users`)
}

// ===== 应用 API =====
export const appApi = {
  list: (params) => api.get('/apps', { params }),
  get: (id) => api.get(`/apps/${id}`),
  create: (data) => api.post('/apps', data),
  update: (id, data) => api.put(`/apps/${id}`, data),
  delete: (id) => api.delete(`/apps/${id}`)
}

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

// ===== AI 配置 API（已废弃，保留向后兼容）=====
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
  
  // 更新页面信息
  updatePage: (pageId, data) => api.put(`/ai/pages/${pageId}`, data),
  
  // 删除页面
  deletePage: (pageId) => api.delete(`/ai/pages/${pageId}`),
  
  // 删除应用
  deleteApp: (appId) => api.delete(`/ai/apps/${appId}`),
  
  // 更新元素
  updateElement: (elementId, data) => api.put(`/ai/elements/${elementId}`, data),
  
  // 删除元素
  deleteElement: (elementId) => api.delete(`/ai/elements/${elementId}`),
  
  // 保存到知识库（数据库 + 向量库）
  saveToKnowledgeBase: (analysisResult, saveToVector = true) => api.post('/ai/save-to-knowledge-base', {
    analysis_result: analysisResult,
    save_to_vector: saveToVector
  }, { timeout: 120000 }),
  
  // ===== 模块管理 =====
  // 获取模块树
  getModuleTree: (appId) => api.get(`/knowledge/modules/tree/${appId}`),
  
  // 获取模块详情
  getModule: (moduleId, includePages = false) => api.get(`/knowledge/modules/${moduleId}?include_pages=${includePages}`),
  
  // 创建模块
  createModule: (data) => api.post('/knowledge/modules', data),
  
  // 更新模块
  updateModule: (moduleId, data) => api.put(`/knowledge/modules/${moduleId}`, data),
  
  // 删除模块
  deleteModule: (moduleId) => api.delete(`/knowledge/modules/${moduleId}`),
  
  // 分配页面到模块
  assignPagesToModule: (moduleId, pageIds) => api.post(`/knowledge/modules/${moduleId}/assign-pages`, { page_ids: pageIds }),
  
  // 从模块移除页面
  removePagesFromModule: (moduleId, pageIds) => api.post(`/knowledge/modules/${moduleId}/remove-pages`, { page_ids: pageIds }),
  
  // 按模块分组获取页面
  getPagesByModule: (appId) => api.get(`/knowledge/modules/app/${appId}/pages-by-module`),
  
  // ===== 知识图谱 =====
  // 获取应用知识图谱
  getAppGraph: (appId) => api.get(`/ai/apps/${appId}/graph`),
  
  // 查找导航路径
  findNavigationPath: (appId, fromPage, toPage) => api.post(`/ai/apps/${appId}/find-path`, {
    from_page: fromPage,
    to_page: toPage
  })
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

// ===== 执行引擎 V2 API =====

// 用例管理 V2
export const caseV2Api = {
  // 列表查询
  list: (params) => api.get('/v2/cases', { params }),
  
  // 获取详情
  get: (id) => api.get(`/v2/cases/${id}`),
  
  // 创建用例
  create: (data) => api.post('/v2/cases', data),
  
  // 更新用例
  update: (id, data) => api.put(`/v2/cases/${id}`, data),
  
  // 删除用例
  delete: (id) => api.delete(`/v2/cases/${id}`),
  
  // 复制用例
  duplicate: (id, newName) => api.post(`/v2/cases/${id}/duplicate`, null, { params: { new_name: newName } }),
  
  // 编译用例（预览生成的 TypeScript）
  compile: (id, variables) => api.post(`/v2/cases/${id}/compile`, variables)
}

// 测试套件/目录 API
export const suiteApi = {
  // 获取套件列表
  list: (params) => api.get('/v2/suites', { params }),
  
  // 获取套件树
  tree: (projectId) => api.get('/v2/suites/tree', { params: { project_id: projectId } }),
  
  // 获取详情
  get: (id) => api.get(`/v2/suites/${id}`),
  
  // 创建套件
  create: (data) => api.post('/v2/suites', data),
  
  // 更新套件
  update: (id, data) => api.put(`/v2/suites/${id}`, data),
  
  // 删除套件
  delete: (id) => api.delete(`/v2/suites/${id}`)
}

// 执行配置 V2
export const configV2Api = {
  // 获取全局配置
  getGlobal: () => api.get('/v2/config'),
  
  // 更新全局配置
  updateGlobal: (data) => api.put('/v2/config', data),
  
  // 获取应用配置（合并全局）
  getAppConfig: (appId) => api.get(`/v2/config/app/${appId}`),
  
  // 更新应用配置
  updateAppConfig: (appId, data) => api.put(`/v2/config/app/${appId}`, data),
  
  // ===== 全局变量 =====
  // 列表
  listVariables: (scope = 'global', scopeId = null) => api.get('/v2/config/variables', { 
    params: { scope, scope_id: scopeId } 
  }),
  
  // 创建变量
  createVariable: (data) => api.post('/v2/config/variables', data),
  
  // 更新变量
  updateVariable: (id, data) => api.put(`/v2/config/variables/${id}`, data),
  
  // 删除变量
  deleteVariable: (id) => api.delete(`/v2/config/variables/${id}`),
  
  // ===== 缓存配置 =====
  // 获取缓存配置
  getCacheConfig: (scope = 'global', scopeId = null) => api.get('/v2/config/cache', {
    params: { scope, scope_id: scopeId }
  }),
  
  // 更新缓存配置
  updateCacheConfig: (data) => api.put('/v2/config/cache', data)
}

// 执行管理 V2
export const executionV2Api = {
  // 启动执行
  run: (data) => api.post('/v2/executions', data),
  
  // 获取执行列表
  list: (params) => api.get('/v2/executions', { params }),
  
  // 获取执行状态
  get: (id) => api.get(`/v2/executions/${id}`),
  
  // 取消执行
  cancel: (id) => api.post(`/v2/executions/${id}/cancel`),
  
  // WebSocket 实时日志
  connectLogs: (executionId) => {
    const wsUrl = `ws://${window.location.host}/api/v2/executions/${executionId}/logs`
    return new WebSocket(wsUrl)
  }
}

// ===== 元素搜索 API（知识库集成）=====
export const elementSearchApi = {
  // 按页面获取元素（用于元素选择器）
  getElementsByPage: (pageId) => api.get(`/ai/pages/${pageId}/elements`),
  
  // 搜索元素（跨页面）
  searchElements: (appId, keyword) => api.post('/ai/search-elements', {
    app_id: appId,
    query: keyword,
    limit: 20
  }),
  
  // 获取页面列表（用于筛选）
  getPages: (appId) => api.get('/ai/pages', { params: { app_id: appId } })
}

export default api
