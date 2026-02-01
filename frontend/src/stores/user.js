/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'xrun_token'
const USER_KEY = 'xrun_user'

// 卡通人物头像 SVG 集合
const CARTOON_AVATARS = [
  // 男孩 1 - 蓝色帽子
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#e3f2fd"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="20" ry="15" fill="#42a5f5"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 65 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M25 40 Q50 15 75 40 L70 45 Q50 25 30 45 Z" fill="#1976d2"/><circle cx="50" cy="22" r="6" fill="#1976d2"/></svg>`,
  
  // 女孩 1 - 粉色头发
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#fce4ec"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="18" ry="12" fill="#ec407a"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 65 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M20 50 Q20 20 50 20 Q80 20 80 50" fill="#f06292"/><circle cx="25" cy="55" r="8" fill="#f06292"/><circle cx="75" cy="55" r="8" fill="#f06292"/></svg>`,
  
  // 男孩 2 - 酷酷墨镜
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#fff3e0"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="72" rx="18" ry="10" fill="#78909c"/><rect x="28" y="45" width="20" height="12" rx="3" fill="#1e293b"/><rect x="52" y="45" width="20" height="12" rx="3" fill="#1e293b"/><path d="M48 51 L52 51" stroke="#1e293b" stroke-width="2"/><path d="M45 62 Q50 66 55 62" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M30 35 Q50 25 70 35 L68 42 Q50 35 32 42 Z" fill="#455a64"/></svg>`,
  
  // 女孩 2 - 双马尾
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#e8f5e9"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="16" ry="10" fill="#66bb6a"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 65 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><ellipse cx="22" cy="45" rx="10" ry="18" fill="#8d6e63"/><ellipse cx="78" cy="45" rx="10" ry="18" fill="#8d6e63"/><path d="M25 35 Q50 20 75 35 L70 50 Q50 35 30 50 Z" fill="#8d6e63"/><circle cx="22" cy="30" r="5" fill="#66bb6a"/><circle cx="78" cy="30" r="5" fill="#66bb6a"/></svg>`,
  
  // 男孩 3 - 运动风
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#fff8e1"/><circle cx="50" cy="55" r="30" fill="#ffb74d"/><ellipse cx="50" cy="72" rx="18" ry="10" fill="#ff7043"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M42 62 Q50 68 58 62" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M28 38 Q50 22 72 38 L68 48 Q50 38 32 48 Z" fill="#ff5722"/><rect x="45" y="22" width="10" height="8" fill="#ff5722"/></svg>`,
  
  // 女孩 3 - 紫色短发
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#f3e5f5"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="16" ry="10" fill="#ab47bc"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 64 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M22 55 Q22 25 50 25 Q78 25 78 55" fill="#7b1fa2"/><path d="M30 55 L28 70" stroke="#7b1fa2" stroke-width="8" stroke-linecap="round"/><path d="M70 55 L72 70" stroke="#7b1fa2" stroke-width="8" stroke-linecap="round"/></svg>`,
  
  // 男孩 4 - 商务风
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#eceff1"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><path d="M35 68 L50 75 L65 68 L65 85 L35 85 Z" fill="#37474f"/><rect x="47" y="68" width="6" height="10" fill="#90a4ae"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 64 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M30 40 Q50 28 70 40 L65 50 Q50 42 35 50 Z" fill="#455a64"/></svg>`,
  
  // 女孩 4 - 可爱刘海
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#ffebee"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="16" ry="10" fill="#ef5350"/><circle cx="40" cy="52" r="4" fill="#1e293b"/><circle cx="60" cy="52" r="4" fill="#1e293b"/><circle cx="42" cy="51" r="1.5" fill="white"/><circle cx="62" cy="51" r="1.5" fill="white"/><path d="M45 62 Q50 66 55 62" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M20 50 Q20 20 50 20 Q80 20 80 50" fill="#5d4037"/><path d="M30 45 L35 30 L42 45 L48 28 L55 45 L62 30 L68 45" fill="#5d4037"/></svg>`,
  
  // 男孩 5 - 艺术家
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#e0f2f1"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="72" rx="18" ry="10" fill="#26a69a"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 62 Q50 66 55 62" stroke="#1e293b" stroke-width="2" fill="none"/><ellipse cx="50" cy="30" rx="25" ry="12" fill="#004d40"/><path d="M25 30 Q50 15 75 30" fill="#00695c"/></svg>`,
  
  // 女孩 5 - 波浪卷发
  `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="50" fill="#fbe9e7"/><circle cx="50" cy="55" r="30" fill="#ffcc80"/><ellipse cx="50" cy="70" rx="16" ry="10" fill="#ff8a65"/><circle cx="40" cy="50" r="4" fill="#1e293b"/><circle cx="60" cy="50" r="4" fill="#1e293b"/><path d="M45 60 Q50 65 55 60" stroke="#1e293b" stroke-width="2" fill="none"/><path d="M18 55 Q15 25 50 22 Q85 25 82 55" fill="#d84315"/><circle cx="20" cy="50" r="8" fill="#d84315"/><circle cx="80" cy="50" r="8" fill="#d84315"/><circle cx="25" cy="62" r="6" fill="#d84315"/><circle cx="75" cy="62" r="6" fill="#d84315"/></svg>`
]

// 根据字符串生成固定的哈希索引
function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const nickname = computed(() => user.value?.nickname || user.value?.username || '用户')
  const avatar = computed(() => user.value?.avatar || '')
  
  // 基于用户 ID 生成固定的卡通头像
  const avatarSvg = computed(() => {
    const userId = user.value?.id || user.value?.username || 'default'
    const hash = hashCode(userId)
    return CARTOON_AVATARS[hash % CARTOON_AVATARS.length]
  })
  
  // 旧的配置保留兼容
  const avatarConfig = computed(() => {
    const userId = user.value?.id || user.value?.username || 'default'
    const hash = hashCode(userId)
    return {
      color: ['#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316'][hash % 5],
      icon: ''
    }
  })
  
  // 方法
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem(TOKEN_KEY, newToken)
  }
  
  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem(USER_KEY, JSON.stringify(newUser))
  }
  
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
  
  function updateUser(updates) {
    if (user.value) {
      user.value = { ...user.value, ...updates }
      localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    }
  }
  
  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    nickname,
    avatar,
    avatarSvg,
    avatarConfig,
    setToken,
    setUser,
    logout,
    updateUser
  }
})
