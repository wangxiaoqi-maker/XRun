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
        
        <h1 class="slogan">加入我们<br/>开启智能测试</h1>
        
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
            <rect x="78" y="125" width="24" height="24" rx="4" fill="#10b981" opacity="0.2"/>
            <path d="M85 137L89 141L97 133" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            
            <!-- 主内容区 -->
            <rect x="120" y="65" width="130" height="95" rx="6" fill="#f0fdf4"/>
            
            <!-- 成功指标 -->
            <circle cx="185" cy="110" r="35" fill="none" stroke="#d1fae5" stroke-width="8"/>
            <circle cx="185" cy="110" r="35" fill="none" stroke="#10b981" stroke-width="8" 
                    stroke-dasharray="176" stroke-dashoffset="35" stroke-linecap="round"
                    transform="rotate(-90 185 110)"/>
            <text x="185" y="115" font-size="16" font-weight="bold" fill="#1e293b" text-anchor="middle">80%</text>
            
            <!-- 小数据卡片 -->
            <rect x="130" y="70" width="45" height="28" rx="4" fill="white"/>
            <rect x="136" y="78" width="20" height="4" rx="1" fill="#10b981"/>
            <rect x="136" y="86" width="30" height="3" rx="1" fill="#d1fae5"/>
            
            <rect x="215" y="70" width="45" height="28" rx="4" fill="white"/>
            <rect x="221" y="78" width="20" height="4" rx="1" fill="#184BFA"/>
            <rect x="221" y="86" width="30" height="3" rx="1" fill="#c7d2fe"/>
            
            <!-- 底部进度条 -->
            <rect x="130" y="150" width="110" height="6" rx="3" fill="#e2e8f0"/>
            <rect x="130" y="150" width="80" height="6" rx="3" fill="#10b981"/>
            
            <!-- 装饰元素 -->
            <circle cx="45" cy="80" r="20" fill="rgba(255,255,255,0.1)"/>
            <circle cx="275" cy="50" r="15" fill="rgba(255,255,255,0.08)"/>
            
            <!-- 浮动小图标 -->
            <g transform="translate(25, 140)">
              <rect width="35" height="35" rx="8" fill="rgba(255,255,255,0.15)"/>
              <circle cx="17.5" cy="17.5" r="8" stroke="white" stroke-width="2" fill="none"/>
              <circle cx="17.5" cy="17.5" r="3" fill="white"/>
            </g>
            
            <g transform="translate(265, 100)">
              <rect width="30" height="30" rx="6" fill="rgba(255,255,255,0.12)"/>
              <path d="M10 15L15 20L25 10" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </g>
          </svg>
        </div>
      </div>
      
      <!-- 右侧注册区域 -->
      <div class="right-panel">
        <h2 class="form-title">注册</h2>
        
        <el-form 
          ref="registerFormRef"
          :model="registerForm" 
          :rules="registerRules"
          class="auth-form"
          @submit.prevent="handleRegister"
        >
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="用户名"
              size="large"
            />
          </el-form-item>
          
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="邮箱（选填）"
              size="large"
            />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="密码"
              size="large"
              show-password
            />
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              size="large"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>
          
          <div class="terms">
            注册即表示同意 <a href="#">服务条款</a> 和 <a href="#">隐私政策</a>
          </div>
          
          <el-button 
            type="primary" 
            size="large"
            class="submit-btn"
            :loading="loading"
            @click="handleRegister"
          >
            立即注册
          </el-button>
        </el-form>
        
        <div class="form-footer">
          <span>已有账号?</span>
          <router-link to="/login" class="link">去登录</router-link>
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

const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2-50 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleRegister() {
  const valid = await registerFormRef.value?.validate().catch(() => false)
  if (!valid) return
  
  loading.value = true
  try {
    const res = await authApi.register({
      username: registerForm.username,
      email: registerForm.email || undefined,
      password: registerForm.password
    })
    userStore.setToken(res.data.access_token)
    userStore.setUser(res.data.user)
    ElMessage.success('注册成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
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
  min-height: 580px;
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
  padding: 50px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.form-title {
  font-size: 28px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 28px 0;
}

.auth-form {
  width: 100%;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 18px;
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

.terms {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 20px;
}

.terms a {
  color: #184BFA;
  text-decoration: none;
}

.terms a:hover {
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
  margin-top: 20px;
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
    min-height: 180px;
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
