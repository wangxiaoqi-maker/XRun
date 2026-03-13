<template>
  <div class="test-chat-container">
    
    <div class="header-tabs">
      <div class="tabs-left">
        <div class="tab active"><span class="icon">📋</span> 任务</div>
        <div class="tab inactive"><span class="icon">🕒</span> 历史会话</div>
      </div>
      <button class="close-btn">✕</button>
    </div>

    <div class="control-bar">
      <select class="modern-select"><option>DeepSeek Chat</option></select>
      <select class="modern-select"><option>gpt-5.3-codex</option></select>
      <select class="modern-select"><option>目录</option></select>
      <div class="skills-badge">⚙ Skills <span class="badge-count">1</span></div>
    </div>

    <div class="context-tags">
      <div class="tag">帮我生成登录功... <span class="close-tag">✕</span></div>
      <div class="tag active">帮我生成登录功... <span class="close-tag">✕</span></div>
      <button class="add-tag-btn">+</button>
    </div>

    <div class="chat-content">
      
      <div class="strategy-container">
        
        <div class="strategy-card">
          <div class="card-header">
            <span class="icon-gear">⚙</span>
            <div class="card-title"><span class="icon-bug">🐛</span> 错误推测</div>
          </div>
          <div class="card-body">基于经验推测可能出错的场景</div>
        </div>

        <div class="strategy-card">
          <div class="card-header">
            <span class="icon-gear">⚙</span>
            <div class="card-title"><span class="icon-table">📋</span> 判定表法</div>
          </div>
          <div class="card-body">列出所有条件和动作，分析条件组合</div>
        </div>

        <div class="strategy-card">
          <div class="card-header">
            <span class="icon-gear">⚙</span>
            <div class="card-title"><span class="icon-flow">🔀</span> 状态迁移法</div>
          </div>
          <div class="card-body">识别所有状态和转换条件</div>
        </div>

      </div>

      <div class="ai-response-group">
        <div class="avatar">A</div>
        <div class="progress-list">
          
          <div class="progress-item">
            <div class="item-text"><span class="dot"></span>共 30 个测试点，分 5 批并行生成</div>
            <div class="percent-badge">5%</div>
          </div>

          <div class="progress-item">
            <div class="item-text"><span class="dot"></span>第 1/5 批: TP-001, TP-002, TP-003, TP-004, TP-005, TP-006</div>
            <div class="percent-badge">5%</div>
          </div>

          <div class="progress-item">
            <div class="item-text"><span class="dot"></span>第 2/5 批: TP-007, TP-008, TP-009, TP-010, TP-011, TP-012</div>
            <div class="percent-badge highlight">19%</div>
          </div>

          <div class="progress-item">
            <div class="item-text"><span class="dot"></span>第 3/5 批: TP-013, TP-014, TP-015, TP-016, TP-017, TP-018</div>
            <div class="percent-badge highlight">33%</div>
          </div>

        </div>
      </div>

    </div>

    <div class="bottom-input-area">
      <div class="input-wrapper">
        <div class="action-buttons">
          <button class="tool-btn">+</button>
          <button class="tool-btn">📎</button>
        </div>
        <input type="text" placeholder="和我对话，或描述测试需求..." class="main-input" />
        <button class="stop-btn">■</button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 基础容器 */
.test-chat-container {
  display: flex;
  flex-direction: column;
  height: 800px; /* 示意高度 */
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

/* 1. 顶部 Tabs */
.header-tabs {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.tabs-left { display: flex; gap: 8px; }
.tab {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.tab.active { background: #ede9fe; color: #6d28d9; }
.tab.inactive { color: #64748b; }
.close-btn { background: none; border: none; font-size: 16px; color: #94a3b8; cursor: pointer; }

/* 2. 控制栏 */
.control-bar {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: #ffffff;
  border-bottom: 1px solid #f1f5f9;
  align-items: center;
}
.modern-select {
  padding: 6px 28px 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  color: #334155;
  font-size: 13px;
  appearance: none; /* 需要配合自定义箭头背景图，这里简化 */
  outline: none;
}
.skills-badge {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6d28d9;
  font-size: 13px;
  font-weight: 600;
  padding: 4px 10px;
  border: 1px solid #ede9fe;
  border-radius: 12px;
  background: #f5f3ff;
}
.badge-count { background: #6d28d9; color: white; border-radius: 50%; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; font-size: 11px; }

/* 3. 上下文标签 */
.context-tags {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}
.tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
}
.tag.active { border-color: #818cf8; color: #4f46e5; font-weight: 500; box-shadow: 0 1px 2px rgba(79, 70, 229, 0.1); }
.close-tag { color: #cbd5e1; }
.add-tag-btn { background: none; border: 1px dashed #cbd5e1; border-radius: 6px; width: 30px; color: #64748b; cursor: pointer; }

/* 4. 聊天内容区 */
.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #ffffff;
}

/* 策略容器 (替代原黑框外层) */
.strategy-container {
  background: #fbfbfe;
  border: 1px solid #ede9fe;
  border-radius: 12px;
  padding: 16px;
  margin-left: 48px; /* 对齐头像右侧 */
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.strategy-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  transition: all 0.2s;
}
.strategy-card:hover { border-color: #c4b5fd; box-shadow: 0 2px 6px rgba(109, 40, 217, 0.08); }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.icon-gear { color: #94a3b8; font-size: 14px; }
.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #6d28d9;
}
.card-body {
  background: #f8fafc; /* 浅灰替代纯黑 */
  color: #334155;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  border-left: 3px solid #8b5cf6; /* 左侧紫色高亮条 */
}

/* AI 回复与进度列表 */
.ai-response-group {
  display: flex;
  gap: 16px;
}
.avatar {
  width: 32px;
  height: 32px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}
.progress-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 6px;
}
.progress-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}
.item-text {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #334155;
  font-size: 14px;
  line-height: 1.5;
}
.dot {
  margin-top: 6px;
  width: 6px;
  height: 6px;
  background: #8b5cf6;
  border-radius: 50%;
  flex-shrink: 0;
}
.percent-badge {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  background: #eff6ff;
  padding: 4px 8px;
  border-radius: 6px;
}
.percent-badge.highlight {
  background: #dbeafe;
  color: #2563eb;
}

/* 5. 底部输入区 */
.bottom-input-area {
  padding: 20px;
  background: #ffffff;
  border-top: 1px solid #f1f5f9;
}
.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.02);
  transition: border-color 0.2s;
}
.input-wrapper:focus-within {
  border-color: #93c5fd;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.action-buttons {
  display: flex;
  gap: 8px;
}
.tool-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.tool-btn:hover { background: #e2e8f0; color: #334155; }
.main-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: #0f172a;
  padding: 8px 0;
}
.main-input::placeholder { color: #94a3b8; }
.stop-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
  transition: background 0.2s;
}
.stop-btn:hover { background: #dc2626; }
</style>