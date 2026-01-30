<template>
  <div class="usage-page">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>LLM Usage</h1>
        <el-select v-model="timeRange" @change="loadData" style="width: 140px">
          <el-option label="最近24小时" :value="24" />
          <el-option label="最近7天" :value="168" />
          <el-option label="最近30天" :value="720" />
        </el-select>
      </div>
      <div class="header-stats">
        <div class="stat-card">
          <span class="value">{{ stats.total.requests }}</span>
          <span class="label">REQUESTS</span>
        </div>
        <div class="stat-card">
          <span class="value">{{ formatTokens(stats.total.tokens) }}</span>
          <span class="label">TOKENS</span>
        </div>
        <div class="stat-card">
          <span class="value">{{ stats.providers_count }}</span>
          <span class="label">PROVIDERS</span>
        </div>
      </div>
      <div class="header-actions">
        <el-input v-model="searchKeyword" placeholder="搜索模型..." style="width: 160px" clearable>
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row" v-loading="loading">
      <!-- 请求趋势 -->
      <div class="chart-card">
        <div class="chart-title">请求量趋势</div>
        <div class="chart-container" ref="trendChartRef"></div>
      </div>
      
      <!-- Token 消耗饼图 -->
      <div class="chart-card">
        <div class="chart-title">Token 消耗</div>
        <div class="chart-container" ref="tokenPieRef"></div>
      </div>
      
      <!-- Token 用量趋势 -->
      <div class="chart-card">
        <div class="chart-title">Token 用量趋势</div>
        <div class="chart-tabs">
          <button :class="{ active: chartTab === 'model' }" @click="chartTab = 'model'">按模型</button>
          <button :class="{ active: chartTab === 'provider' }" @click="chartTab = 'provider'">按供应商</button>
        </div>
        <div class="chart-container" ref="tokenTrendRef"></div>
      </div>
    </div>

    <!-- 供应商列表 -->
    <div class="providers-list">
      <div 
        v-for="provider in stats.by_provider" 
        :key="provider.provider_id"
        class="provider-row"
        @click="$router.push('/llm/providers')"
      >
        <div class="provider-icon">
          <el-icon :size="24"><Cpu /></el-icon>
        </div>
        <div class="provider-info">
          <div class="name">{{ provider.provider_name }}</div>
          <div class="code">{{ provider.provider_code }}</div>
        </div>
        <div class="provider-stats">
          <div class="stat">
            <span class="value">{{ provider.requests }}</span>
            <span class="label">请求数</span>
          </div>
          <div class="stat">
            <span class="value">{{ formatTokens(provider.tokens) }}</span>
            <span class="label">Tokens</span>
          </div>
          <div class="stat">
            <span class="value" :class="provider.success_rate >= 90 ? 'success' : 'warning'">
              {{ provider.success_rate }}% 成功率
            </span>
          </div>
          <div class="stat">
            <span class="value">{{ provider.avg_latency_ms }}ms</span>
            <span class="label">延迟</span>
          </div>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
      
      <div v-if="stats.by_provider?.length === 0" class="empty-state">
        <el-icon :size="48"><DataLine /></el-icon>
        <p>暂无数据</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { Refresh, Search, Cpu, ArrowRight, DataLine } from '@element-plus/icons-vue'
import { llmApi } from '@/api'
import * as echarts from 'echarts'

const loading = ref(false)
const timeRange = ref(24)
const searchKeyword = ref('')
const chartTab = ref('model')

const stats = ref({
  total: { requests: 0, tokens: 0 },
  by_provider: [],
  providers_count: 0
})

const trend = ref([])
const tokenByModel = ref([])

const trendChartRef = ref(null)
const tokenPieRef = ref(null)
const tokenTrendRef = ref(null)

let trendChart = null
let pieChart = null
let tokenTrendChart = null

async function loadData() {
  loading.value = true
  try {
    const [statsRes, trendRes, modelRes] = await Promise.all([
      llmApi.getUsageStats(timeRange.value),
      llmApi.getUsageTrend(timeRange.value, timeRange.value > 24 ? 'day' : 'hour'),
      llmApi.getUsageByModel(timeRange.value)
    ])
    
    stats.value = statsRes.data
    trend.value = trendRes.data.data || []
    tokenByModel.value = modelRes.data.data || []
    
    await nextTick()
    renderCharts()
  } catch (e) {
    console.error('加载数据失败:', e)
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  // 趋势图
  if (trendChartRef.value) {
    if (!trendChart) {
      trendChart = echarts.init(trendChartRef.value)
    }
    trendChart.setOption({
      grid: { top: 20, right: 20, bottom: 30, left: 50 },
      xAxis: {
        type: 'category',
        data: trend.value.map(d => d.time.split(' ')[1] || d.time),
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b', fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#64748b', fontSize: 11 },
        splitLine: { lineStyle: { color: '#f1f5f9' } }
      },
      series: [{
        type: 'line',
        data: trend.value.map(d => d.requests),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#3b82f6', width: 2 },
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ])
        }
      }],
      tooltip: { trigger: 'axis' }
    })
  }
  
  // Token 饼图
  if (tokenPieRef.value) {
    if (!pieChart) {
      pieChart = echarts.init(tokenPieRef.value)
    }
    const pieData = tokenByModel.value.slice(0, 6).map(d => ({
      name: d.model_name,
      value: d.tokens
    }))
    
    pieChart.setOption({
      color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
      series: [{
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['35%', '50%'],
        data: pieData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        }
      }],
      legend: {
        orient: 'vertical',
        right: 20,
        top: 'center',
        textStyle: { color: '#64748b', fontSize: 12 },
        formatter: name => {
          const item = pieData.find(d => d.name === name)
          return `${name}`
        }
      },
      tooltip: {
        formatter: p => `${p.name}: ${formatTokens(p.value)} tokens`
      }
    })
  }
  
  // Token 趋势图
  if (tokenTrendRef.value) {
    if (!tokenTrendChart) {
      tokenTrendChart = echarts.init(tokenTrendRef.value)
    }
    
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
    const series = stats.value.by_provider?.slice(0, 5).map((p, i) => ({
      name: p.provider_name,
      type: 'bar',
      stack: 'total',
      data: [p.tokens],
      itemStyle: { color: colors[i] }
    })) || []
    
    tokenTrendChart.setOption({
      grid: { top: 40, right: 20, bottom: 30, left: 50 },
      xAxis: { type: 'category', data: ['Token用量'] },
      yAxis: { type: 'value' },
      series,
      legend: {
        top: 5,
        textStyle: { fontSize: 11 }
      },
      tooltip: { trigger: 'axis' }
    })
  }
}

function formatTokens(num) {
  if (!num) return '0'
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

watch(chartTab, () => {
  nextTick(() => renderCharts())
})

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.usage-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 700;
      color: #1e293b;
    }
  }
  
  .header-stats {
    display: flex;
    gap: 40px;
    
    .stat-card {
      text-align: center;
      
      .value {
        display: block;
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
      }
      
      .label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 500;
        letter-spacing: 1px;
      }
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  
  .chart-title {
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 16px;
  }
  
  .chart-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    
    button {
      padding: 4px 12px;
      border: none;
      background: #f1f5f9;
      color: #64748b;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      
      &.active {
        background: #3b82f6;
        color: white;
      }
    }
  }
  
  .chart-container {
    height: 200px;
  }
}

.providers-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 16px;
}

.provider-row {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .provider-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }
  
  .provider-info {
    min-width: 100px;
    
    .name {
      font-weight: 600;
      color: #1e293b;
    }
    
    .code {
      font-size: 12px;
      color: #94a3b8;
    }
  }
  
  .provider-stats {
    flex: 1;
    display: flex;
    gap: 24px;
    
    .stat {
      .value {
        font-size: 15px;
        font-weight: 600;
        color: #1e293b;
        
        &.success { color: #10b981; }
        &.warning { color: #f59e0b; }
      }
      
      .label {
        display: block;
        font-size: 11px;
        color: #94a3b8;
      }
    }
  }
  
  .arrow {
    color: #cbd5e1;
  }
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px;
  color: #94a3b8;
  
  p {
    margin-top: 12px;
  }
}
</style>
