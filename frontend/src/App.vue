<template>
  <el-config-provider :locale="zhCn">
    <!-- 等待路由就绪 -->
    <template v-if="isRouterReady">
      <!-- 公开页面（登录/注册）直接显示 -->
      <router-view v-if="route.meta.public" />
      
      <!-- 主布局 - 仅已登录时显示 -->
      <div v-else-if="userStore.isLoggedIn" class="app-layout">
      <!-- 第一行：白色主导航栏 -->
      <header class="main-header">
        <div class="header-left">
          <div class="logo">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" width="24" height="24">
                <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" fill="url(#logoGradient)" stroke="none"/>
                <defs>
                  <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#667eea"/>
                    <stop offset="100%" style="stop-color:#764ba2"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <span class="logo-text">测试平台</span>
          </div>
          
          <!-- 项目选择器 -->
          <el-dropdown trigger="click" class="project-selector" @command="handleProjectSelect">
            <div class="project-trigger">
              <span class="project-icon">{{ projectStore.projectIcon }}</span>
              <span class="project-name">{{ projectStore.projectName }}</span>
              <el-icon class="project-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="project in projectStore.projects" 
                  :key="project.id"
                  :command="project"
                  :class="{ 'is-active': projectStore.currentProject?.id === project.id }"
                >
                  <span class="dropdown-project-icon">{{ project.icon }}</span>
                  <span class="dropdown-project-name">{{ project.name }}</span>
                </el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" divided command="__create__">
                  <el-icon><Plus /></el-icon>
                  <span>新建项目</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 分隔线 -->
          <div class="header-divider"></div>
        </div>
        
        <!-- 主导航菜单 -->
        <nav class="main-nav">
          <!-- 数据看板 -->
          <span 
            class="nav-item" 
            :class="{ active: currentNav === 'dashboard' }"
            @click="navTo('/dashboard')"
          >
            <el-icon><DataLine /></el-icon>
            <span>看板</span>
          </span>
          
          <!-- UI自动化 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'ui' }">
              <el-icon><Monitor /></el-icon>
              <span>UI自动化</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/ui/apps">应用管理</el-dropdown-item>
                <el-dropdown-item command="/ui/mirror">真机调试</el-dropdown-item>
                <el-dropdown-item command="/ui/scripts">脚本管理</el-dropdown-item>
                <el-dropdown-item command="/ui/knowledge">页面知识库</el-dropdown-item>
                <el-dropdown-item command="/ui/tasks">任务管理</el-dropdown-item>
                <el-dropdown-item command="/ui/reports">测试报告</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- Web自动化 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'web' }">
              <el-icon><ChromeFilled /></el-icon>
              <span>Web自动化</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/web/cases">用例管理</el-dropdown-item>
                <el-dropdown-item command="/web/tasks">任务管理</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- API自动化 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'api' }">
              <el-icon><Connection /></el-icon>
              <span>API自动化</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/api/cases">用例管理</el-dropdown-item>
                <el-dropdown-item command="/api/mock">Mock服务</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 数据工厂 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'data' }">
              <el-icon><Coin /></el-icon>
              <span>数据工厂</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/data/factory">数据生成</el-dropdown-item>
                <el-dropdown-item command="/data/env">环境变量</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 用例智能生成（独立导航） -->
          <span 
            class="nav-item" 
            :class="{ active: currentNav === 'tcg' }"
            @click="navTo('/tcg')"
          >
            <el-icon><MagicStick /></el-icon>
            <span>用例生成</span>
          </span>
          
          <!-- AI 中心 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'llm' }">
              <el-icon><Setting /></el-icon>
              <span>AI 配置</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/llm/providers">模型供应商</el-dropdown-item>
                <el-dropdown-item command="/llm/skills">Skills技能</el-dropdown-item>
                <el-dropdown-item command="/llm/usage">用量统计</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          
          <!-- 项目管理（仅管理员可见） -->
          <span 
            v-if="userStore.isAdmin"
            class="nav-item" 
            :class="{ active: currentNav === 'project' }"
            @click="navTo('/project/manage')"
          >
            <el-icon><Setting /></el-icon>
            <span>项目管理</span>
          </span>
        </nav>
        
        <!-- 右侧用户 -->
        <div class="header-right">
          <el-dropdown trigger="click" @command="handleUserCommand">
            <div class="user-area">
              <div class="user-avatar-cartoon" v-html="userStore.avatarSvg"></div>
              <span class="user-name">{{ userStore.nickname }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item v-if="userStore.isAdmin" command="users">用户管理</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 第二行：标签栏（带圆点和滚动箭头） -->
      <div class="tabs-bar">
        <div v-if="showTabsArrow" class="tabs-arrow left" @click="scrollTabs('left')">
          <el-icon><ArrowLeft /></el-icon>
        </div>
        <div class="tabs-wrapper" ref="tabsWrapper">
          <div 
            v-for="tab in openTabs" 
            :key="tab.path"
            class="tab-item"
            :class="{ active: currentPath === tab.path }"
            @click="switchTab(tab)"
          >
            <span class="tab-dot" :class="{ active: currentPath === tab.path }"></span>
            <span class="tab-title">{{ tab.title }}</span>
            <el-icon class="tab-close" @click.stop="closeTab(tab)"><Close /></el-icon>
          </div>
        </div>
        <div v-if="showTabsArrow" class="tabs-arrow right" @click="scrollTabs('right')">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
      
      <!-- 内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive :include="cachedViews">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </main>
    </div>
    </template>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { 
  ArrowDown, ArrowLeft, ArrowRight, Close,
  DataLine, Monitor, ChromeFilled, Connection, 
  Coin, Iphone, Folder, MagicStick, Setting, Plus
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const tabsWrapper = ref(null)
const userStore = useUserStore()
const projectStore = useProjectStore()

// 路由就绪状态
const isRouterReady = ref(false)
onMounted(async () => {
  await router.isReady()
  isRouterReady.value = true
  // 加载项目列表
  if (userStore.isLoggedIn) {
    projectStore.loadProjects()
  }
})

const currentPath = computed(() => route.path)

// 项目选择处理
function handleProjectSelect(command) {
  if (command === '__create__') {
    router.push('/project/manage?action=create')
  } else {
    projectStore.selectProject(command)
  }
}

// 用户操作处理
function handleUserCommand(command) {
  switch (command) {
    case 'profile':
      router.push('/settings')
      break
    case 'users':
      router.push('/settings?tab=users')
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning'
      }).then(() => {
        userStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      }).catch(() => {})
      break
  }
}

// 缓存的页面组件名称（动态管理，关闭标签时清除）
const cachedViews = ref([])

// 路由路径到组件名的映射（用于缓存管理）
// 这些组件会被 keep-alive 缓存，关闭标签时自动清除缓存
const routeComponentMap = {
  '/ui/scripts/new': 'ScriptEditorView',
  '/ui/mirror': 'MirrorView',
  '/ui/knowledge/new': 'PageAnalysisView',
  '/tcg': 'TcgWorkspaceView',
}

// 根据路由获取组件名（支持动态路由如 /ui/scripts/:id/edit）
function getComponentName(path) {
  // 精确匹配
  if (routeComponentMap[path]) return routeComponentMap[path]
  // 模糊匹配（处理 /ui/scripts/:id/edit 这类路由）
  if (path.includes('/scripts/') && path.includes('/edit')) return 'ScriptEditorView'
  // 页面详情不需要缓存
  return null
}

const currentNav = computed(() => {
  const path = route.path
  if (path === '/' || path.startsWith('/dashboard')) return 'dashboard'
  if (path.startsWith('/ui') || path.startsWith('/app')) return 'ui'
  if (path.startsWith('/web')) return 'web'
  if (path.startsWith('/api')) return 'api'
  if (path.startsWith('/data')) return 'data'
  if (path.startsWith('/device')) return 'device'
  if (path.startsWith('/plan')) return 'plan'
  if (path.startsWith('/tcg')) return 'tcg'
  if (path.startsWith('/llm')) return 'llm'
  if (path.startsWith('/project')) return 'project'
  return ''
})

const openTabs = ref([
  { path: '/dashboard', title: '数据看板' }
])

// 当标签数量超过6个时显示左右箭头
const showTabsArrow = computed(() => openTabs.value.length > 6)

watch(() => route.path, (newPath) => {
  // 公开页面（登录、注册等）不添加到标签栏
  if (route.meta?.public) return
  
  const title = route.meta?.title || '页面'
  const exists = openTabs.value.find(t => t.path === newPath)
  if (!exists && newPath !== '/') {
    openTabs.value.push({ path: newPath, title })
  }
  
  // 添加到缓存（如果是需要缓存的组件）
  const componentName = getComponentName(newPath)
  if (componentName && !cachedViews.value.includes(componentName)) {
    cachedViews.value.push(componentName)
  }
}, { immediate: true })

function navTo(path) {
  if (path) router.push(path)
}

function switchTab(tab) {
  router.push(tab.path)
}

function closeTab(tab) {
  const idx = openTabs.value.findIndex(t => t.path === tab.path)
  if (idx > -1 && openTabs.value.length > 1) {
    openTabs.value.splice(idx, 1)
    
    // 从缓存中移除组件（确保组件完全销毁重置状态）
    const componentName = getComponentName(tab.path)
    if (componentName) {
      const cacheIdx = cachedViews.value.indexOf(componentName)
      if (cacheIdx > -1) {
        cachedViews.value.splice(cacheIdx, 1)
      }
    }
    
    if (tab.path === route.path) {
      const nextTab = openTabs.value[Math.max(0, idx - 1)]
      if (nextTab) router.push(nextTab.path)
    }
  }
}

function scrollTabs(direction) {
  if (tabsWrapper.value) {
    const scrollAmount = 200
    tabsWrapper.value.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth'
    })
  }
}
</script>

<style lang="scss">
:root {
  --header-height: 50px;
  --tabs-height: 42px;
  --primary-color: #409eff;
  --primary-light: #ecf5ff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --text-color: #303133;
  --text-secondary: #606266;
  --text-muted: #909399;
  --border-color: #e4e7ed;
  --bg-color: #f5f7fa;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  color: var(--text-color);
  background: var(--bg-color);
}

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh; /* 关键：固定高度为视口高度，不允许超出 */
  max-height: 100vh;
  overflow: hidden;
}

// ==================== 第一行：白色主导航栏 ====================
.main-header {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 16px;
  flex-shrink: 0;
  position: relative;
  overflow: visible;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 16px;
  flex-shrink: 0;
  
  .logo-icon {
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  
  .logo-text {
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    white-space: nowrap;
  }
}

// 分隔线
.header-divider {
  width: 1px;
  height: 20px;
  background: #e2e8f0;
  margin: 0 8px;
}

// 项目选择器
.project-selector {
  margin-right: 8px;
  
  .project-trigger {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      background: #f1f5f9;
      border-color: #cbd5e1;
    }
  }
  
  .project-icon {
    font-size: 16px;
  }
  
  .project-name {
    font-size: 14px;
    font-weight: 500;
    color: #1e293b;
    max-width: 70px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .project-arrow {
    font-size: 12px;
    color: #64748b;
  }
}

// 项目下拉菜单样式
.dropdown-project-icon {
  margin-right: 8px;
}

.dropdown-project-name {
  flex: 1;
}


.main-nav {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
  height: 100%;
  
  .nav-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0 16px;
    height: 100%;
    color: #000000;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
    position: relative;
    border-radius: 0;
    border-bottom: 3px solid transparent;
    box-sizing: border-box;
    
    .el-icon {
      font-size: 15px;
      color: inherit;
    }
    
    .arrow {
      font-size: 11px;
      margin-left: 2px;
      color: #666;
    }
    
    &:hover {
      color: #004E97;
      background: rgba(0, 78, 151, 0.04);
      
      .el-icon { color: #004E97; }
      .arrow { color: #004E97; }
    }
    
    &.active {
      color: #004E97;
      font-weight: 500;
      border-bottom-color: #004E97;
      background: rgba(0, 78, 151, 0.06);
      
      .el-icon { color: #004E97; }
      .arrow { color: #004E97; }
    }
  }
  
  .el-dropdown { 
    height: 100%;
    .nav-item { outline: none; }
  }
}

.header-right {
  margin-left: auto;
  
  .user-area {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover { background: #f5f7fa; }
    
    .user-avatar-cartoon {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      overflow: hidden;
      flex-shrink: 0;
      background: #f1f5f9;
    }
    
    .user-avatar-cartoon :deep(svg) {
      width: 100%;
      height: 100%;
    }
    
    .user-name {
      color: var(--text-color);
      font-size: 14px;
    }
    
    .role-tag {
      margin-left: 4px;
      height: 18px;
      line-height: 16px;
      padding: 0 6px;
      font-size: 10px;
    }
    
    .el-icon {
      color: var(--text-muted);
      font-size: 12px;
    }
  }
}

// ==================== 第二行：标签栏 ====================
.tabs-bar {
  height: var(--tabs-height);
  background: #fafafa;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.tabs-arrow {
  width: 32px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
  border-right: 1px solid var(--border-color);
  
  &.right { border-right: none; border-left: 1px solid var(--border-color); }
  
  &:hover {
    color: var(--primary-color);
    background: #f0f0f0;
  }
}

.tabs-wrapper {
  flex: 1;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding: 0 12px;
  height: 100%;
  align-items: center;
  
  &::-webkit-scrollbar { display: none; }
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  
  .tab-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #d9d9d9;
    flex-shrink: 0;
  }
  
  .tab-title {
    font-size: 13px;
    color: #3E3E3E;
  }
  
  .tab-close {
    font-size: 11px;
    color: #999;
    padding: 2px;
    border-radius: 50%;
    transition: all 0.2s;
    opacity: 0;
    
    &:hover {
      background: rgba(0,0,0,0.06);
      color: var(--danger-color);
    }
  }
  
  &:hover {
    border-color: #d0d0d0;
    
    .tab-close { opacity: 1; }
  }
  
  &.active {
    background: #F1F7FF;
    border-color: #4E70FF;
    
    .tab-dot {
      background: #4E70FF;
    }
    
    .tab-title { 
      color: #4E70FF; 
      font-weight: 500;
    }
    
    .tab-close { 
      opacity: 1;
      color: #4E70FF;
    }
  }
}

// ==================== 内容区 ====================
.main-content {
  flex: 1;
  padding: 0;
  overflow: hidden;
  background: var(--bg-color);
  display: flex;
  flex-direction: column;
  min-height: 0; /* 关键：允许 flex 子元素正确收缩 */
}

// ==================== 下拉菜单 ====================
.nav-dropdown {
  .el-dropdown-menu {
    border-radius: 8px;
    padding: 6px;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    border: 1px solid var(--border-color);
    
    .el-dropdown-menu__item {
      padding: 10px 16px;
      font-size: 14px;
      border-radius: 4px;
      color: var(--text-secondary);
      
      &:hover {
        background: var(--primary-light);
        color: var(--primary-color);
      }
    }
  }
}

// ==================== 滚动条 ====================
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #909399; }

// ==================== Element Plus 弹窗圆角 ====================
.el-dialog {
  border-radius: 10px !important;
  overflow: hidden;
  
  .el-dialog__header {
    padding: 10px 15px;
    margin-right: 0;
    
    .el-dialog__title {
      font-size: 15px;
      font-weight: 600;
      color: #1e293b;
    }
    
    .el-dialog__headerbtn {
      top: 12px;
      right: 14px;
      width: 24px;
      height: 24px;
      
      .el-dialog__close {
        font-size: 14px;
      }
    }
  }
  
  .el-dialog__body {
    padding: 10px 14px;
  }
  
  .el-dialog__footer {
    padding: 10px 15px 12px;
  }
}

// Message Box 弹窗圆角
.el-message-box {
  border-radius: 12px !important;
  padding-bottom: 16px;
  
  .el-message-box__header {
    padding: 14px 16px 10px;
  }
  
  .el-message-box__title {
    font-size: 15px;
    font-weight: 600;
  }
  
  .el-message-box__content {
    padding: 10px 16px;
  }
  
  .el-message-box__btns {
    padding: 8px 16px 0;
  }
}

// Popover 圆角
.el-popover {
  border-radius: 12px !important;
}

// Select dropdown 圆角
.el-select-dropdown {
  border-radius: 10px !important;
}
</style>
