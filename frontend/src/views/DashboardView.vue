<template>
  <div class="dashboard">
    <!-- 用户欢迎区 -->
    <div class="welcome-section">
      <div class="welcome-card">
        <div class="user-profile">
          <el-avatar :size="64" class="profile-avatar">
            <span>QA</span>
          </el-avatar>
          <div class="profile-info">
            <h2>测试工程师 <el-tag size="small" type="primary">管理员</el-tag></h2>
            <p>登录时间: {{ loginTime }}</p>
            <p>访问IP: 127.0.0.1</p>
          </div>
        </div>
        
        <div class="quick-stats">
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalCases }}</div>
            <div class="stat-change up">
              <el-icon><Top /></el-icon> {{ stats.casesChange }}
            </div>
            <div class="stat-label">功能用例数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalApis }}</div>
            <div class="stat-change up">
              <el-icon><Top /></el-icon> {{ stats.apisChange }}
            </div>
            <div class="stat-label">接口数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalScenarios }}</div>
            <div class="stat-change up">
              <el-icon><Top /></el-icon> {{ stats.scenariosChange }}
            </div>
            <div class="stat-label">接口用例数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalUiCases }}</div>
            <div class="stat-change up">
              <el-icon><Top /></el-icon> {{ stats.uiCasesChange }}
            </div>
            <div class="stat-label">UI用例数量</div>
          </div>
        </div>
        
        <div class="quick-guide">
          <el-button type="primary" text>
            快来了解平台使用方法吧 🚀
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 常用工具区 -->
    <div class="tools-section">
      <div class="section-title">
        <el-icon><Grid /></el-icon>
        <span>常用工具</span>
      </div>
      <div class="tools-grid">
        <div 
          v-for="tool in quickTools" 
          :key="tool.name"
          class="tool-item"
          @click="handleToolClick(tool)"
        >
          <div class="tool-icon" :style="{ background: tool.bg }">
            <el-icon :size="20"><component :is="tool.icon" /></el-icon>
          </div>
          <div class="tool-info">
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-desc">{{ tool.desc }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据统计区 -->
    <div class="stats-section">
      <!-- UI 自动化统计 -->
      <div class="stat-card">
        <div class="card-header">
          <span class="card-title">UI自动化</span>
          <el-button type="primary" link size="small" @click="$router.push('/ui/executions')">
            查看详情
          </el-button>
        </div>
        <div class="card-content">
          <div class="big-stats">
            <div class="big-stat">
              <div class="big-value">{{ uiStats.total }}</div>
              <div class="big-label">用例总数</div>
            </div>
            <div class="big-stat success">
              <div class="big-value">{{ uiStats.passRate }}%</div>
              <div class="big-label">通过率</div>
            </div>
          </div>
          <div class="mini-stats">
            <div class="mini-item">
              <span class="label">启用:</span>
              <span class="value success">{{ uiStats.enabled }}</span>
            </div>
            <div class="mini-item">
              <span class="label">禁用:</span>
              <span class="value danger">{{ uiStats.disabled }}</span>
            </div>
            <div class="mini-item">
              <span class="label">今日执行:</span>
              <span class="value">{{ uiStats.todayRuns }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 接口自动化统计 -->
      <div class="stat-card">
        <div class="card-header">
          <span class="card-title">APIs</span>
          <el-tag size="small" type="success">API Status</el-tag>
        </div>
        <div class="card-content">
          <div class="big-stats">
            <div class="big-stat">
              <div class="big-value">{{ apiStats.coverage }}%</div>
              <div class="big-label">API测试覆盖</div>
            </div>
            <div class="big-stat success">
              <div class="big-value">{{ apiStats.passRate }}%</div>
              <div class="big-label">用例通过率</div>
            </div>
          </div>
          <div class="mini-stats">
            <div class="mini-item">
              <span class="label">API总数:</span>
              <span class="value">{{ apiStats.total }}</span>
            </div>
            <div class="mini-item">
              <span class="label">场景用例:</span>
              <span class="value">{{ apiStats.scenarios }}</span>
            </div>
          </div>
          <div class="api-types">
            <el-tag size="small" type="success">RestAPI: {{ apiStats.rest }}</el-tag>
            <el-tag size="small" type="warning">OpenAPI: {{ apiStats.openapi }}</el-tag>
            <el-tag size="small" type="info">Dubbo: {{ apiStats.dubbo }}</el-tag>
          </div>
        </div>
      </div>
      
      <!-- 设备状态 -->
      <div class="stat-card">
        <div class="card-header">
          <span class="card-title">设备状态</span>
          <el-button type="primary" link size="small" @click="$router.push('/ui/devices')">
            管理设备
          </el-button>
        </div>
        <div class="card-content">
          <div class="device-stats">
            <div class="device-ring">
              <div ref="deviceChartRef" style="width: 120px; height: 120px;"></div>
            </div>
            <div class="device-list">
              <div class="device-item">
                <span class="dot online"></span>
                <span class="name">在线</span>
                <span class="count">{{ deviceStats.online }}</span>
              </div>
              <div class="device-item">
                <span class="dot offline"></span>
                <span class="name">离线</span>
                <span class="count">{{ deviceStats.offline }}</span>
              </div>
              <div class="device-item">
                <span class="dot busy"></span>
                <span class="name">使用中</span>
                <span class="count">{{ deviceStats.busy }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 执行任务统计 -->
      <div class="stat-card">
        <div class="card-header">
          <span class="card-title">执行任务</span>
          <el-tag size="small">今日</el-tag>
        </div>
        <div class="card-content">
          <div class="big-stats">
            <div class="big-stat success">
              <div class="big-value">{{ taskStats.successRate }}%</div>
              <div class="big-label">任务成功率</div>
            </div>
          </div>
          <div class="task-counts">
            <div class="task-item">
              <el-icon class="success"><CircleCheck /></el-icon>
              <span>成功: {{ taskStats.success }}</span>
            </div>
            <div class="task-item">
              <el-icon class="danger"><CircleClose /></el-icon>
              <span>失败: {{ taskStats.failed }}</span>
            </div>
            <div class="task-item">
              <el-icon class="warning"><Clock /></el-icon>
              <span>队列中: {{ taskStats.pending }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 图表区 -->
    <div class="charts-section">
      <!-- 执行趋势 -->
      <div class="chart-card">
        <div class="card-header">
          <span class="card-title">近7日执行趋势</span>
          <el-radio-group v-model="trendType" size="small">
            <el-radio-button label="ui">UI</el-radio-button>
            <el-radio-button label="api">接口</el-radio-button>
          </el-radio-group>
        </div>
        <div class="card-content">
          <div ref="trendChartRef" style="width: 100%; height: 280px;"></div>
        </div>
      </div>
      
      <!-- 用例状态分布 -->
      <div class="chart-card">
        <div class="card-header">
          <span class="card-title">用例状态分布</span>
        </div>
        <div class="card-content">
          <div ref="statusChartRef" style="width: 100%; height: 280px;"></div>
        </div>
      </div>
    </div>
    
    <!-- 最近执行记录 -->
    <div class="recent-section">
      <div class="section-card">
        <div class="card-header">
          <span class="card-title">最近执行记录</span>
          <el-button type="primary" link size="small" @click="$router.push('/ui/executions')">
            查看全部
          </el-button>
        </div>
        <div class="card-content">
          <el-table :data="recentExecutions" style="width: 100%" size="small">
            <el-table-column prop="id" label="执行ID" width="100" />
            <el-table-column prop="name" label="用例名称" min-width="200" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.type === 'UI' ? 'primary' : 'success'">
                  {{ row.type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="getStatusType(row.status)">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="耗时" width="100" />
            <el-table-column prop="executor" label="执行人" width="100" />
            <el-table-column prop="time" label="执行时间" width="180" />
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="viewReport(row)">
                  查看报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { 
  Top, Grid, Iphone, Connection, Box, DataLine, 
  CircleCheck, CircleClose, Clock, Document, Setting, Tools,
  MagicStick, VideoPlay, Edit
} from '@element-plus/icons-vue'

const router = useRouter()

// 登录时间
const loginTime = ref(new Date().toLocaleString('zh-CN'))

// 统计数据
const stats = reactive({
  totalCases: 156,
  casesChange: 12,
  totalApis: 89,
  apisChange: 5,
  totalScenarios: 234,
  scenariosChange: 18,
  totalUiCases: 45,
  uiCasesChange: 3
})

// UI 自动化统计
const uiStats = reactive({
  total: 45,
  passRate: 92.5,
  enabled: 42,
  disabled: 3,
  todayRuns: 15
})

// API 统计
const apiStats = reactive({
  coverage: 78.5,
  passRate: 95.2,
  total: 89,
  scenarios: 156,
  rest: 45,
  openapi: 32,
  dubbo: 12
})

// 设备统计
const deviceStats = reactive({
  online: 3,
  offline: 1,
  busy: 1
})

// 任务统计
const taskStats = reactive({
  successRate: 94.5,
  success: 28,
  failed: 2,
  pending: 3
})

// 快捷工具
const quickTools = [
  { name: 'AI用例生成', desc: 'AI智能生成测试用例', icon: MagicStick, bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', route: '/ui/cases/new' },
  { name: '实时投屏', desc: '设备实时投屏控制', icon: Iphone, bg: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', route: '/ui/mirror' },
  { name: '接口调试', desc: '在线接口测试调试', icon: Connection, bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', route: '/api/debug' },
  { name: '执行报告', desc: '查看执行报告', icon: Document, bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', route: '/ui/executions' },
  { name: '数据工厂', desc: '测试数据生成管理', icon: Box, bg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', route: '/data-factory' },
  { name: '系统设置', desc: 'AI配置与系统设置', icon: Setting, bg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', route: '/settings' },
]

// 最近执行记录
const recentExecutions = ref([
  { id: 'E001', name: '登录功能测试', type: 'UI', status: '通过', duration: '2m 15s', executor: 'QA', time: '2026-01-17 10:30:00' },
  { id: 'E002', name: '用户注册接口', type: 'API', status: '通过', duration: '1.2s', executor: 'QA', time: '2026-01-17 10:25:00' },
  { id: 'E003', name: '商品列表加载', type: 'UI', status: '失败', duration: '3m 45s', executor: 'QA', time: '2026-01-17 10:20:00' },
  { id: 'E004', name: '支付流程测试', type: 'UI', status: '通过', duration: '5m 30s', executor: 'QA', time: '2026-01-17 10:15:00' },
  { id: 'E005', name: '订单查询接口', type: 'API', status: '通过', duration: '0.8s', executor: 'QA', time: '2026-01-17 10:10:00' },
])

// 趋势类型
const trendType = ref('ui')

// 图表引用
const deviceChartRef = ref(null)
const trendChartRef = ref(null)
const statusChartRef = ref(null)

let deviceChart = null
let trendChart = null
let statusChart = null

function getStatusType(status) {
  const map = {
    '通过': 'success',
    '失败': 'danger',
    '运行中': 'warning',
    '待执行': 'info'
  }
  return map[status] || 'info'
}

function handleToolClick(tool) {
  router.push(tool.route)
}

function viewReport(row) {
  router.push(`/ui/report/${row.id}`)
}

function initCharts() {
  // 设备状态饼图
  if (deviceChartRef.value) {
    deviceChart = echarts.init(deviceChartRef.value)
    deviceChart.setOption({
      series: [{
        type: 'pie',
        radius: ['60%', '80%'],
        avoidLabelOverlap: false,
        label: { show: false },
        data: [
          { value: deviceStats.online, name: '在线', itemStyle: { color: '#52c41a' } },
          { value: deviceStats.offline, name: '离线', itemStyle: { color: '#d9d9d9' } },
          { value: deviceStats.busy, name: '使用中', itemStyle: { color: '#1890ff' } },
        ]
      }]
    })
  }
  
  // 执行趋势图
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['通过', '失败'], top: 0 },
      grid: { left: 40, right: 20, top: 40, bottom: 30 },
      xAxis: {
        type: 'category',
        data: ['01-11', '01-12', '01-13', '01-14', '01-15', '01-16', '01-17'],
        axisLine: { lineStyle: { color: '#e4e7ed' } },
        axisLabel: { color: '#909399' }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#e4e7ed', type: 'dashed' } },
        axisLabel: { color: '#909399' }
      },
      series: [
        {
          name: '通过',
          type: 'line',
          smooth: true,
          data: [12, 15, 18, 14, 20, 22, 19],
          itemStyle: { color: '#52c41a' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
              { offset: 1, color: 'rgba(82, 196, 26, 0)' }
            ])
          }
        },
        {
          name: '失败',
          type: 'line',
          smooth: true,
          data: [2, 1, 3, 1, 2, 1, 2],
          itemStyle: { color: '#ff4d4f' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(255, 77, 79, 0.3)' },
              { offset: 1, color: 'rgba(255, 77, 79, 0)' }
            ])
          }
        }
      ]
    })
  }
  
  // 用例状态饼图
  if (statusChartRef.value) {
    statusChart = echarts.init(statusChartRef.value)
    statusChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 20, top: 'center' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        data: [
          { value: 85, name: '通过', itemStyle: { color: '#52c41a' } },
          { value: 8, name: '失败', itemStyle: { color: '#ff4d4f' } },
          { value: 5, name: '跳过', itemStyle: { color: '#faad14' } },
          { value: 2, name: '未执行', itemStyle: { color: '#d9d9d9' } },
        ]
      }]
    })
  }
}

function handleResize() {
  deviceChart?.resize()
  trendChart?.resize()
  statusChart?.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  deviceChart?.dispose()
  trendChart?.dispose()
  statusChart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
}

// 欢迎区
.welcome-section {
  margin-bottom: 20px;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .profile-avatar {
    background: rgba(255, 255, 255, 0.2);
    font-size: 24px;
    font-weight: 600;
  }
  
  .profile-info {
    h2 {
      font-size: 18px;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-tag {
        background: rgba(255, 255, 255, 0.2);
        border: none;
        color: #fff;
      }
    }
    
    p {
      font-size: 13px;
      opacity: 0.85;
      margin: 4px 0;
    }
  }
}

.quick-stats {
  display: flex;
  gap: 40px;
  
  .stat-item {
    text-align: center;
    
    .stat-value {
      font-size: 32px;
      font-weight: 700;
    }
    
    .stat-change {
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2px;
      margin: 4px 0;
      
      &.up {
        color: #a3e635;
      }
      
      &.down {
        color: #fca5a5;
      }
    }
    
    .stat-label {
      font-size: 13px;
      opacity: 0.85;
    }
  }
}

.quick-guide {
  .el-button {
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
  }
}

// 工具区
.tools-section {
  margin-bottom: 20px;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
  }
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.tool-item {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  
  .tool-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
  }
  
  .tool-info {
    .tool-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .tool-desc {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }
  }
}

// 统计卡片区
.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--border-color);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .big-stats {
    display: flex;
    gap: 24px;
    margin-bottom: 16px;
    
    .big-stat {
      .big-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
      }
      
      .big-label {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 4px;
      }
      
      &.success .big-value {
        color: var(--success-color);
      }
    }
  }
  
  .mini-stats {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    
    .mini-item {
      font-size: 13px;
      
      .label {
        color: var(--text-muted);
      }
      
      .value {
        font-weight: 600;
        margin-left: 4px;
        
        &.success { color: var(--success-color); }
        &.danger { color: var(--danger-color); }
      }
    }
  }
  
  .api-types {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }
}

.device-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  
  .device-list {
    flex: 1;
    
    .device-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
      font-size: 13px;
      
      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        
        &.online { background: var(--success-color); }
        &.offline { background: #d9d9d9; }
        &.busy { background: var(--primary-color); }
      }
      
      .name {
        color: var(--text-secondary);
      }
      
      .count {
        margin-left: auto;
        font-weight: 600;
      }
    }
  }
}

.task-counts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
  
  .task-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    
    .el-icon {
      font-size: 16px;
      
      &.success { color: var(--success-color); }
      &.danger { color: var(--danger-color); }
      &.warning { color: var(--warning-color); }
    }
  }
}

// 图表区
.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-card {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--border-color);
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
}

// 最近执行区
.recent-section {
  .section-card {
    background: var(--card-bg);
    border-radius: 8px;
    padding: 20px;
    border: 1px solid var(--border-color);
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      .card-title {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }
  }
}

// 响应式
@media (max-width: 1200px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .quick-stats {
    gap: 24px;
    
    .stat-item .stat-value {
      font-size: 24px;
    }
  }
}

@media (max-width: 768px) {
  .welcome-card {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .stats-section {
    grid-template-columns: 1fr;
  }
  
  .tools-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>






