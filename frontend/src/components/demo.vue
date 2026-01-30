<template>
  <div class="flex h-screen bg-slate-50 font-sans text-slate-700 overflow-hidden">
    
    <div class="w-[380px] flex-shrink-0 bg-slate-900 flex flex-col border-r border-slate-800 shadow-2xl z-10">
      <div class="h-10 flex items-center justify-between px-4 border-b border-slate-800 text-[10px] text-slate-400 font-mono">
        <div class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,0.5)]"></span>
          <span>ONLINE: iPhone 15 Pro</span>
        </div>
        <span>FPS: 60 | 12ms</span>
      </div>

      <div class="flex-1 flex items-center justify-center p-4 overflow-hidden relative group select-none">
        <div class="relative w-[300px] h-[650px] bg-black rounded-[35px] border-[6px] border-slate-700 shadow-2xl overflow-hidden ring-1 ring-white/10">
          
          <img 
            src="https://images.unsplash.com/photo-1616348436168-de43ad0db179?q=80&w=1000&auto=format&fit=crop" 
            class="w-full h-full object-cover opacity-95"
            draggable="false"
          />

          <div v-if="mode === 'teach'" class="absolute inset-0 z-10">
            <div 
              v-for="item in elements" 
              :key="item.id"
              class="absolute transition-all duration-200 border-2 rounded-[2px] cursor-pointer"
              :class="[
                hoverId === item.id 
                  ? 'border-indigo-400 bg-indigo-500/20 z-20 shadow-[0_0_15px_rgba(99,102,241,0.6)]' 
                  : 'border-blue-400/30 hover:border-blue-400 hover:bg-blue-400/10'
              ]"
              :style="{
                left: item.bbox[0] + '%',
                top: item.bbox[1] + '%',
                width: item.bbox[2] + '%',
                height: item.bbox[3] + '%'
              }"
              @mouseenter="hoverId = item.id"
              @mouseleave="hoverId = null"
              @click="scrollToItem(item.id)"
            >
              <div v-if="hoverId === item.id" class="absolute -top-5 left-0 bg-indigo-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap z-30 flex items-center gap-1">
                <span>{{ item.id }}</span>
                <span class="opacity-50">|</span>
                <span>{{ item.name }}</span>
              </div>
            </div>
            
            <div v-if="isAnalyzing" class="absolute inset-0 z-50 bg-slate-900/40 backdrop-blur-[1px] pointer-events-none flex flex-col items-center justify-center">
               <div class="w-full h-[2px] bg-gradient-to-r from-transparent via-indigo-400 to-transparent absolute top-0 animate-scan"></div>
               <div class="px-3 py-1 bg-black/60 rounded-full text-indigo-300 text-xs font-mono border border-indigo-500/30">AI Analysis in Progress...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="flex-1 flex flex-col bg-slate-100 h-full min-w-0">
      
      <div class="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-6 shrink-0 shadow-sm z-20">
        
        <div class="flex bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button 
            @click="mode = 'execute'"
            class="px-4 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-2"
            :class="mode === 'execute' ? 'bg-white text-slate-800 shadow-sm ring-1 ring-black/5' : 'text-slate-500 hover:text-slate-700'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            执行模式
          </button>
          <button 
            @click="mode = 'teach'"
            class="px-4 py-1.5 text-xs font-bold rounded-md transition-all flex items-center gap-2"
            :class="mode === 'teach' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:text-slate-700'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            知识库教学
          </button>
        </div>

        <div v-if="mode === 'teach'" class="flex items-center gap-4">
           <div class="text-right hidden xl:block">
             <div class="text-xs font-bold text-slate-700">微信-个人中心</div>
             <div class="text-[10px] text-slate-400">上次更新: 刚刚</div>
           </div>
           <div class="h-6 w-px bg-slate-200 mx-2"></div>
           <button class="text-slate-400 hover:text-red-500 p-2 rounded-full hover:bg-slate-100 transition-colors" title="清空">
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
           </button>
           <button 
             @click="analyzePage"
             :disabled="isAnalyzing"
             class="group relative px-5 py-2 bg-slate-800 text-white rounded-lg text-xs font-bold flex items-center gap-2 hover:bg-black transition-all disabled:opacity-70 shadow-lg shadow-slate-300"
           >
             <svg v-if="!isAnalyzing" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
             <svg v-else class="animate-spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
             <span>{{ isAnalyzing ? '正在扫描...' : 'AI 全页分析' }}</span>
           </button>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 md:p-6" ref="listContainer">
        
        <div v-if="mode === 'teach' && elements.length === 0 && !isAnalyzing" class="h-full flex flex-col items-center justify-center opacity-40">
           <div class="w-32 h-32 bg-slate-200 rounded-full flex items-center justify-center mb-6">
             <svg class="text-slate-400" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 12h20M2 12l5-5M22 12l-5 5"/></svg>
           </div>
           <p class="text-lg font-medium text-slate-500">知识库暂无当前页面数据</p>
           <p class="text-sm text-slate-400 mt-2">点击右上角按钮开始 AI 扫描</p>
        </div>

        <div v-if="mode === 'teach' && elements.length > 0" class="max-w-6xl mx-auto space-y-6">
          
          <div class="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex gap-4 items-start">
            <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600 shrink-0">
               <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14 2z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div class="flex-1">
               <label class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Page Summary & Context</label>
               <textarea 
                  v-model="pageSummary" 
                  rows="2"
                  class="w-full mt-1 text-sm text-slate-700 bg-transparent border-none p-0 focus:ring-0 resize-none leading-relaxed placeholder-slate-300"
                  placeholder="请输入页面描述..."
               ></textarea>
            </div>
          </div>

          <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
            
            <div 
              v-for="item in elements" 
              :key="item.id"
              :id="'item-' + item.id"
              class="group bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all duration-200 flex flex-col relative overflow-hidden"
              :class="{'ring-2 ring-indigo-500 ring-offset-2': hoverId === item.id}"
              @mouseenter="hoverId = item.id"
              @mouseleave="hoverId = null"
            > 
              <div class="p-3 flex gap-3 border-b border-slate-50 bg-gradient-to-b from-white to-slate-50/50">
                <div class="w-14 h-14 bg-slate-200 rounded-lg border border-slate-300 overflow-hidden shrink-0 relative shadow-inner">
                   <div 
                     class="w-full h-full bg-no-repeat transition-transform duration-500 group-hover:scale-110"
                     :style="calculateBackgroundStyle(item.bbox)"
                   ></div>
                </div>

                <div class="flex-1 min-w-0 flex flex-col justify-center">
                   <div class="flex items-center justify-between">
                      <input 
                        v-model="item.name" 
                        class="font-bold text-sm text-slate-800 bg-transparent border-none p-0 focus:ring-0 w-full truncate hover:text-indigo-600 transition-colors"
                      />
                      <span class="text-[9px] font-mono px-1.5 py-0.5 bg-slate-100 text-slate-400 rounded-full">
                        {{ item.confidence }}%
                      </span>
                   </div>
                   
                   <div class="flex items-center gap-2 mt-1.5">
                     <span class="text-[10px] font-bold px-2 py-0.5 rounded border" 
                       :class="{
                         'bg-blue-50 text-blue-600 border-blue-100': item.type === 'Button',
                         'bg-green-50 text-green-600 border-green-100': item.type === 'Input',
                         'bg-orange-50 text-orange-600 border-orange-100': item.type === 'Icon',
                         'bg-slate-50 text-slate-600 border-slate-100': item.type === 'Text'
                       }">
                       {{ item.type }}
                     </span>
                     
                     <span v-if="item.ocr" class="flex items-center gap-1 text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded truncate max-w-[120px]">
                       <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7V4h16v3M9 20h6M12 4v16"/></svg>
                       {{ item.ocr }}
                     </span>
                   </div>
                </div>
              </div>

              <div class="p-3 bg-white flex-1 relative">
                <label class="text-[9px] font-bold text-slate-300 uppercase mb-1 block">Visual Context</label>
                <textarea 
                  v-model="item.desc" 
                  rows="2"
                  class="w-full text-xs text-slate-600 bg-slate-50 border border-transparent rounded-md px-2 py-1.5 focus:bg-white focus:border-indigo-300 focus:ring-2 focus:ring-indigo-50 outline-none resize-none leading-relaxed transition-all hover:bg-white hover:border-slate-200"
                ></textarea>
                
                <div class="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 backdrop-blur pl-2 rounded-l-lg">
                   <button class="p-1.5 hover:bg-slate-100 rounded text-slate-400 hover:text-indigo-600" title="重新生成">
                     <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/></svg>
                   </button>
                   <button class="p-1.5 hover:bg-red-50 rounded text-slate-400 hover:text-red-500" @click="removeElement(item.id)" title="删除">
                     <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                   </button>
                </div>
              </div>

            </div>
            
            <div class="border-2 border-dashed border-slate-200 rounded-xl p-4 flex flex-col items-center justify-center text-slate-400 min-h-[140px] hover:border-indigo-300 hover:text-indigo-500 hover:bg-indigo-50/10 cursor-pointer transition-all">
               <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
               <span class="text-xs font-bold mt-2">手动添加元素</span>
            </div>

          </div>
        </div>
        
        <div v-if="mode === 'execute'" class="h-full flex flex-col items-center justify-center text-slate-400">
           <div class="text-6xl mb-4">🤖</div>
           <h3 class="text-slate-600 font-bold text-lg">执行模式就绪</h3>
           <p class="text-sm mt-2">点击顶部切换到“知识库教学”模式进行录入</p>
        </div>

      </div>

      <div v-if="mode === 'teach' && elements.length > 0" class="h-16 bg-white border-t border-slate-200 px-6 flex items-center justify-between shrink-0 z-20 shadow-[0_-5px_20px_rgba(0,0,0,0.03)]">
         <div class="flex items-center gap-4">
            <div class="text-xs text-slate-500 font-medium bg-slate-100 px-3 py-1.5 rounded-full">
               已识别 <span class="text-indigo-600 font-bold">{{ elements.length }}</span> 个元素
            </div>
            <div class="text-[10px] text-slate-400">预计消耗向量存储: 12KB</div>
         </div>
         <div class="flex gap-3">
           <button class="px-5 py-2.5 rounded-lg border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50 transition-colors">取消变更</button>
           <button class="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all transform active:scale-95 flex items-center gap-2">
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
             保存到知识库
           </button>
         </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const mode = ref('teach');
const isAnalyzing = ref(false);
const hoverId = ref(null);
const pageSummary = ref("微信-个人中心页，包含顶部的用户信息卡片，以及下方的支付、收藏等入口列表。");

// 模拟更丰富的数据
const elements = ref([
  { id: 1, name: '微信图标', type: 'Icon', ocr: null, bbox: [5, 42, 18, 9], confidence: 99, desc: '绿色的方形App图标，经典对话气泡Logo。' },
  { id: 2, name: '支付入口', type: 'Button', ocr: '支付', bbox: [5, 30, 90, 8], confidence: 95, desc: '列表项，包含绿色钱包图标和文字“支付”，右侧有箭头。' },
  { id: 3, name: '收藏', type: 'Button', ocr: '收藏', bbox: [5, 40, 90, 8], confidence: 92, desc: '列表项，包含彩色立方体图标。' },
  { id: 4, name: '搜索框', type: 'Input', ocr: '搜索', bbox: [10, 5, 80, 6], confidence: 98, desc: '顶部灰色圆角矩形区域，内含放大镜图标。' },
  { id: 5, name: '底部导航-我', type: 'Text', ocr: '我', bbox: [75, 92, 20, 8], confidence: 88, desc: '底部Tab栏最右侧的选项，图标为高亮绿色。' },
]);

const calculateBackgroundStyle = (bbox) => {
  const [left, top, width, height] = bbox;
  const imgUrl = 'https://images.unsplash.com/photo-1616348436168-de43ad0db179?q=80&w=1000&auto=format&fit=crop';
  const safeW = Math.max(width, 1);
  const safeH = Math.max(height, 1);
  return {
    backgroundImage: `url('${imgUrl}')`,
    backgroundSize: `${(100 / safeW) * 100}% ${(100 / safeH) * 100}%`,
    backgroundPosition: `${(left / (100 - safeW)) * 100}% ${(top / (100 - safeH)) * 100}%`
  };
};

const analyzePage = () => {
  isAnalyzing.value = true;
  setTimeout(() => isAnalyzing.value = false, 2000);
};

const removeElement = (id) => {
  elements.value = elements.value.filter(e => e.id !== id);
};

const scrollToItem = (id) => {
  const el = document.getElementById('item-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  hoverId.value = id;
};
</script>

<style scoped>
/* 扫描动画 */
@keyframes scan {
  0% { top: 0%; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}
.animate-scan {
  animation: scan 2s linear infinite;
}

/* 隐藏滚动条但保留滚动功能 (可选，看个人喜好) */
/* ::-webkit-scrollbar { width: 0px; } */
</style>