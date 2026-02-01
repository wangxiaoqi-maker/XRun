<template>
  <div class="auth-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>
    
    <div class="auth-card">
      <!-- 左侧区域 -->
      <div class="left-panel">
        <div class="brand">
          <svg viewBox="0 0 32 32" width="28" height="28">
            <rect x="4" y="4" width="24" height="24" rx="6" fill="rgba(255,255,255,0.2)"/>
            <path d="M10 10h12M10 16h12M10 22h8" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span class="brand-text">XRun</span>
        </div>
        
        <h1 class="slogan">智能测试<br/>一键启动</h1>
        
        <!-- 数据仪表盘插画 -->
        <div class="illustration">
          <svg viewBox="0 0 300 220" class="ill-svg">
            <!-- 主面板 -->
            <rect x="60" y="30" width="200" height="140" rx="12" fill="white" opacity="0.95"/>
            
            <!-- 顶部状态栏 -->
            <circle cx="80" cy="48" r="4" fill="#f87171"/>
            <circle cx="95" cy="48" r="4" fill="#fbbf24"/>
            <circle cx="110" cy="48" r="4" fill="#34d399"/>
            
            <!-- 侧边栏 -->
            <rect x="70" y="65" width="40" height="95" rx="6" fill="#f1f5f9"/>
            <rect x="78" y="75" width="24" height="6" rx="2" fill="#cbd5e1"/>
            <rect x="78" y="88" width="18" height="4" rx="1" fill="#e2e8f0"/>
            <rect x="78" y="98" width="20" height="4" rx="1" fill="#e2e8f0"/>
            <rect x="78" y="108" width="16" height="4" rx="1" fill="#e2e8f0"/>
            <rect x="78" y="125" width="24" height="24" rx="4" fill="#184BFA" opacity="0.2"/>
            <rect x="84" y="131" width="12" height="12" rx="2" fill="#184BFA"/>
            
            <!-- 主内容区图表 -->
            <rect x="120" y="65" width="130" height="95" rx="6" fill="#eef2ff"/>
            
            <!-- 折线图 -->
            <polyline points="135,130 155,115 175,120 195,95 215,105 235,85" 
                      stroke="#184BFA" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="195" cy="95" r="5" fill="#184BFA"/>
            <circle cx="235" cy="85" r="5" fill="#184BFA"/>
            
            <!-- 柱状图 -->
            <rect x="135" y="135" width="12" height="15" rx="2" fill="#a5b4fc"/>
            <rect x="155" y="125" width="12" height="25" rx="2" fill="#818cf8"/>
            <rect x="175" y="130" width="12" height="20" rx="2" fill="#a5b4fc"/>
            <rect x="195" y="115" width="12" height="35" rx="2" fill="#184BFA"/>
            <rect x="215" y="120" width="12" height="30" rx="2" fill="#818cf8"/>
            
            <!-- 顶部数据卡片 -->
            <rect x="120" y="70" width="55" height="35" rx="4" fill="white"/>
            <text x="128" y="88" font-size="14" font-weight="bold" fill="#1e293b">98%</text>
            <text x="128" y="100" font-size="8" fill="#64748b">通过率</text>
            
            <rect x="182" y="70" width="55" height="35" rx="4" fill="white"/>
            <text x="190" y="88" font-size="14" font-weight="bold" fill="#1e293b">256</text>
            <text x="190" y="100" font-size="8" fill="#64748b">用例数</text>
            
            <!-- 装饰元素 -->
            <circle cx="45" cy="80" r="20" fill="rgba(255,255,255,0.1)"/>
            <circle cx="275" cy="50" r="15" fill="rgba(255,255,255,0.08)"/>
            <rect x="270" y="150" width="30" height="30" rx="8" fill="rgba(255,255,255,0.06)" transform="rotate(15 285 165)"/>
            
            <!-- 浮动小图标 -->
            <g transform="translate(25, 140)">
              <rect width="35" height="35" rx="8" fill="rgba(255,255,255,0.15)"/>
              <path d="M10 17.5L15 22.5L25 12.5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </g>
            
            <g transform="translate(265, 100)">
              <rect width="30" height="30" rx="6" fill="rgba(255,255,255,0.12)"/>
              <circle cx="15" cy="15" r="6" stroke="white" stroke-width="2" fill="none"/>
              <path d="M19 19L24 24" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </g>
          </svg>
        </div>
      </div>
      
      <!-- 右侧登录区域 -->
      <div class="right-panel">
        <h2 class="form-title">登录</h2>
        
        <el-form 
          ref="loginFormRef"
          :model="loginForm" 
          :rules="loginRules"
          class="auth-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              size="large"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          
          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <a href="#" class="forgot-link">忘记密码?</a>
          </div>
          
          <el-button 
            type="primary" 
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>
        
        <div class="form-footer">
          <span>还没有账号?</span>
          <router-link to="/register" class="link">去注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(true)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

async function handleLogin() {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    const res = await authApi.login(loginForm)
    userStore.setToken(res.data.access_token)
    userStore.setUser(res.data.user)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 50%, #f5f0ff 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(24, 75, 250, 0.08), rgba(99, 102, 241, 0.05));
}

.bg-circle-1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: -150px;
}

.bg-circle-2 {
  width: 400px;
  height: 400px;
  bottom: -100px;
  left: -100px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.06), rgba(24, 75, 250, 0.04));
}

.bg-circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 10%;
  background: rgba(24, 75, 250, 0.03);
}

.auth-card {
  display: flex;
  width: 900px;
  min-height: 540px;
  background: white;
  border-radius: 24px;
  box-shadow: 0 25px 60px -15px rgba(24, 75, 250, 0.15), 0 10px 30px -10px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.left-panel {
  width: 420px;
  background: linear-gradient(150deg, #0f3dd9 0%, #184BFA 50%, #3d6afc 100%);
  padding: 40px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 40px;
}

.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: 1px;
}

.slogan {
  font-size: 32px;
  font-weight: 700;
  color: white;
  line-height: 1.3;
  margin: 0 0 auto 0;
}

.illustration {
  margin-top: auto;
}

.ill-svg {
  width: 100%;
  max-width: 300px;
}

.right-panel {
  flex: 1;
  padding: 60px 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-title {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 32px 0;
}

.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.auth-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: none;
  border: 1px solid #e5e7eb;
  padding: 4px 14px;
  height: 50px;
}

.auth-form :deep(.el-input__wrapper:hover) {
  border-color: #184BFA;
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  border-color: #184BFA;
  box-shadow: 0 0 0 3px rgba(24, 75, 250, 0.1);
}

.auth-form :deep(.el-input__inner) {
  height: 100%;
}

.auth-form :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.forgot-link {
  font-size: 13px;
  color: #184BFA;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: #184BFA;
  border: none;
}

.submit-btn:hover {
  background: #0f3dd9;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #64748b;
}

.link {
  color: #184BFA;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .auth-card {
    flex-direction: column;
    width: 100%;
    max-width: 400px;
  }
  
  .left-panel {
    width: 100%;
    min-height: 200px;
    padding: 30px;
  }
  
  .slogan {
    font-size: 24px;
  }
  
  .illustration {
    display: none;
  }
  
  .right-panel {
    padding: 40px 30px;
  }
  
  .bg-circle-1 {
    width: 300px;
    height: 300px;
  }
  
  .bg-circle-2 {
    width: 200px;
    height: 200px;
  }
}
</style>
