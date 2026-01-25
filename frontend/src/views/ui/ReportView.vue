<template>
  <div class="report-page">
    <!-- 报告头部 -->
    <div class="report-header">
      <div class="header-left">
        <el-button text @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="report-title">
          <h1>{{ report.caseName || '执行报告' }}</h1>
          <div class="report-meta">
            <el-tag :type="getStatusType(report.status)" size="small">
              {{ getStatusText(report.status) }}
            </el-tag>
            <span class="meta-item">
              <el-icon><Calendar /></el-icon>
              {{ formatDate(report.startTime) }}
            </span>
            <span class="meta-item">
              <el-icon><Timer /></el-icon>
              耗时: {{ report.duration }}
            </span>
            <span class="meta-item">
              <el-icon><Iphone /></el-icon>
              {{ report.device?.name }}
            </span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="downloadReport">
          <el-icon><Download /></el-icon> 下载报告
        </el-button>
        <el-button type="primary" @click="rerunCase">
          <el-icon><RefreshRight /></el-icon> 重新执行
        </el-button>
      </div>
    </div>
    
    <!-- 统计概览 -->
    <div class="report-summary">
      <div class="summary-card">
        <div class="summary-value">{{ report.totalSteps }}</div>
        <div class="summary-label">总步骤</div>
      </div>
      <div class="summary-card success">
        <div class="summary-value">{{ report.passedSteps }}</div>
        <div class="summary-label">通过</div>
      </div>
      <div class="summary-card danger">
        <div class="summary-value">{{ report.failedSteps }}</div>
        <div class="summary-label">失败</div>
      </div>
      <div class="summary-card warning">
        <div class="summary-value">{{ report.skippedSteps }}</div>
        <div class="summary-label">跳过</div>
      </div>
      <div class="summary-card info">
        <div class="summary-value">{{ report.passRate }}%</div>
        <div class="summary-label">通过率</div>
      </div>
    </div>
    
    <!-- 步骤详情 - 参考 Midscene 风格 -->
    <div class="steps-timeline">
      <div class="timeline-header">
        <h2>执行步骤</h2>
        <div class="timeline-filters">
          <el-radio-group v-model="stepFilter" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="passed">通过</el-radio-button>
            <el-radio-button label="failed">失败</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <div class="timeline-content">
        <div 
          v-for="(step, index) in filteredSteps" 
          :key="index"
          class="timeline-item"
          :class="step.status"
        >
          <!-- 时间线 -->
          <div class="timeline-line">
            <div class="timeline-dot" :class="step.status">
              <el-icon v-if="step.status === 'passed'"><Check /></el-icon>
              <el-icon v-else-if="step.status === 'failed'"><Close /></el-icon>
              <el-icon v-else><Clock /></el-icon>
            </div>
          </div>
          
          <!-- 步骤内容 -->
          <div class="timeline-card">
            <div class="card-header">
              <div class="step-info">
                <span class="step-number">Step {{ index + 1 }}</span>
                <span class="step-type">{{ getStepTypeLabel(step.type) }}</span>
                <el-tag size="small" :type="getStatusType(step.status)">
                  {{ getStatusText(step.status) }}
                </el-tag>
              </div>
              <div class="step-time">
                <el-icon><Timer /></el-icon>
                {{ step.duration }}ms
              </div>
            </div>
            
            <div class="card-body">
              <!-- AI 操作描述 -->
              <div v-if="step.prompt" class="step-prompt">
                <el-icon><MagicStick /></el-icon>
                <span>{{ step.prompt }}</span>
              </div>
              
              <!-- 操作详情 -->
              <div class="step-detail">
                <template v-if="step.type === 'tap' || step.type === 'aiTap'">
                  点击坐标: ({{ step.x }}, {{ step.y }})
                </template>
                <template v-else-if="step.type === 'input' || step.type === 'aiInput'">
                  输入内容: "{{ step.text }}"
                </template>
                <template v-else-if="step.type === 'swipe'">
                  滑动: ({{ step.startX }}, {{ step.startY }}) → ({{ step.endX }}, {{ step.endY }})
                </template>
                <template v-else-if="step.type === 'aiAssert'">
                  断言: {{ step.prompt }}
                </template>
              </div>
              
              <!-- 截图对比 - Midscene 风格 -->
              <div v-if="step.screenshots" class="screenshots-section">
                <div class="screenshots-row">
                  <div class="screenshot-item" v-if="step.screenshots.before">
                    <div class="screenshot-label">执行前</div>
                    <div class="screenshot-wrapper">
                      <img :src="step.screenshots.before" @click="previewImage(step.screenshots.before)" />
                    </div>
                  </div>
                  <div class="screenshot-item" v-if="step.screenshots.after">
                    <div class="screenshot-label">执行后</div>
                    <div class="screenshot-wrapper">
                      <img :src="step.screenshots.after" @click="previewImage(step.screenshots.after)" />
                      <!-- AI 识别标注 -->
                      <div 
                        v-if="step.aiResult?.element" 
                        class="ai-marker"
                        :style="{
                          left: step.aiResult.element.x + 'px',
                          top: step.aiResult.element.y + 'px',
                          width: step.aiResult.element.width + 'px',
                          height: step.aiResult.element.height + 'px'
                        }"
                      >
                        <div class="marker-label">{{ step.aiResult.element.label }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- AI 分析结果 -->
              <div v-if="step.aiResult" class="ai-result">
                <div class="result-header">
                  <el-icon><MagicStick /></el-icon>
                  <span>AI 分析结果</span>
                </div>
                <div class="result-content">
                  <div v-if="step.aiResult.thinking" class="thinking">
                    <strong>思考过程:</strong> {{ step.aiResult.thinking }}
                  </div>
                  <div v-if="step.aiResult.action" class="action">
                    <strong>执行动作:</strong> {{ step.aiResult.action }}
                  </div>
                  <div v-if="step.aiResult.confidence" class="confidence">
                    <strong>置信度:</strong> 
                    <el-progress 
                      :percentage="step.aiResult.confidence * 100" 
                      :stroke-width="6"
                      style="width: 200px; display: inline-flex;"
                    />
                  </div>
                </div>
              </div>
              
              <!-- 错误信息 -->
              <div v-if="step.error" class="error-section">
                <div class="error-header">
                  <el-icon><WarningFilled /></el-icon>
                  <span>错误信息</span>
                </div>
                <div class="error-content">
                  <pre>{{ step.error }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 图片预览 -->
    <el-image-viewer
      v-if="previewVisible"
      :url-list="[previewUrl]"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, Download, RefreshRight, Calendar, Timer, Iphone,
  Check, Close, Clock, MagicStick, WarningFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const stepFilter = ref('all')
const previewVisible = ref(false)
const previewUrl = ref('')

// 模拟报告数据
const report = reactive({
  id: route.params.id,
  caseName: '登录功能测试',
  status: 'passed',
  startTime: '2026-01-17T10:30:00',
  duration: '2m 15s',
  device: {
    name: 'OnePlus NE2210',
    platform: 'android',
    version: '15'
  },
  totalSteps: 8,
  passedSteps: 7,
  failedSteps: 1,
  skippedSteps: 0,
  passRate: 87.5,
  steps: [
    {
      type: 'launch',
      status: 'passed',
      duration: 2500,
      package: 'com.example.app',
      screenshots: {
        after: '/static/screenshots/step1.png'
      }
    },
    {
      type: 'aiTap',
      status: 'passed',
      duration: 1200,
      prompt: '点击登录按钮',
      x: 540,
      y: 1200,
      screenshots: {
        before: '/static/screenshots/step2_before.png',
        after: '/static/screenshots/step2_after.png'
      },
      aiResult: {
        thinking: '识别到页面上有一个蓝色的"登录"按钮，位于屏幕中下方',
        action: 'tap(540, 1200)',
        confidence: 0.95,
        element: {
          label: '登录按钮',
          x: 100,
          y: 180,
          width: 200,
          height: 48
        }
      }
    },
    {
      type: 'aiInput',
      status: 'passed',
      duration: 800,
      prompt: '在用户名输入框中输入',
      text: '13800138000',
      screenshots: {
        after: '/static/screenshots/step3.png'
      },
      aiResult: {
        thinking: '找到标签为"用户名"的输入框',
        action: 'input("13800138000")',
        confidence: 0.92
      }
    },
    {
      type: 'aiInput',
      status: 'passed',
      duration: 750,
      prompt: '在密码输入框中输入',
      text: '******',
      screenshots: {
        after: '/static/screenshots/step4.png'
      }
    },
    {
      type: 'aiTap',
      status: 'passed',
      duration: 1100,
      prompt: '点击确认登录',
      x: 540,
      y: 1400,
      screenshots: {
        after: '/static/screenshots/step5.png'
      }
    },
    {
      type: 'sleep',
      status: 'passed',
      duration: 3000
    },
    {
      type: 'aiAssert',
      status: 'passed',
      duration: 1500,
      prompt: '验证页面显示"欢迎回来"',
      screenshots: {
        after: '/static/screenshots/step7.png'
      },
      aiResult: {
        thinking: '在页面顶部找到文字"欢迎回来，用户"',
        action: 'assert(true)',
        confidence: 0.98
      }
    },
    {
      type: 'screenshot',
      status: 'passed',
      duration: 500,
      description: '登录成功截图',
      screenshots: {
        after: '/static/screenshots/step8.png'
      }
    }
  ]
})

const filteredSteps = computed(() => {
  if (stepFilter.value === 'all') return report.steps
  return report.steps.filter(s => s.status === stepFilter.value)
})

const stepTypeLabels = {
  tap: '点击',
  swipe: '滑动',
  input: '输入',
  back: '返回',
  home: 'Home',
  sleep: '等待',
  launch: '启动应用',
  screenshot: '截图',
  aiTap: 'AI 点击',
  aiInput: 'AI 输入',
  aiAssert: 'AI 断言',
  aiQuery: 'AI 查询'
}

function getStepTypeLabel(type) {
  return stepTypeLabels[type] || type
}

function getStatusType(status) {
  const map = {
    passed: 'success',
    failed: 'danger',
    skipped: 'warning',
    running: 'primary'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    passed: '通过',
    failed: '失败',
    skipped: '跳过',
    running: '运行中'
  }
  return map[status] || status
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

function goBack() {
  router.push('/ui/executions')
}

function downloadReport() {
  ElMessage.info('功能开发中')
}

function rerunCase() {
  ElMessage.info('功能开发中')
}

function previewImage(url) {
  previewUrl.value = url
  previewVisible.value = true
}

onMounted(() => {
  // 加载报告数据
  // loadReport()
})
</script>

<style lang="scss" scoped>
.report-page {
  max-width: 1200px;
  margin: 0 auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }
  
  .report-title {
    h1 {
      font-size: 24px;
      font-weight: 600;
      margin: 0 0 8px 0;
    }
    
    .report-meta {
      display: flex;
      align-items: center;
      gap: 16px;
      color: var(--text-muted);
      font-size: 14px;
      
      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.report-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
  text-align: center;
  
  .summary-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary);
  }
  
  .summary-label {
    font-size: 14px;
    color: var(--text-muted);
    margin-top: 4px;
  }
  
  &.success .summary-value { color: var(--success-color); }
  &.danger .summary-value { color: var(--danger-color); }
  &.warning .summary-value { color: var(--warning-color); }
  &.info .summary-value { color: var(--primary-color); }
}

.steps-timeline {
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 24px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h2 {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
  }
}

.timeline-content {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  
  &:last-child {
    margin-bottom: 0;
    
    .timeline-line::after {
      display: none;
    }
  }
}

.timeline-line {
  position: relative;
  width: 32px;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  
  &::after {
    content: '';
    position: absolute;
    top: 32px;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: calc(100% + 24px);
    background: var(--border-color);
  }
}

.timeline-dot {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  position: relative;
  z-index: 1;
  
  &.passed { background: var(--success-color); }
  &.failed { background: var(--danger-color); }
  &.skipped { background: var(--warning-color); }
  &.running { background: var(--primary-color); }
}

.timeline-card {
  flex: 1;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #fff;
    border-bottom: 1px solid var(--border-color);
    
    .step-info {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .step-number {
        font-weight: 600;
        color: var(--text-primary);
      }
      
      .step-type {
        color: var(--text-secondary);
      }
    }
    
    .step-time {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--text-muted);
      font-size: 13px;
    }
  }
  
  .card-body {
    padding: 16px;
  }
}

.step-prompt {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(24, 144, 255, 0.06);
  border-radius: 6px;
  margin-bottom: 12px;
  
  .el-icon {
    color: var(--primary-color);
  }
  
  span {
    color: var(--text-primary);
  }
}

.step-detail {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.screenshots-section {
  margin-top: 16px;
}

.screenshots-row {
  display: flex;
  gap: 16px;
}

.screenshot-item {
  flex: 1;
  
  .screenshot-label {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  
  .screenshot-wrapper {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    background: #f5f5f5;
    
    img {
      width: 100%;
      height: auto;
      display: block;
      cursor: pointer;
      transition: transform 0.2s;
      
      &:hover {
        transform: scale(1.02);
      }
    }
  }
}

.ai-marker {
  position: absolute;
  border: 2px solid var(--success-color);
  background: rgba(82, 196, 26, 0.1);
  border-radius: 4px;
  pointer-events: none;
  
  .marker-label {
    position: absolute;
    top: -24px;
    left: 0;
    background: var(--success-color);
    color: #fff;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    white-space: nowrap;
  }
}

.ai-result {
  margin-top: 16px;
  padding: 12px;
  background: rgba(102, 126, 234, 0.06);
  border-radius: 6px;
  
  .result-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    color: #667eea;
    font-weight: 600;
  }
  
  .result-content {
    font-size: 13px;
    color: var(--text-secondary);
    
    > div {
      margin-bottom: 8px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
    
    strong {
      color: var(--text-primary);
    }
  }
}

.error-section {
  margin-top: 16px;
  padding: 12px;
  background: rgba(255, 77, 79, 0.06);
  border-radius: 6px;
  border: 1px solid rgba(255, 77, 79, 0.2);
  
  .error-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    color: var(--danger-color);
    font-weight: 600;
  }
  
  .error-content {
    pre {
      margin: 0;
      font-family: 'Fira Code', monospace;
      font-size: 12px;
      color: var(--danger-color);
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}

@media (max-width: 768px) {
  .report-summary {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .screenshots-row {
    flex-direction: column;
  }
}
</style>






