<template>
  <div class="knowledge-layout">
    
    <aside class="sidebar-panel">
      <div class="sidebar-header">
        <div class="brand-card">
          <div class="logo-box">
             <svg width="24" height="24" viewBox="0 0 24 24" fill="white"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          <div class="brand-meta">
            <span class="app-name">翼支付 Pro</span>
            <span class="workspace">UI 自动化工作台</span>
          </div>
        </div>
        <button class="mini-add-btn" title="新建文件夹">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>

      <div class="nav-scroll">
        <div class="nav-group-label">主要视图</div>
        <div class="nav-item active">
          <span class="icon">💠</span> 全部页面 <span class="badge">13</span>
        </div>
        <div class="nav-item"><span class="icon">🧩</span> 公共组件 <span class="badge gray">4</span></div>
        <div class="nav-group-label mt-4">业务模块</div>
        <div class="nav-item"><span class="icon">📂</span> 充值缴费</div>
        <div class="nav-item"><span class="icon">📂</span> 转账业务</div>
      </div>
    </aside>

    <main class="gallery-container">
      
      <header class="hero-header">
        
        <div class="hero-left">
          <div class="hero-icon-box">
             <span class="emoji">📱</span>
          </div>
          
          <div class="hero-text">
            <div class="title-row">
              <h1 class="page-title">UI 页面知识库</h1>
              <div class="status-badge">
                <span class="dot"></span> Online
              </div>
            </div>
            
            <p class="page-desc">
              管理已识别的 App 页面及其 UI 元素资产
              <span class="divider">|</span>
              <span class="stat-text">共收录 <strong>13</strong> 个页面</span>
            </p>
          </div>
        </div>
        
        <div class="hero-right">
          <div class="search-box">
             <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
             <input type="text" placeholder="搜索页面 ID 或名称...">
          </div>
          
          <div class="view-switcher">
            <button class="switch-btn active"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg></button>
            <div class="v-line"></div>
            <button class="switch-btn"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg></button>
          </div>

          <button class="btn-new">
            <span class="plus">+</span> 新增页面
          </button>
        </div>
      </header>

      <div class="gallery-scroll-area">
        <div class="card-grid">
           <div class="page-card" v-for="page in pages" :key="page.id">
              <div class="card-top-bar"><span class="id-tag">#{{page.id}}</span><div class="actions">...</div></div>
              <div class="card-preview"><img :src="page.screenshot" class="screen-img"></div>
              <div class="card-info">
                <div class="title-row"><div class="page-name">{{page.name}}</div><span class="ver-badge">{{page.ver}}</span></div>
                <div class="meta-row"><span class="label">元素 {{page.elements}}</span> <span class="dot">·</span> <span>{{page.time}}</span></div>
              </div>
           </div>
           
           <div class="upload-placeholder">
             <div class="dashed-border"><div class="upload-icon">+</div><div class="upload-text">上传新截图</div></div>
           </div>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const pages = ref([
  { id: 1001, name: '翼支付-我的-余额', screenshot: 'https://cdn.dribbble.com/users/1615584/screenshots/15710319/media/c0702d7607a049cb94c7943d702d08a5.jpg', elements: 14, ver: 'v1.0', time: '6小时前' },
  { id: 1002, name: '转账到账-结果页', screenshot: 'https://cdn.dribbble.com/users/4136335/screenshots/14457630/media/1a5665476711516e814a0194483a991f.png', elements: 7, ver: 'v1.2', time: '1天前' },
  { id: 1003, name: '公共组件-支付密码', screenshot: 'https://cdn.dribbble.com/users/2563359/screenshots/15456499/media/b02c003233842186987c93e488106981.png', elements: 12, ver: 'v2.0', time: '2天前' },
]);
</script>

<style scoped>
/* 基础重置 */
.knowledge-layout { display: flex; height: 100vh; background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; }

/* --- Left Sidebar (更精致的头部) --- */
.sidebar-panel { width: 240px; background: white; display: flex; flex-direction: column; border-right: 1px solid #f1f5f9; flex-shrink: 0; }

.sidebar-header { 
  padding: 16px; 
  display: flex; justify-content: space-between; align-items: center; 
  border-bottom: 1px solid #f8fafc;
}
.brand-card { display: flex; align-items: center; gap: 10px; }
.logo-box { 
  width: 32px; height: 32px; 
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}
.brand-meta { display: flex; flex-direction: column; justify-content: center; }
.app-name { font-weight: 800; font-size: 14px; color: #0f172a; line-height: 1.2; }
.workspace { font-size: 10px; color: #94a3b8; font-weight: 500; }

.mini-add-btn { width: 24px; height: 24px; border: 1px solid #e2e8f0; border-radius: 6px; background: white; color: #64748b; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.mini-add-btn:hover { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }

/* 导航样式省略，保持不变 */
.nav-scroll { flex: 1; padding: 16px 12px; }
.nav-group-label { font-size: 11px; color: #94a3b8; font-weight: 700; padding: 0 12px 8px; text-transform: uppercase; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 8px; cursor: pointer; color: #64748b; font-size: 13px; font-weight: 500; margin-bottom: 2px; }
.nav-item.active { background: #eff6ff; color: #3b82f6; font-weight: 600; }
.nav-item .badge { margin-left: auto; font-size: 10px; background: #dbeafe; color: #3b82f6; padding: 1px 6px; border-radius: 10px; }
.nav-item .badge.gray { background: #f1f5f9; color: #94a3b8; }

/* --- Right Content --- */
.gallery-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ★ 核心：Hero Header 样式 ★ */
.hero-header {
  height: 88px; /* 增加高度，更有气势 */
  padding: 0 32px;
  background: white;
  border-bottom: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
}

.hero-left { display: flex; align-items: center; gap: 16px; }

/* 视觉锚点：大图标盒子 */
.hero-icon-box {
  width: 48px; height: 48px;
  background: #f1f5f9;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
}

.hero-text { display: flex; flex-direction: column; gap: 4px; }

.title-row { display: flex; align-items: center; gap: 10px; }
.page-title { font-size: 20px; font-weight: 800; color: #0f172a; margin: 0; line-height: 1; }

/* 优化后的状态胶囊 */
.status-badge { 
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 600; color: #15803d; 
  background: #dcfce7; padding: 2px 8px; border-radius: 12px; 
  border: 1px solid #bbf7d0; /* 增加边框增加精致感 */
}
.status-badge .dot { width: 6px; height: 6px; background: #15803d; border-radius: 50%; }

/* 描述行：聚合信息 */
.page-desc { font-size: 13px; color: #64748b; margin: 0; display: flex; align-items: center; gap: 10px; }
.divider { color: #e2e8f0; font-size: 12px; }
.stat-text { color: #64748b; font-size: 12px; background: #f8fafc; padding: 2px 6px; border-radius: 4px; }
.stat-text strong { color: #0f172a; font-weight: 700; }

/* Header Right Actions */
.hero-right { display: flex; align-items: center; gap: 12px; }

.search-box { position: relative; }
.search-box input { 
  padding: 9px 12px 9px 34px; border: 1px solid #e2e8f0; border-radius: 8px; width: 200px; 
  outline: none; font-size: 13px; background: #fff; transition: all 0.2s; 
}
.search-box input:focus { border-color: #3b82f6; width: 240px; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
.search-box .icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; }

.view-switcher { display: flex; align-items: center; background: #f1f5f9; padding: 2px; border-radius: 8px; border: 1px solid #e2e8f0; }
.switch-btn { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; color: #94a3b8; cursor: pointer; border-radius: 6px; }
.switch-btn.active { background: white; color: #3b82f6; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.v-line { width: 1px; height: 16px; background: #cbd5e1; margin: 0 2px; }

.btn-new { 
  padding: 0 20px; height: 38px; background: #0f172a; color: white; border: none; 
  border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; 
  display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); 
}
.btn-new:hover { background: #1e293b; transform: translateY(-1px); }

/* Grid Area (保持不变) */
.gallery-scroll-area { flex: 1; overflow-y: auto; padding: 24px 32px; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 24px; }
.page-card { background: white; border-radius: 16px; overflow: hidden; border: 1px solid #f1f5f9; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; transition: all 0.2s; }
.page-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px -8px rgba(0,0,0,0.1); border-color: #e2e8f0; }
.card-top-bar { padding: 10px 14px; display: flex; justify-content: space-between; border-bottom: 1px solid #f8fafc; }
.id-tag { font-family: monospace; font-size: 12px; color: #94a3b8; background: #f8fafc; padding: 2px 6px; border-radius: 4px; }
.card-preview { height: 160px; background: #f8fafc; display: flex; justify-content: center; overflow: hidden; }
.screen-img { width: 100%; height: 100%; object-fit: cover; object-position: top; }
.card-info { padding: 14px; }
.title-row { display: flex; justify-content: space-between; margin-bottom: 6px; }
.page-name { font-weight: 700; font-size: 15px; color: #0f172a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 140px; }
.ver-badge { font-size: 10px; background: #f0fdf4; color: #166534; padding: 1px 6px; border-radius: 4px; }
.meta-row { font-size: 12px; color: #64748b; display: flex; gap: 6px; align-items: center; }
.upload-placeholder { border: 2px dashed #e2e8f0; border-radius: 16px; min-height: 260px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #94a3b8; font-size: 13px; font-weight: 500; flex-direction: column; }
.upload-icon { font-size: 32px; font-weight: 300; margin-bottom: 8px; }
</style>