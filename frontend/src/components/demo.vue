<template>
  <div class="script-manager-unified">
    
    <aside class="sidebar-tree">
      <div class="sidebar-header">
        <div class="app-selector">
          <span class="app-icon">📱</span>
          <span class="app-name">翼支付 App</span>
          <svg class="chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </div>
        <button class="add-folder-btn" title="新建文件夹">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
      </div>

      <div class="tree-container">
        <div 
          v-for="node in treeData" 
          :key="node.id"
          class="tree-node"
          :class="{ 'active': activeNode === node.id }"
          :style="{ paddingLeft: (node.level * 18 + 16) + 'px' }"
          @click="handleNodeClick(node)"
        >
          <div class="arrow-box" :class="{ 'expanded': node.expanded, 'hidden': !node.hasChildren }">
             <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </div>
          <div class="folder-icon">
             <svg v-if="node.expanded" width="18" height="18" viewBox="0 0 24 24" fill="#3b82f6" stroke="currentColor" stroke-width="0"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
             <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="#93c5fd" stroke="currentColor" stroke-width="0"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
          </div>
          <span class="node-name">{{ node.name }}</span>
          <span class="node-count" v-if="node.count">{{ node.count }}</span>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="trash-bin">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          回收站
        </div>
      </div>
    </aside>

    <main class="content-area">
      <div class="big-white-card">
        
        <header class="card-header">
          <div class="header-left">
            <h2 class="section-title">Script Management</h2>
            <div class="breadcrumb">
              <span>All Scripts</span>
              <span class="sep">/</span>
              <span class="current">Login Module</span>
            </div>
          </div>
          
          <div class="header-controls">
            <div class="control-group">
              <span class="label">Showing</span>
              <select class="select-box">
                <option>10</option>
                <option>20</option>
                <option>50</option>
              </select>
            </div>
            
            <button class="tool-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
              Filter
            </button>
            <button class="tool-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
              Export
            </button>
            <button class="primary-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
              New Script
            </button>
          </div>
        </header>

        <div class="unified-table-wrapper">
          <div class="grid-header">
            <div class="th col-name">Script Name</div>
            <div class="th col-id">ID</div>
            <div class="th col-type">Type</div>
            <div class="th col-platform">Platform</div>
            <div class="th col-author">Author</div>
            <div class="th col-status">Status</div>
            <div class="th col-action">Action</div>
          </div>

          <div class="grid-body">
            <div 
              class="grid-row" 
              v-for="script in scripts" 
              :key="script.id"
            >
              <div class="td col-name">
                <div class="icon-thumb">TS</div>
                <div class="name-text">
                  <div class="main-text">{{ script.name }}</div>
                  <div class="sub-text">Updated {{ script.updated }}</div>
                </div>
              </div>

              <div class="td col-id">#{{ script.code }}</div>
              
              <div class="td col-type">{{ script.type }}</div>

              <div class="td col-platform">
                <span class="badge" :class="script.platform.toLowerCase()">{{ script.platform }}</span>
              </div>

              <div class="td col-author">
                <img :src="script.avatar" class="avatar">
                <span>{{ script.author }}</span>
              </div>

              <div class="td col-status">
                <span class="status-pill" :class="script.status.toLowerCase()">
                  {{ script.status }}
                </span>
              </div>

              <div class="td col-action">
                <button class="dots-btn">•••</button>
              </div>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <button class="page-nav prev">Previous</button>
          <div class="page-numbers">
            <span class="num active">1</span>
            <span class="num">2</span>
            <span class="num">3</span>
            <span class="dots">...</span>
            <span class="num">10</span>
          </div>
          <button class="page-nav next">Next</button>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const activeNode = ref('2');

// 文件夹目录树数据
const treeData = ref([
  { id: '1', name: '全量回归测试', level: 0, expanded: true, hasChildren: true, count: 56 },
  { id: '2', name: '登录注册模块', level: 1, expanded: false, hasChildren: false, count: 12 },
  { id: '3', name: '个人中心', level: 1, expanded: false, hasChildren: true, count: 8 },
  { id: '4', name: '营销活动页', level: 0, expanded: false, hasChildren: true, count: 15 },
]);

// 脚本列表数据
const scripts = ref([
  { id: 1, name: 'Login_Flow_Main', code: '827364', type: 'UI', platform: 'Android', author: 'Felix', status: 'Active', updated: '2h ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix' },
  { id: 2, name: 'Payment_Wechat', code: '293847', type: 'API', platform: 'Backend', author: 'Ana', status: 'Pending', updated: '1d ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ana' },
  { id: 3, name: 'UserProfile_Edit', code: '938471', type: 'UI', platform: 'iOS', author: 'Bob', status: 'Failed', updated: '3d ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob' },
  { id: 4, name: 'Home_Banner_Click', code: '102938', type: 'UI', platform: 'Android', author: 'Felix', status: 'Inactive', updated: '1w ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix' },
  { id: 5, name: 'Search_Function', code: '556123', type: 'UI', platform: 'Web', author: 'Sarah', status: 'Active', updated: '5h ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah' },
  { id: 6, name: 'Cart_Add_Remove', code: '662190', type: 'UI', platform: 'iOS', author: 'Mike', status: 'Active', updated: '10m ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mike' },
  { id: 7, name: 'Settings_Logout', code: '991230', type: 'UI', platform: 'Android', author: 'Bob', status: 'Pending', updated: '2d ago', avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Bob' },
]);

const handleNodeClick = (node) => {
  activeNode.value = node.id;
  if(node.hasChildren) node.expanded = !node.expanded;
};
</script>

<style scoped>
/* 容器 */
.script-manager-unified {
  display: flex;
  height: 100vh;
  background-color: #F8FAFC; /* 页面背景：极淡的灰 */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
  padding: 20px;
  gap: 20px;
  box-sizing: border-box;
}

/* --- LEFT SIDEBAR (文件夹风格) --- */
.sidebar-tree {
  width: 260px;
  background: white;
  border-radius: 20px; /* 圆角 */
  display: flex; flex-direction: column;
  padding: 20px 0;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}

.sidebar-header {
  padding: 0 20px 20px 20px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #f1f5f9; margin-bottom: 12px;
}
.app-selector { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; color: #0f172a; cursor: pointer; }
.app-icon { font-size: 18px; }
.add-folder-btn {
  background: #eff6ff; color: #3b82f6; border: none; width: 28px; height: 28px;
  border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer;
}

.tree-container { flex: 1; overflow-y: auto; padding: 0 12px; }
.tree-node {
  display: flex; align-items: center; height: 40px; margin-bottom: 2px;
  border-radius: 8px; cursor: pointer; color: #64748b; font-size: 14px;
  transition: all 0.2s; user-select: none;
}
.tree-node:hover { background: #f8fafc; color: #1e293b; }
.tree-node.active { background: #eff6ff; color: #2563eb; font-weight: 600; }

.arrow-box { width: 16px; display: flex; justify-content: center; color: #cbd5e1; transition: transform 0.2s; }
.arrow-box.expanded { transform: rotate(90deg); }
.arrow-box.hidden { opacity: 0; }
.folder-icon { margin-right: 8px; display: flex; align-items: center; }
.node-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-count { font-size: 11px; background: #f1f5f9; padding: 2px 6px; border-radius: 10px; color: #94a3b8; }
.tree-node.active .node-count { background: #dbeafe; color: #3b82f6; }

.sidebar-footer { padding: 16px 20px 0 20px; border-top: 1px solid #f1f5f9; }
.trash-bin { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #64748b; cursor: pointer; }

/* --- RIGHT CONTENT (大白卡片) --- */
.content-area {
  flex: 1;
  display: flex;
  overflow: hidden; /* 防止出现双滚动条 */
}

.big-white-card {
  flex: 1;
  background: white;
  border-radius: 24px; /* 统一的大卡片圆角 */
  display: flex; flex-direction: column;
  box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
  padding: 32px;
  overflow: hidden;
}

/* 1. Header */
.card-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 24px; flex-shrink: 0;
}
.section-title { font-size: 26px; font-weight: 800; color: #0f172a; margin: 0 0 8px 0; }
.breadcrumb { font-size: 14px; color: #64748b; display: flex; gap: 8px; }
.breadcrumb .current { color: #3b82f6; font-weight: 500; }

.header-controls { display: flex; gap: 12px; align-items: center; }
.control-group { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #64748b; margin-right: 12px; }
.select-box {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 4px 8px; color: #0f172a; font-weight: 600; outline: none; cursor: pointer;
}
.tool-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; background: white; border: 1px solid #e2e8f0;
  border-radius: 12px; font-weight: 600; color: #475569; cursor: pointer;
  transition: all 0.2s;
}
.tool-btn:hover { background: #f8fafc; border-color: #cbd5e1; }

.primary-btn {
  padding: 10px 24px; background: #3b82f6; color: white; border: none;
  border-radius: 12px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; gap: 8px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  transition: transform 0.1s;
}
.primary-btn:hover { background: #2563eb; transform: translateY(-1px); }

/* 2. Unified Table (CSS Grid) */
.unified-table-wrapper {
  flex: 1;
  display: flex; flex-direction: column;
  overflow: hidden; /* 让表格体可以滚动 */
}

/* 网格定义: Name | ID | Type | Platform | Author | Status | Action */
.grid-header, .grid-row {
  display: grid;
  grid-template-columns: 2.5fr 1fr 1fr 1fr 1.5fr 1.2fr 80px;
  gap: 16px;
  padding: 0 16px;
  align-items: center;
}

/* Header */
.grid-header {
  height: 48px;
  border-bottom: 2px solid #f1f5f9; /* 表头分割线稍粗 */
  flex-shrink: 0;
}
.th { font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
.col-action { text-align: right; }

/* Body */
.grid-body {
  overflow-y: auto;
  flex: 1;
}
.grid-row {
  height: 72px; /* 舒适的行高 */
  border-bottom: 1px solid #f1f5f9; /* 极细的分割线 */
  transition: background 0.2s;
}
.grid-row:hover { background: #f8fafc; }
.grid-row:last-child { border-bottom: none; }

/* Columns */
.col-name { display: flex; align-items: center; gap: 16px; }
.icon-thumb {
  width: 36px; height: 36px; background: #f1f5f9; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; color: #64748b;
}
.name-text { display: flex; flex-direction: column; gap: 2px; }
.main-text { font-weight: 700; font-size: 14px; color: #0f172a; }
.sub-text { font-size: 12px; color: #94a3b8; }

.col-id, .col-type { font-size: 13px; color: #64748b; font-family: monospace; }
.col-type { font-family: sans-serif; font-weight: 500; }

.col-platform .badge {
  font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 600;
  border: 1px solid transparent;
}
.badge.android { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.badge.ios { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }
.badge.backend { background: #e0e7ff; color: #4338ca; border-color: #c7d2fe; }

.col-author { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; color: #334155; }
.avatar { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; }

/* Candy Pills */
.status-pill {
  padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: 700; display: inline-block; text-align: center; min-width: 70px;
}
.active { background: #dcfce7; color: #15803d; }
.pending { background: #ffedd5; color: #c2410c; }
.failed { background: #fee2e2; color: #b91c1c; }
.inactive { background: #f1f5f9; color: #94a3b8; }

.dots-btn {
  background: transparent; border: none; font-size: 18px; color: #cbd5e1; cursor: pointer; padding: 4px;
}
.dots-btn:hover { color: #64748b; }

/* 3. Pagination Footer */
.card-footer {
  margin-top: auto; /* 沉底 */
  padding-top: 24px; border-top: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 500; color: #64748b;
  flex-shrink: 0;
}
.page-nav { background: transparent; border: none; cursor: pointer; color: #64748b; font-weight: 500; transition: color 0.2s; }
.page-nav:hover { color: #3b82f6; }

.page-numbers { display: flex; gap: 8px; }
.num {
  width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; cursor: pointer; transition: all 0.2s;
}
.num.active { background: #3b82f6; color: white; box-shadow: 0 4px 10px rgba(59,130,246,0.3); }
.num:hover:not(.active) { background: #f1f5f9; color: #0f172a; }
</style>