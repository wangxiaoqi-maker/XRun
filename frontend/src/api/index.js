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
  screenshotBase64: (udid, platform) => api.get(`/devices/${udid}/screenshot-base64?platform=${platform}`),

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

// ===== 系统 API =====
export const systemApi = {
  health: () => api.get('/health'),
  info: () => api.get('/')
}

export default api
