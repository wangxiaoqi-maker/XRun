<template>
  <div class="editor-page">
    <!-- 顶部工具栏 -->
    <!-- 顶部工具栏 - 新的整合布局 -->
    <div class="editor-header">
      <!-- 左侧：设备状态栏 (与下方设备面板对齐) -->
      <div class="header-device-portion">
        <template v-if="mirrorRef?.selectedDevice">
          <div class="device-info-group">
             <span class="device-name-title">{{ mirrorRef?.selectedDevice?.name || mirrorRef?.selectedDevice?.model }}</span>
             <span class="fps-tag" v-if="mirrorRef?.fps > 0">{{ mirrorRef?.fps }} FPS</span>
          </div>
          
          <div class="device-ctrl-group">
             <span class="mode-box">{{ mirrorRef?.screenMode?.toUpperCase() || 'SCRCPY' }}</span>
             <el-button link type="primary" size="small" @click="mirrorRef?.toggleScreenMode">切换</el-button>
             <el-button link type="danger" size="small" @click="mirrorRef?.disconnect">断开</el-button>
          </div>
        </template>
        <template v-else>
           <div class="device-status-dot disconnected"></div>
           <span class="device-name-title text-gray">未连接设备</span>
        </template>
      </div>

      <!-- 右侧：脚本信息与操作 -->
      <div class="header-script-portion">
        <div class="script-meta">
           <div class="script-icon-box">
             <el-icon><Document /></el-icon>
           </div>
           <div class="script-text-group">
             <span class="script-title">{{ scriptName }}</span>
             <span class="script-subtitle">Last edited just now</span>
           </div>
        </div>

        <div class="header-actions">
          <el-button @click="saveScript" class="header-btn" plain size="default">保存</el-button>
          <el-button type="primary" @click="runScript" :loading="isRunning" class="header-btn run-btn" size="default">
            <el-icon v-if="!isRunning" class="el-icon--left"><VideoPlay /></el-icon>
            {{ isRunning ? 'Running...' : 'Run' }}
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 主体内容 -->
    <div class="editor-body">
      <!-- 左侧：设备投屏 (移除背景，纯净展示) -->
      <div class="device-panel">
        <DeviceMirror 
          ref="mirrorRef"
          :recording="isRecording"
          :hide-header="true"
          @action-recorded="onActionRecorded"
          @device-connected="onDeviceConnected"
        />
        <!-- 移除原来底部的 device-controls -->
      </div>
      
      <!-- 右侧：步骤编辑器 -->
      <div class="steps-panel">
        <div class="steps-container">
          <div class="steps-wrapper">
            
            <draggable 
              v-model="steps" 
              item-key="id"
              handle=".step-index" 
              animation="200"
              class="steps-list-area"
              ghost-class="ghost-card"
            >
              <template #item="{ element: step, index }">
                <div 
                  class="step-row"
                  :class="[
                    { active: activeIndex === index },
                    step.status === 'running' ? 'status-running' : '',
                    step.status === 'success' ? 'status-success' : ''
                  ]"
                  @click="activeIndex = index"
                >
                  <!-- Left Colored Strip -->
                  <div class="status-strip" v-if="['running', 'success'].includes(step.status)"></div>

                  <!-- 1. Index (Drag Handle) -->
                  <div class="step-index">{{ (index + 1).toString().padStart(2, '0') }}</div>
                  
                  <!-- 2. Action Tag -->
                  <div class="step-tag">
                    <span class="tag-badge" :class="step.action">{{ step.actionLabel }}</span>
                  </div>
                  
                  <!-- 3. Content -->
                  <div class="step-content">
                    <!-- Target (Bold) -->
                    <span class="target-text" v-if="step.target">{{ step.target }}</span>
                    
                    <!-- Value (Gray pill) -->
                    <span class="value-pill" v-if="step.value">{{ step.value }}</span>
                    
                     <!-- Scheme URL display -->
                    <span class="value-pill" v-if="['schemeUrl', 'schemeRouter'].includes(step.action) && step.url">
                       {{ step.url }}
                    </span>
                    
                     <el-icon class="config-icon" @click.stop="editStep(index)"><Setting /></el-icon>
                  </div>
                  
                  <!-- 4. Status (Right side) -->
                  <div class="step-status-area">
                    <!-- Running -->
                    <div v-if="step.status === 'running'" class="status-box running">
                        <span>执行中</span>
                        <div class="spinner-ring"></div>
                    </div>
                    
                    <!-- Success -->
                    <div v-else-if="step.status === 'success'" class="status-box success">
                        <span class="duration-text">{{ formatDuration(step.duration) }}</span>
                        <div class="check-circle"><el-icon><Check /></el-icon></div>
                    </div>
                    
                    <!-- Pending -->
                    <div v-else class="status-box pending">
                        <span>等待执行</span>
                    </div>
                    
                    <!-- Hover Actions -->
                    <div class="hover-actions">
                        <el-button type="danger" link @click.stop="deleteStep(index)">
                            <el-icon><Delete /></el-icon>
                        </el-button>
                    </div>
                  </div>
                </div>
              </template>
            </draggable>
            
            <!-- Inline Add Form Area -->
            <div class="add-step-wrapper">
              <!-- Trigger Button -->
              <div 
                v-if="!showInlineAdd" 
                class="add-trigger-btn" 
                @click="toggleInlineAdd"
              >
                <el-icon class="icon-plus"><Plus /></el-icon>
                <span class="placeholder-text">添加步骤...</span>
              </div>
              
              <!-- Inline Form -->
              <div v-else class="inline-add-form">
                <div class="form-row">
                  <div class="form-item" style="flex: 0 0 140px;">
                    <el-select v-model="inlineForm.action" placeholder="操作类型" @change="onActionChange">
                       <el-option 
                        v-for="opt in actionOptions" 
                        :key="opt.action"
                        :label="opt.value"
                        :value="opt.action"
                      />
                    </el-select>
                  </div>
                  
                  <template v-if="['schemeUrl', 'schemeRouter'].includes(inlineForm.action)">
                      <div class="form-item" style="flex: 1">
                        <el-input 
                            v-model="inlineForm.url" 
                            :placeholder="inlineForm.action === 'schemeUrl' ? '请输入 Scheme URL' : '请输入路由 Path'"
                            clearable
                            ref="inlineFormInput" 
                        />
                      </div>
                  </template>
                  
                  <template v-else>
                      <div class="form-item" style="flex: 1">
                        <el-input 
                          v-model="inlineForm.target" 
                          placeholder="操作目标"
                          ref="inlineFormInput" 
                          clearable
                        />
                      </div>
                      
                      <div class="form-item" style="flex: 1" v-if="['input', 'wait', 'assert'].includes(inlineForm.action)">
                        <el-input v-model="inlineForm.value" placeholder="值 / 参数" clearable />
                      </div>
                  </template>
                </div>
                
                <div class="form-footer">
                   <div style="flex: 1"></div>
                   <el-button size="small" @click="cancelInlineAdd">取消</el-button>
                   <el-button size="small" type="primary" color="#1e293b" @click="confirmInlineAdd">确定</el-button>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  ArrowLeft, VideoPlay, Check, Minus, Setting, Delete, Plus, Loading, Camera,
  SwitchButton, CircleClose, Document
} from '@element-plus/icons-vue'
import Draggable from 'vuedraggable'
import DeviceMirror from '@/components/DeviceMirror.vue'
import { deviceApi } from '@/api'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const scriptName = ref('微信支付流程自动化')
const isSaved = ref(true)
const isRecording = ref(false)
const isRunning = ref(false)
const activeIndex = ref(-1)
const mirrorRef = ref(null) // DeviceMirror 组件引用

// Mock Data
// 脚本步骤数据
const steps = ref([])

const actionOptions = [
  { value: '点击 (Click)', action: 'click' },
  { value: '输入 (Input)', action: 'input' },
  { value: '滑动 (Swipe)', action: 'swipe' },
  { value: '等待 (Wait)', action: 'wait' },
  { value: '检查 (Assert)', action: 'assert' },
  { value: 'Scheme URL', action: 'schemeUrl' },
  { value: 'Scheme Router', action: 'schemeRouter' },
]

// Inline Form State
const showInlineAdd = ref(false)
const inlineFormInput = ref(null)
const inlineForm = ref({ action: 'click', target: '', value: '', url: '' })
const editingIndex = ref(-1)

function goBack() { router.push('/ui/scripts') }
function saveScript() { isSaved.value = true; ElMessage.success('保存成功') }
function toggleRecord() { isRecording.value = !isRecording.value }
function screenshot() { /* Implement screenshot */ }
function onActionRecorded(action) { console.log("Recorded", action) }
function onDeviceConnected(device) { ElMessage.success('设备已连接') }

function formatDuration(ms) {
    if (ms >= 1000) return (ms / 1000).toFixed(1) + 's';
    return ms + 'ms';
}

// Run Script
// Run Script
async function runScript() {
    if(isRunning.value) return;
    if(!steps.value.length) {
        ElMessage.warning('请先添加步骤')
        return
    }
    
    isRunning.value = true;
    ElMessage.info('开始执行脚本...')
    
    // 重置状态
    steps.value.forEach(s => {
        s.status = 'pending'
        s.duration = 0
    })
    
    try {
        for (let i = 0; i < steps.value.length; i++) {
            const step = steps.value[i]
            step.status = 'running'
            
            const startTime = performance.now() // 精准计时
            
            try {
                // 根据类型执行
                switch (step.action) {
                    case 'schemeUrl':
                    case 'schemeRouter':
                        if (!step.url) throw new Error('Scheme URL 为空')
                        
                        // 获取当前 WDA 端口 (从 DeviceMirror 组件)
                        let wdaUrl = undefined
                        if (mirrorRef.value && mirrorRef.value.wdaPort > 0) {
                            wdaUrl = `http://localhost:${mirrorRef.value.wdaPort}`
                            console.log('Using WDA URL:', wdaUrl)
                        } else {
                            console.warn('未获取到 WDA 端口，尝试使用默认 http://localhost:8100')
                        }
                        
                        await deviceApi.iosSchemeJump(step.url, wdaUrl)
                        // 硬性等待 2s (User Request)
                        console.log('   Wait 2s after jump...')
                        await new Promise(r => setTimeout(r, 2000))
                        break
                        
                    case 'wait':
                        // 解析时长 (支持 '3s', '3000ms' 或纯数字)
                        let ms = 1000
                        const val = String(step.target || step.value)
                        if (val.includes('s') && !val.includes('ms')) {
                             ms = parseFloat(val) * 1000
                        } else {
                             ms = parseInt(val) || 1000
                        }
                        await new Promise(r => setTimeout(r, ms))
                        break
                        
                    default:
                        // 其他暂时模拟成功 (后续对接更多 API)
                        console.warn('暂未实现的步骤类型:', step.action)
                        await new Promise(r => setTimeout(r, 500))
                        break
                }
                
                step.status = 'success'
            } catch (e) {
                console.error(`步骤 ${i+1} 执行失败:`, e)
                step.status = 'error'
                ElMessage.error(`步骤 ${i+1} 执行失败: ${e.message}`)
                // 可以选择 break 中断执行
                // break 
            } finally {
                const endTime = performance.now()
                step.duration = Math.round(endTime - startTime)
            }
            
            // 步骤间微小间隔
            await new Promise(r => setTimeout(r, 100))
        }
        ElMessage.success('执行完成')
    } catch (e) {
        ElMessage.error('执行异常: ' + e.message)
    } finally {
        isRunning.value = false
    }
}

// Inline Form Logic
function toggleInlineAdd() {
    if (showInlineAdd.value) {
        cancelInlineAdd()
    } else {
        resetInlineForm()
        showInlineAdd.value = true
        nextTick(() => { inlineFormInput.value?.focus() })
    }
}

function resetInlineForm() {
    inlineForm.value = { action: 'click', target: '', value: '', url: '' }
    editingIndex.value = -1
}

function onActionChange() {}

function cancelInlineAdd() {
    showInlineAdd.value = false
    resetInlineForm()
}

function confirmInlineAdd() {
    const actionObj = actionOptions.find(o => o.action === inlineForm.value.action)
    const newStep = {
        id: Date.now(),
        action: inlineForm.value.action,
        actionLabel: actionObj ? actionObj.value.split(' ')[0] : '自定义',
        target: inlineForm.value.target,
        value: inlineForm.value.value,
        url: inlineForm.value.url,
        status: 'pending',
        duration: 0
    }

    if (editingIndex.value > -1) {
        steps.value[editingIndex.value] = { ...steps.value[editingIndex.value], ...newStep }
    } else {
        steps.value.push(newStep)
    }
    cancelInlineAdd()
    isSaved.value = false
}

function editStep(index) {
    const step = steps.value[index]
    inlineForm.value = {
        action: step.action,
        target: step.target,
        value: step.value,
        url: step.url || ''
    }
    editingIndex.value = index
    showInlineAdd.value = true
}

function deleteStep(index) {
    steps.value.splice(index, 1)
    isSaved.value = false
}

watchEffect(() => {
  if (mirrorRef.value?.fps !== undefined) {
    console.log('Parent[ScriptEditorView]: mirrorRef.fps =', mirrorRef.value.fps)
  }
})
</script>

<style lang="scss" scoped>
/* Reset */
button { outline: none; }

/* Full Page Layout - 填满父容器 */
.editor-page {
  background: #f8fafc;
  flex: 1; /* 填满 .main-content */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin: 15px; /* 上下左右间隔 20px */
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

/* Header */
/* Editor Header - 重构后的顶部栏 */
.editor-header {
  height: 56px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: stretch;
  padding: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  z-index: 10;
}

/* 左侧设备状态部分 - 直接与设备面板对齐 */
.header-device-portion {
  width: 340px;
  min-width: 340px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between; /* 两端对齐：信息左，控制右 */
  padding: 0 12px;
  border-right: 1px solid #f1f5f9;
  background: #fff;
}

.device-info-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-name-title {
  font-weight: 700; /* 加粗 */
  font-size: 14px;
  color: #1e293b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fps-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 4px;
  border-radius: 4px;
  background: #ecfdf5;
  color: #10b981; /* 绿色 */
  /* 只在大于0时显示，避免显示 0 FPS */
  display: inline-flex;
}

.device-ctrl-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-box {
  font-size: 11px;
  border: 1px solid #e2e8f0;
  padding: 0 4px;
  border-radius: 2px;
  color: #94a3b8;
  height: 20px;
  line-height: 18px;
}

/* 覆盖 el-button link 样式，使其更紧凑 */
.device-ctrl-group .el-button {
  font-size: 12px;
  font-weight: 500;
  padding: 0 4px;
}

.device-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 10px;
  flex-shrink: 0;
}
/* 右侧脚本部分 */
.header-script-portion {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 24px;
  justify-content: space-between;
  background: #fcfcfc; /* 轻微区别于左侧 */
}

.script-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.script-icon-box {
  width: 36px;
  height: 36px;
  background: #eff6ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  font-size: 18px;
}

.script-text-group {
  display: flex;
  flex-direction: column;
}

.script-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.2;
}

.script-subtitle {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-btn {
  font-weight: 500;
  border-radius: 6px;
}

.run-btn {
  padding-left: 20px; 
  padding-right: 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); /* 渐变蓝 */
  border: none;
  color: #fff;
  transition: all 0.2s;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.editor-body {
  flex: 1;
  display: flex;
  align-items: stretch; /* 确保子元素高度一致 */
  padding: 0;
  gap: 0;
  overflow: hidden;
  min-height: 0; /* 关键：允许 flex 子元素收缩 */
}

/* Device Panel - 左侧面板，与右侧高度一致 */
.device-panel {
  width: 340px; 
  min-width: 340px;
  flex-shrink: 0;
  align-self: stretch; /* 关键：让高度与 flex 容器一致 */
  padding: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  border-radius: 0 0 0 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;

  /* device-mirror 填满父容器 */
  :deep(.device-mirror) {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center; /* 未连接时居中 .phone-frame */
    min-height: 0;
    height: 100%; /* 确保填满 */
  }
  
  /* 未连接时的 phone-frame：保持固定尺寸，不拉伸 */
  :deep(.phone-frame:not(.phone-frame--connected)) {
    flex: none !important; /* 不被 flex 拉伸 */
    width: 220px !important; /* 固定宽度 */
    height: auto !important; /* 高度自适应内容 */
  }
  
  /* 连接后：device-mirror 从顶部开始 */
  :deep(.device-mirror.is-active) {
    justify-content: flex-start;
  }

  /* 连接后：phone-frame 填满 */
  :deep(.phone-frame--connected) {
    flex: 1;
    width: 100%;
    min-height: 0;
    margin: 0 !important;
    background: transparent !important;
  }
  
  /* 连接后的屏幕区域 */
  :deep(.phone-frame--connected .phone-screen) {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent !important;
  }
  
  /* 投屏图片 */
  :deep(.mirror-screen) {
    width: 100%;
    height: auto;
    max-height: 100%;
    object-fit: contain;
  }
}

.steps-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
  background: #f8fafc;
  padding: 16px 0 16px 16px;
  border-radius: 0 0 8px 0; /* 右下圆角 */
}

.steps-container {
    flex: 1;
    min-height: 0; /* 关键：允许 flex 子元素收缩 */
    overflow-y: auto;
    padding-right: 16px;
}

/* 包装器也需要约束 */
.steps-wrapper {
    display: flex;
    flex-direction: column;
}

.steps-list-area {
    display: flex;
    flex-direction: column;
    gap: 16px; 
}

/* Step Card Styles */
.step-row {
    position: relative;
    display: flex;
    align-items: center;
    height: 48px; /* 减小高度，由 64px -> 48px */
    padding: 0 24px;
    background: #ffffff;
    border-radius: 12px;
    
    border: 1px solid transparent; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    transition: all 0.2s;
    cursor: default;
    
    &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        transform: translateY(-1px);
        .hover-actions, .config-icon { opacity: 1; }
    }
    
    /* Running: Blue Border + Blue Glow */
    &.status-running {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        z-index: 5;
    }
}

/* Left Colored Strip: Rounded on left side to match card */
.status-strip {
    position: absolute;
    left: 0;
    top: 4px; 
    bottom: 4px; 
    width: 4px; 
    border-radius: 0 4px 4px 0; /* 左侧贴边，右侧圆角 */
    background: transparent;
}

.status-running .status-strip { background: #3b82f6; } 
.status-success .status-strip { background: #10b981; }

/* Index */
.step-index {
    font-family: 'MonoLisa', 'SF Mono', monospace;
    font-size: 13px;
    color: #94a3b8; /* Lighter Gray */
    width: 48px; 
    font-weight: 500;
}

/* Action Tag */
.step-tag { width: 80px; display: flex; align-items: center; }
.tag-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
}
/* Tag Colors - Muted backgrounds, strong text */
.wait { background: #f3f4f6; color: #4b5563; }
.swipe { background: #fff7ed; color: #c2410c; }
.click { background: #eff6ff; color: #2563eb; }
.input { background: #f5f3ff; color: #7c3aed; }
.assert { background: #ecfdf5; color: #059669; }
.schemeUrl, .schemeRouter { background: #eef2ff; color: #4338ca; }

/* Content */
.step-content {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    margin-left: 12px;
    
    .target-text { font-weight: 600; color: #334155; font-size: 14px; }
    .value-pill {
        background: #f8fafc;
        color: #64748b;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-family: 'SF Mono', monospace;
        border: 1px solid #e2e8f0;
    }
    .config-icon { margin-left: auto; color: #cbd5e1; cursor: pointer; opacity: 0; transition: opacity 0.2s; }
}

/* Status */
.step-status-area {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-width: 120px;
    font-size: 13px;
    
    .pending { color: #cbd5e1; font-weight: 400; font-size: 12px; }
    
    .running { color: #3b82f6; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    .spinner-ring {
        width: 14px; height: 14px;
        border: 2px solid #3b82f6; border-top-color: transparent; border-radius: 50%;
        animation: rotate 1s linear infinite;
    }
    
    .success {
        display: flex; align-items: center; gap: 8px;
        .duration-text { color: #94a3b8; font-size: 12px; font-family: 'SF Mono', monospace; }
        .check-circle { 
            width: 16px; height: 16px; background: #10b981; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-size: 10px;
        }
    }
    
    .hover-actions { margin-left:12px; opacity: 0; transition: opacity 0.2s; }
}

@keyframes rotate { to { transform: rotate(360deg); } }

/* Inline Form */
.add-step-wrapper { margin-top: 16px; }

.add-trigger-btn {
    height: 56px;
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    &:hover { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }
}

.inline-add-form {
    background: #ffffff;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    .form-row { display: flex; gap: 16px; margin-bottom: 20px; }
    .form-footer { display: flex; gap: 12px; }
}
</style>
