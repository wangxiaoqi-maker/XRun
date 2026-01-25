<template>
  <el-config-provider :locale="zhCn">
    <div class="app-layout">
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
                <el-dropdown-item command="/ui/mirror">真机调试</el-dropdown-item>
                <el-dropdown-item command="/ui/scripts">脚本管理</el-dropdown-item>
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
          

          <!-- 测试计划 -->
          <span 
            class="nav-item" 
            :class="{ active: currentNav === 'plan' }"
            @click="navTo('/plans')"
          >
            <el-icon><Calendar /></el-icon>
            <span>测试计划</span>
          </span>
          
          <!-- 项目管理 -->
          <el-dropdown trigger="click" @command="navTo" popper-class="nav-dropdown">
            <span class="nav-item" :class="{ active: currentNav === 'project' }">
              <el-icon><Folder /></el-icon>
              <span>项目管理</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="/project/list">项目列表</el-dropdown-item>
                <el-dropdown-item command="/project/members">成员管理</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </nav>
        
        <!-- 右侧用户 -->
        <div class="header-right">
          <el-dropdown trigger="click">
            <div class="user-area">
              <el-avatar :size="28" class="user-avatar">{{ username.charAt(0) }}</el-avatar>
              <span class="user-name">{{ username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
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
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { 
  ArrowDown, ArrowLeft, ArrowRight, Close,
  DataLine, Monitor, ChromeFilled, Connection, 
  Coin, Iphone, Calendar, Folder
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const tabsWrapper = ref(null)

const username = ref('测试工程师')
const currentPath = computed(() => route.path)

const currentNav = computed(() => {
  const path = route.path
  if (path === '/' || path.startsWith('/dashboard')) return 'dashboard'
  if (path.startsWith('/ui') || path.startsWith('/app')) return 'ui'
  if (path.startsWith('/web')) return 'web'
  if (path.startsWith('/api')) return 'api'
  if (path.startsWith('/data')) return 'data'
  if (path.startsWith('/device')) return 'device'
  if (path.startsWith('/plan')) return 'plan'
  if (path.startsWith('/project')) return 'project'
  return ''
})

const openTabs = ref([
  { path: '/dashboard', title: '数据看板' }
])

// 当标签数量超过6个时显示左右箭头
const showTabsArrow = computed(() => openTabs.value.length > 6)

watch(() => route.path, (newPath) => {
  const title = route.meta?.title || '页面'
  const exists = openTabs.value.find(t => t.path === newPath)
  if (!exists && newPath !== '/') {
    openTabs.value.push({ path: newPath, title })
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
  min-height: 100vh;
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
  margin-right: 24px;
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
    
    .user-avatar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
      font-size: 12px;
    }
    
    .user-name {
      color: var(--text-color);
      font-size: 14px;
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
  padding: 10px; /* 移除内边距，让子页面自己控制 */
  overflow: auto; /* 改为 hidden，让子页面控制滚动 */
  background: var(--bg-color);
  display: flex; /* 使子页面能够填满 */
  flex-direction: column;
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
</style>
