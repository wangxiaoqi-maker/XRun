import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  
  // 数据看板
  { path: '/dashboard', name: 'Dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '数据看板' } },
  
  // UI自动化
  { path: '/ui/mirror', name: 'Mirror', component: () => import('../views/app/MirrorView.vue'), meta: { title: '真机调试' } },
  { path: '/ui/scripts', name: 'Scripts', component: () => import('../views/app/ScriptsView.vue'), meta: { title: '脚本管理' } },
  { path: '/ui/scripts/new', name: 'NewScript', component: () => import('../views/app/ScriptEditorView.vue'), meta: { title: '新建脚本' } },
  { path: '/ui/scripts/:id/edit', name: 'EditScript', component: () => import('../views/app/ScriptEditorView.vue'), meta: { title: '编辑脚本' } },
  { path: '/ui/tasks', name: 'Tasks', component: () => import('../views/app/TasksView.vue'), meta: { title: '任务管理' } },
  { path: '/ui/reports', name: 'Reports', component: () => import('../views/app/ReportView.vue'), meta: { title: '测试报告' } },
  { path: '/ui/demo', name: 'Demo', component: () => import('../views/DemoView.vue'), meta: { title: '样式预览' } },
  
  // 设备管理 (已合并到真机调试)
  // { path: '/devices', name: 'DeviceList', component: () => import('../views/app/DevicesView.vue'), meta: { title: '设备管理' } },
  
  // Web 自动化
  { path: '/web/cases', name: 'WebCases', component: () => import('../views/PlaceholderView.vue'), meta: { title: 'Web用例管理' } },
  
  // 桌面自动化
  { path: '/desktop/cases', name: 'DesktopCases', component: () => import('../views/PlaceholderView.vue'), meta: { title: '桌面用例管理' } },
  
  // 数据管理
  { path: '/data/factory', name: 'DataFactory', component: () => import('../views/PlaceholderView.vue'), meta: { title: '数据工厂' } },
  
  // 测试计划
  { path: '/plans', name: 'Plans', component: () => import('../views/PlaceholderView.vue'), meta: { title: '测试计划' } },
  
  // 项目管理
  { path: '/project/list', name: 'ProjectList', component: () => import('../views/PlaceholderView.vue'), meta: { title: '项目管理' } },
  
  // 设置
  { path: '/settings', name: 'Settings', component: () => import('../views/SettingsView.vue'), meta: { title: '系统设置' } },
  
  // LLM 配置
  { path: '/llm/providers', name: 'LLMProviders', component: () => import('../views/llm/ProvidersView.vue'), meta: { title: '模型供应商' } },
  { path: '/llm/usage', name: 'LLMUsage', component: () => import('../views/llm/UsageView.vue'), meta: { title: '用量统计' } },
  
  // 404 - 放在最后
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '自动化测试平台'}`
  next()
})

export default router
