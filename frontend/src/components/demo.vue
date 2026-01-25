<template>
  <div class="flex h-screen w-full bg-[#F5F7FA] font-sans text-slate-600 overflow-hidden">
    
    <aside class="w-[360px] flex flex-col border-r border-slate-200 bg-white shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-10">
      
      <div class="h-14 border-b border-slate-100 flex items-center justify-between px-4 bg-white/50 backdrop-blur">
        <div class="flex items-center gap-2">
           <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
           <span class="text-xs font-bold text-slate-700">iPhone 15 Pro</span>
        </div>
        <div class="flex items-center gap-1">
           <button class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors" title="Back">
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
           </button>
           <button class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors" title="Home">
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="5" width="14" height="14" rx="4"/></svg>
           </button>
           <button class="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors" title="Inspector Mode">
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
           </button>
        </div>
      </div>

      <div class="flex-1 bg-slate-50 flex items-center justify-center p-6 overflow-hidden relative group">
        
        <div class="relative w-full max-w-[280px] aspect-[9/19.5] bg-gray-900 rounded-[2.5rem] shadow-2xl border-[6px] border-gray-800 ring-1 ring-black/10 overflow-hidden select-none transform transition-transform duration-500 hover:scale-[1.02]">
           
           <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[30%] h-[24px] bg-black rounded-b-2xl z-20"></div>

           <div class="absolute inset-0 bg-white flex flex-col">
              <div class="h-24 bg-slate-100 border-b border-slate-200 flex items-end pb-3 px-4">
                 <div class="flex-1 h-8 bg-slate-200 rounded animate-pulse"></div>
                 <div class="w-6 h-6 bg-slate-200 rounded-full ml-3"></div>
              </div>
              <div class="flex-1 p-4 space-y-4 overflow-hidden">
                 <div class="h-20 bg-blue-50 rounded-xl border border-blue-100 flex items-center justify-center text-blue-300 text-xs">File Transfer Helper</div>
                 <div class="space-y-2">
                    <div class="h-3 w-1/2 bg-slate-100 rounded"></div>
                    <div class="h-3 w-3/4 bg-slate-100 rounded"></div>
                 </div>
                 <div class="absolute top-[30%] left-[10%] right-[10%] h-12 border-2 border-dashed border-red-500 bg-red-500/10 flex items-center justify-center z-10 cursor-pointer">
                    <span class="bg-red-500 text-white text-[10px] px-1 absolute -top-4 left-0 rounded-t">Button: Login</span>
                 </div>
              </div>
           </div>
        </div>

        <div class="absolute bottom-4 text-[10px] text-slate-400 font-mono">
           Resolution: 1179x2556 | 60fps
        </div>

      </div>
    </aside>

    <main class="flex-1 flex flex-col min-w-0 bg-[#F5F7FA]">
      
      <header class="h-14 flex items-center justify-between px-6 bg-white border-b border-slate-200 shadow-sm z-10">
         <div class="flex items-center gap-3">
             <div class="p-1.5 bg-blue-100 rounded text-blue-600">
               <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
             </div>
             <div>
                <h1 class="text-sm font-bold text-slate-800">微信支付流程自动化</h1>
                <p class="text-[10px] text-slate-400 leading-none mt-0.5">Last edited 2 mins ago</p>
             </div>
         </div>
         
         <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400 mr-2" v-if="isRunning">Executing Step {{ currentStepIndex + 1 }}/{{ steps.length }}</span>
            <button class="h-8 px-3 bg-white border border-slate-200 hover:border-blue-400 hover:text-blue-500 text-slate-600 rounded text-xs font-semibold transition-all">保存</button>
            <button 
              @click="runScript"
              :disabled="isRunning"
              class="h-8 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold transition-all flex items-center gap-2 shadow-lg shadow-slate-200"
            >
              <svg v-if="!isRunning" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              <svg v-else class="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
              {{ isRunning ? 'Running...' : 'Run Test' }}
            </button>
         </div>
      </header>

      <div class="flex-1 overflow-y-auto p-6 scroll-smooth" ref="scrollContainer">
        <div class="max-w-4xl mx-auto space-y-2.5 pb-20">
          
          <transition-group name="list">
            <div 
              v-for="(step, index) in steps" 
              :key="step.id"
              :id="'step-' + index"
              draggable="true"
              @dragstart="onDragStart($event, index)"
              @dragover.prevent="onDragOver($event, index)"
              @dragend="onDragEnd"
              class="relative bg-white rounded-lg border flex items-center overflow-hidden transition-all duration-300"
              :class="[
                draggedIndex === index ? 'opacity-40 border-dashed border-slate-400 bg-slate-50 scale-[0.98]' : 'hover:shadow-md',
                // 运行状态样式逻辑
                step.status === 'running' ? 'border-blue-400 ring-1 ring-blue-400 shadow-md translate-x-1 z-10' : 
                step.status === 'success' ? 'border-slate-100 opacity-70 hover:opacity-100' : 'border-slate-100'
              ]"
            >
              
              <div 
                 class="absolute left-0 top-0 bottom-0 w-[3px] transition-colors duration-300 z-20"
                 :class="{
                    'bg-blue-500': step.status === 'running',
                    'bg-emerald-400': step.status === 'success',
                    'bg-transparent': step.status === 'pending'
                 }"
              ></div>

              <div class="w-10 flex-shrink-0 self-stretch flex items-center justify-center bg-slate-50/50 border-r border-slate-50">
                <span class="text-[10px] font-mono font-medium" :class="step.status === 'running' ? 'text-blue-600 font-bold' : 'text-slate-300'">
                  {{ String(index + 1).padStart(2, '0') }}
                </span>
              </div>

              <div class="flex-1 flex items-center py-2.5 px-3 gap-3 overflow-hidden">
                <span 
                    class="flex-shrink-0 inline-flex items-center justify-center px-2 py-[2px] rounded-[4px] text-[10px] font-bold uppercase tracking-wide min-w-[50px] border shadow-sm"
                    :class="getActionStyle(step.type).badge"
                  >
                    {{ getActionLabel(step.type) }}
                </span>

                <div class="flex-1 flex items-center text-[13px] leading-none gap-2 truncate">
                   <span v-if="step.method" class="font-medium" :class="getMethodColor(step.type)">{{ step.method }}</span>
                   <span v-if="step.target" class="font-semibold text-slate-700">{{ step.target }}</span>
                   <code v-if="step.value" class="px-1.5 py-0.5 bg-slate-50 border border-slate-200 text-slate-600 rounded text-[11px] font-mono">{{ step.value }}</code>
                   <span v-if="step.suffix" class="text-blue-600 font-medium ml-0.5 text-[12px]">{{ step.suffix }}</span>
                </div>

                <div class="flex items-center justify-end pl-2 min-w-[80px]">
                   <div v-if="step.status === 'running'" class="flex items-center gap-1.5 text-blue-600">
                      <svg class="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg>
                   </div>
                   <div v-if="step.status === 'success'" class="flex items-center gap-1 text-emerald-500 animate-in fade-in zoom-in">
                      <span class="text-[10px] font-mono text-slate-300 mr-1">{{ step.actualDuration }}</span>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                   </div>
                </div>
              </div>

              <div v-if="!isRunning" class="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 hover:opacity-100 transition-opacity bg-white pl-2 shadow-[-10px_0_10px_white]">
                 <button class="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-blue-600"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
                 <button class="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-red-600"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
              </div>

            </div>
          </transition-group>
        </div>
      </div>
      
      <div class="h-16 bg-white border-t border-slate-100 flex items-center justify-center px-6">
         <div class="w-full max-w-2xl relative group">
             <div class="absolute inset-0 bg-blue-100 rounded-lg opacity-20 blur group-hover:opacity-40 transition duration-500"></div>
             <div class="relative bg-white rounded-lg flex items-center p-1.5 border border-blue-100 shadow-sm">
                <div class="pl-3 pr-2 text-blue-500"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
                <input type="text" class="flex-1 py-1.5 bg-transparent border-none focus:ring-0 text-slate-700 placeholder-slate-400 text-sm" placeholder="Ask AI to add step: 'Wait for Login button then Click'...">
                <button class="px-3 py-1 bg-slate-50 hover:bg-blue-50 text-slate-500 hover:text-blue-600 rounded text-xs font-medium border border-slate-200 transition-colors">Generate</button>
             </div>
         </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// 样式配置与之前的保持一致
const actionConfig = {
  click: { label: '点击', badge: 'bg-blue-50 text-blue-600 border-blue-100' },
  input: { label: '输入', badge: 'bg-purple-50 text-purple-600 border-purple-100' },
  swipe: { label: '滑动', badge: 'bg-orange-50 text-orange-600 border-orange-100' },
  wait:  { label: '等待', badge: 'bg-slate-100 text-slate-600 border-slate-200' },
  check: { label: '检查', badge: 'bg-teal-50 text-teal-600 border-teal-100' },
};

const initialSteps = [
  { id: 1, type: 'wait', value: '3秒', status: 'pending', duration: 3000 },
  { id: 2, type: 'swipe', method: '向上', target: '文件传输助手', suffix: '出现', status: 'pending', duration: 1200 },
  { id: 3, type: 'click', method: '文字', target: '文件传输助手', status: 'pending', duration: 500 },
  { id: 4, type: 'input', method: '变量', target: 'random', value: '=', status: 'pending', duration: 200 },
  { id: 5, type: 'click', method: 'ID', target: '微信input', status: 'pending', duration: 800 },
  { id: 6, type: 'input', value: '${wechat_pay_link}', status: 'pending', duration: 600 },
  { id: 7, type: 'click', method: '文字', target: '发送', status: 'pending', duration: 400 },
  { id: 8, type: 'check', method: '文字', target: '支付成功', suffix: '存在', status: 'pending', duration: 300 },
];

const steps = ref(JSON.parse(JSON.stringify(initialSteps)));
const isRunning = ref(false);
const draggedIndex = ref(null);
const currentStepIndex = ref(0);

// 辅助函数
const getActionStyle = (type) => actionConfig[type] || actionConfig.click;
const getActionLabel = (type) => actionConfig[type]?.label || type;
const getMethodColor = (type) => {
    if (type === 'swipe') return 'text-orange-500';
    if (type === 'click') return 'text-red-500';
    if (type === 'input') return 'text-purple-500';
    if (type === 'check') return 'text-teal-600';
    return 'text-slate-500';
}

// 拖拽逻辑
const onDragStart = (e, index) => { draggedIndex.value = index; e.dataTransfer.effectAllowed = 'move'; };
const onDragOver = (e, index) => {
  if (draggedIndex.value === null || draggedIndex.value === index) return;
  const item = steps.value[draggedIndex.value];
  steps.value.splice(draggedIndex.value, 1);
  steps.value.splice(index, 0, item);
  draggedIndex.value = index;
};
const onDragEnd = () => { draggedIndex.value = null; };

// 运行逻辑 (带滚动)
const runScript = async () => {
  if (isRunning.value) return;
  isRunning.value = true;
  steps.value.forEach(s => { s.status = 'pending'; delete s.actualDuration; });

  for (let i = 0; i < steps.value.length; i++) {
    currentStepIndex.value = i;
    const step = steps.value[i];
    step.status = 'running';
    
    // 自动滚动到对应元素
    const el = document.getElementById('step-' + i);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });

    await new Promise(resolve => setTimeout(resolve, step.duration || 500));
    
    step.status = 'success';
    step.actualDuration = (step.duration < 1000) ? `${step.duration}ms` : `${(step.duration/1000).toFixed(1)}s`;
  }
  isRunning.value = false;
};
</script>

<style scoped>
/* 隐藏滚动条但保留功能 */
.overflow-y-auto::-webkit-scrollbar { width: 6px; }
.overflow-y-auto::-webkit-scrollbar-track { background: transparent; }
.overflow-y-auto::-webkit-scrollbar-thumb { background-color: rgba(203, 213, 225, 0.5); border-radius: 3px; }
.overflow-y-auto::-webkit-scrollbar-thumb:hover { background-color: rgba(148, 163, 184, 0.8); }

.list-enter-active, .list-leave-active { transition: all 0.3s ease; }
.list-enter-from, .list-leave-to { opacity: 0; transform: translateX(20px); }
</style>