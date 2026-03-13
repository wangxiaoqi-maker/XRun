<template>
  <div class="tcg-layout">

    <!-- ======== 左侧栏：目录树 ======== -->
    <aside class="sidebar">
      <div class="project-header">
        <el-dropdown trigger="click" @command="handleProjectCommand" max-height="300px" style="width: 100%;">
          <div class="proj-select">
            <div class="proj-icon">📦</div>
            <div class="proj-info">
              <div class="proj-name">{{ currentProject?.name || '选择项目' }}</div>
            </div>
            <span class="proj-arrow">▼</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="__create__" divided>
                <span style="color: #6366f1; font-weight: 500;">+ 新建项目</span>
              </el-dropdown-item>
              <el-dropdown-item v-for="p in projects" :key="p.id" :command="p.id"
                :class="{ 'is-active': currentProject?.id === p.id }">📦 {{ p.name }}</el-dropdown-item>
              <el-dropdown-item v-if="projects.length === 0" disabled>暂无项目</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="search-box">
        <input type="text" v-model="treeSearch" placeholder="搜索目录或用例..." />
      </div>

      <div class="module-tree">
        <div class="tree-header">
          <span>用例目录</span>
          <button class="add-root-btn" title="新建根目录" @click="startAddModule(null)">+</button>
        </div>
        <template v-if="currentProject">
          <template v-for="node in filteredTree" :key="node.id">
            <div class="tree-node-folder" :class="{ active: activeModuleId === node.id }"
              @click="onSelectModule(node)">
              <span class="node-indent" :style="{ width: '0px' }"></span>
              <span class="node-arrow" :class="{ open: isNodeOpen(node.id) }" @click.stop="toggleTreeNode(node.id)">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><path d="M3 2l4 3-4 3z"/></svg>
              </span>
              <span class="node-icon">{{ isNodeOpen(node.id) ? '📂' : '📁' }}</span>
              <span class="node-name">{{ node.name }}</span>
              <span class="node-count">{{ node.caseCount || 0 }}</span>
              <span v-if="node.id !== '__uncategorized__'" class="node-actions">
                <span class="na-add" title="添加子目录" @click.stop="startAddModule(node)">+</span>
                <span class="na-del" title="删除" @click.stop="handleDeleteModule(node)">×</span>
              </span>
            </div>
            <template v-if="isNodeOpen(node.id)">
              <template v-for="child in (node.children || [])" :key="child.id">
                <div class="tree-node-folder" :class="{ active: activeModuleId === child.id }"
                  @click="onSelectModule(child)">
                  <span class="node-indent" :style="{ width: '16px' }"></span>
                  <span class="node-arrow" :class="{ open: isNodeOpen(child.id) }" @click.stop="toggleTreeNode(child.id)">
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><path d="M3 2l4 3-4 3z"/></svg>
                  </span>
                  <span class="node-icon">{{ isNodeOpen(child.id) ? '📂' : '📁' }}</span>
                  <span class="node-name">{{ child.name }}</span>
                  <span class="node-count">{{ child.caseCount || 0 }}</span>
                  <span class="node-actions">
                    <span class="na-add" title="添加子目录" @click.stop="startAddModule(child)">+</span>
                    <span class="na-del" title="删除" @click.stop="handleDeleteModule(child)">×</span>
                  </span>
                </div>
                <template v-if="isNodeOpen(child.id)">
                  <template v-for="sub in (child.children || [])" :key="sub.id">
                    <div class="tree-node-folder" :class="{ active: activeModuleId === sub.id }"
                      @click="onSelectModule(sub)">
                      <span class="node-indent" :style="{ width: '32px' }"></span>
                      <span class="node-arrow" :class="{ open: isNodeOpen(sub.id) }" @click.stop="toggleTreeNode(sub.id)">
                        <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor"><path d="M3 2l4 3-4 3z"/></svg>
                      </span>
                      <span class="node-icon">{{ isNodeOpen(sub.id) ? '📂' : '📁' }}</span>
                      <span class="node-name">{{ sub.name }}</span>
                      <span class="node-count">{{ sub.caseCount || 0 }}</span>
                      <span class="node-actions">
                        <span class="na-del" title="删除" @click.stop="handleDeleteModule(sub)">×</span>
                      </span>
                    </div>
                  </template>
                  <div v-for="c in (child.cases || [])" :key="c.id" class="tree-node-case"
                    :class="{ active: selectedCase?.id === c.id }" @click="selectedCase = c">
                    <span class="node-indent" :style="{ width: '40px' }"></span>
                    <span class="node-icon">📄</span>
                    <span class="node-name">{{ c.name }}</span>
                  </div>
                </template>
              </template>
              <div v-for="c in (node.cases || [])" :key="c.id" class="tree-node-case"
                :class="{ active: selectedCase?.id === c.id }" @click="selectedCase = c">
                <span class="node-indent" :style="{ width: '24px' }"></span>
                <span class="node-icon">📄</span>
                <span class="node-name">{{ c.name }}</span>
              </div>
            </template>
          </template>
          <div v-if="filteredTree.length === 0 && !addingModule" class="tree-empty">暂无目录，点击 + 创建</div>
          <div v-if="addingModule" class="add-module-row" :style="{ paddingLeft: (addingParentDepth * 20 + 12) + 'px' }">
            <input ref="moduleInputRef" v-model="newModuleName" placeholder="输入目录名称"
              class="add-module-input" @keydown.enter.prevent="confirmAddModule" @keydown.escape="cancelAddModule" @blur="onModuleInputBlur" />
          </div>
        </template>
        <div v-else class="tree-empty">请先选择或创建项目</div>
      </div>
    </aside>

    <!-- ======== 主工作区：用例表格 ======== -->
    <main class="main-workspace">
      <header class="ws-header">
        <div class="breadcrumb">
          <span v-if="currentProject">{{ currentProject.name }}</span>
          <template v-if="breadcrumbPath.length">
            <span v-for="b in breadcrumbPath" :key="b.id"> / {{ b.name }}</span>
          </template>
        </div>
        <button class="ai-toggle-btn" :class="{ 'is-open': copilotOpen }" @click="copilotOpen = !copilotOpen">
          ✨ {{ copilotOpen ? '收起 Copilot' : '唤出 Copilot' }}
        </button>
      </header>

      <div class="toolbar">
        <div class="actions-left">
          <button class="btn-outline" @click="openExportDialog">📥 导出</button>
          <button v-if="hasSelected" class="btn-danger" @click="batchDeleteCases">🗑️ 批量删除 ({{ selectedIds.size }})</button>
        </div>
        <div class="actions-right">
          <span class="kb-stat" v-if="kbStats.total > 0" title="知识库已索引的向量数">📚 {{ kbStats.doc_chunks }} 文档块 · {{ kbStats.case_vectors }} 用例</span>
          <button class="btn-outline btn-sm" @click="rebuildKnowledgeBase" :disabled="kbRebuilding" title="重建知识库">
            {{ kbRebuilding ? '重建中...' : '🔄 重建知识库' }}
          </button>
          <span>用例总数: {{ filteredCases.length }}</span>
        </div>
      </div>

      <div class="table-container">
        <table v-if="filteredCases.length > 0" class="case-table">
          <thead>
            <tr>
              <th width="40">
                <input type="checkbox" :checked="allSelected" @change="toggleSelectAll">
              </th>
              <th width="70">编号</th>
              <th width="200">用例名称</th>
              <th width="100">模块</th>
              <th width="60">优先级</th>
              <th width="150">前置条件</th>
              <th width="80">创建人</th>
              <th width="80">状态</th>
              <th width="120">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in filteredCases" :key="c.id" :class="{ 'row-active': selectedCase?.id === c.id }"
              @click="selectedCase = c">
              <td><input type="checkbox" :checked="selectedIds.has(c.id)" @click.stop @change="toggleSelect(c.id)"></td>
              <td class="id-text">{{ c.case_no }}</td>
              <td class="name-text" :title="c.name">
                <span class="case-name-cell">{{ c.name }}</span>
                <button v-if="c.test_steps?.length" class="expand-btn" @click.stop="toggleExpandCase(c.id)">
                  {{ expandedCaseIds.has(c.id) ? '收起' : `步骤(${c.test_steps.length})` }}
                </button>
              </td>
              <td class="module-text">{{ c.module_name || '—' }}</td>
              <td><span class="priority" :class="c.priority">{{ c.priority }}</span></td>
              <td class="precondition-cell" :title="c.preconditions">
                {{ c.preconditions ? (c.preconditions.length > 30 ? c.preconditions.slice(0, 30) + '...' : c.preconditions) : '—' }}
              </td>
              <td class="creator-text">{{ c.creator || '—' }}</td>
              <td><span class="status-badge" :class="c.review_status">{{ statusLabel(c.review_status) }}</span></td>
              <td class="ops-cell">
                <button class="op-btn" title="执行" @click.stop="executeCase(c)">▶️</button>
                <button class="op-btn" title="编辑" @click.stop="editCase(c)">✏️</button>
                <button class="op-btn" title="删除" @click.stop="deleteCase(c)">🗑️</button>
              </td>
            </tr>
            <tr v-for="c in filteredCases.filter(tc => tc.test_steps?.length && expandedCaseIds.has(tc.id))" :key="c.id + '_expanded'" class="expanded-row">
              <td colspan="9">
                <div class="expanded-content">
                  <div class="expanded-section">
                    <div class="section-title">测试步骤</div>
                    <div class="steps-list">
                      <div v-for="s in c.test_steps" :key="s.step" class="step-item">
                        <span class="step-num">{{ s.step }}.</span>
                        <span class="step-action">{{ s.action }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="expanded-section">
                    <div class="section-title">预期结果</div>
                    <div class="expect-list">
                      <div v-for="s in c.test_steps" :key="s.step" class="expect-item">
                        <span class="step-num">{{ s.step }}.</span>
                        <span class="step-expected">{{ s.expected }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty-table">
          <div class="empty-icon">📋</div>
          <p>暂无用例</p>
          <p class="empty-hint">在右侧 Copilot 对话中输入需求开始生成</p>
        </div>
      </div>
    </main>

    <!-- ======== 右侧 Copilot（核心交互区）======== -->
    <transition name="slide">
      <aside v-show="copilotOpen" class="ai-drawer">
        <!-- 头部 -->
        <div class="drawer-header">
          <div class="drawer-title-area">
            <span class="drawer-title">{{ conversations.find(c => c.id === currentConvId)?.title || 'X-Run 助手' }}</span>
          </div>
          <div class="drawer-header-actions">
            <button class="header-icon-btn" :class="{ active: drawerTab === 'history' }" @click="drawerTab = drawerTab === 'history' ? 'task' : 'history'" title="历史会话">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 107 7A7 7 0 008 1zm0 12.5A5.5 5.5 0 1113.5 8 5.51 5.51 0 018 13.5zM8.5 4v4.25l3.5 2.08-.75 1.23L7.25 9V4z"/></svg>
            </button>
            <button class="header-icon-btn" @click="copilotOpen = false" title="关闭">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4l8 8M12 4l-8 8"/></svg>
            </button>
          </div>
        </div>

        <!-- 配置栏 -->
        <div v-show="drawerTab === 'task'" class="config-bar">
          <el-select v-model="genConfig.textModelId" placeholder="模型" size="small" class="cfg-select" @change="syncConvConfig">
            <el-option v-for="m in allModels.filter(x => x.model_type === 'chat')" :key="m.id" :value="m.id" :label="m.name">
              <span>{{ m.name }}</span>
              <span style="float:right;color:#94a3b8;font-size:11px">{{ m.provider?.name }}</span>
            </el-option>
          </el-select>
          <el-select v-model="genConfig.visionModelId" placeholder="视觉模型" clearable size="small" class="cfg-select" @change="syncConvConfig">
            <el-option v-for="m in visionModels" :key="m.id" :value="m.id" :label="m.name" />
          </el-select>
          <el-select v-model="genConfig.moduleName" placeholder="目录" clearable filterable allow-create
            default-first-option size="small" class="cfg-select" @change="syncConvConfig">
            <el-option v-for="m in flatModuleOptions" :key="m.id" :value="m.name" :label="m.fullPath" />
          </el-select>
          <el-popover placement="bottom-start" :width="280" trigger="click">
            <template #reference>
              <button class="skills-toggle" title="Skills">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/></svg>
                Skills <span class="skills-count">{{ enabledSkills.length }}</span>
              </button>
            </template>
            <div class="skills-popover">
              <div class="skills-pop-title">已启用 Skills</div>
              <div v-for="s in enabledSkills" :key="s.key" class="skill-info-item">
                <span>{{ s.icon || '📋' }} {{ s.name }}</span>
                <el-tag size="small" type="info">{{ s.category || 'general' }}</el-tag>
              </div>
              <div v-if="!enabledSkills.length" class="skills-empty">暂无已启用的 Skills</div>
              <div class="skills-pop-footer">
                <router-link to="/skills" class="skills-manage-link">管理 Skills</router-link>
              </div>
            </div>
          </el-popover>
        </div>

        <!-- ======== 历史会话面板 ======== -->
        <div v-if="drawerTab === 'history'" class="history-panel">
          <div class="history-header">
            <span class="history-count">{{ conversations.length }} 个会话</span>
            <button class="history-new-btn" @click="createNewConversation(); drawerTab = 'task'">+ 新建</button>
          </div>
          <div class="history-list">
            <div v-if="conversations.length === 0" class="history-empty">
              <p>暂无会话</p>
              <button class="history-start-btn" @click="createNewConversation(); drawerTab = 'task'">开始新对话</button>
            </div>
            <div
              v-for="conv in conversations"
              :key="conv.id"
              class="history-card"
              :class="{ active: currentConvId === conv.id }"
              @click="switchConversation(conv.id); drawerTab = 'task'"
            >
              <div class="hcard-body">
                <span class="hcard-title">{{ convTitle(conv) }}</span>
                <span class="hcard-time">{{ formatConvTime(conv.created_at) }}</span>
              </div>
              <button class="hcard-del" @click.stop="handleDeleteConversation(conv.id)" title="删除">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor" opacity="0.4"><path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H6a1 1 0 011-1h2a1 1 0 011 1h3.5a1 1 0 011 1v1zM4.118 4L4 4.059V13a1 1 0 001 1h6a1 1 0 001-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 对话区 -->
        <ChatMessageList
          v-show="drawerTab === 'task'"
          ref="chatListRef"
          :messages="chatMessages"
          :generating="generating"
          :config="genConfig"
          :module-options="flatModuleOptions"
          :confirmed-point-ids="confirmedPointIds"
          :editing-point="editingPoint"
          @hint="handleInputSend($event)"
          @upload="triggerUpload"
          @new-conversation="createNewConversation"
          @start-generation="handleStartGeneration"
          @update:config="Object.assign(genConfig, $event)"
          @toggle-point="toggleTestPoint"
          @confirm-points="confirmTestPoints"
          @select-all-points="selectAllTestPoints"
          @add-point="addTestPoint"
          @edit-point="editTestPoint"
          @delete-point="deleteTestPoint"
          @supplement="supplementAndReanalyze"
          @save-edit-point="saveEditPoint"
          @cancel-edit-point="cancelEditPoint"
          @update:editingPoint="editingPoint = $event"
          @set-review-status="setReviewStatus"
          @approve-all="batchApproveAll"
          @submit-review="submitReview"
          @save-cases="submitReviewAndSave"
          @regenerate="submitSupplementRegenerate"
          @action-confirm="handleActionConfirm"
        />

        <!-- 底部输入区 -->
        <ChatInputBar
          v-show="drawerTab === 'task'"
          ref="chatInputRef"
          :generating="generating"
          :pending-files="pendingFiles"
          @send="handleInputSend"
          @cancel="handleCancelGeneration"
          @upload="triggerUpload"
          @remove-file="removePendingFile"
          @files-selected="onFilesSelected"
        />
      </aside>
    </transition>

    <!-- 创建项目弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建项目" width="440px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="项目名称" required>
          <el-input v-model="createForm.name" placeholder="输入项目名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="项目描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateProject" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 执行用例弹窗 -->
    <el-dialog v-model="showExecuteDialog" title="执行用例" width="780px" destroy-on-close top="4vh">
      <div v-if="caseDetail" class="execute-detail">
        <!-- 用例信息 -->
        <div class="detail-header">
          <div class="detail-title">{{ caseDetail.name }}</div>
          <div class="detail-meta">
            <span class="meta-item">编号: {{ caseDetail.case_no }}</span>
            <span class="meta-item">优先级: <span class="priority" :class="caseDetail.priority">{{ caseDetail.priority }}</span></span>
            <span class="meta-item">模块: {{ caseDetail.module_name || '—' }}</span>
          </div>
        </div>
        <div v-if="caseDetail.preconditions" class="detail-section">
          <div class="section-label">前置条件</div>
          <div class="section-content">{{ caseDetail.preconditions }}</div>
        </div>

        <!-- 步骤列表 + 执行状态 -->
        <div class="detail-section">
          <div class="section-label">测试步骤</div>
          <div class="exec-steps-table">
            <div class="exec-step-header">
              <span class="es-col-num">#</span>
              <span class="es-col-action">操作</span>
              <span class="es-col-expected">预期结果</span>
              <span class="es-col-status">结果</span>
            </div>
            <div 
              v-for="(s, idx) in caseDetail.test_steps" 
              :key="s.step" 
              class="exec-step-row"
              :class="{ 
                'is-current': currentExecution && !isExecutionFinished() && idx === currentStepIndex,
                'is-passed': getStepStatus(s.step) === 'passed',
                'is-failed': getStepStatus(s.step) === 'failed',
                'is-blocked': getStepStatus(s.step) === 'blocked',
              }"
            >
              <span class="es-col-num">{{ s.step }}</span>
              <span class="es-col-action">{{ s.action }}</span>
              <span class="es-col-expected">{{ s.expected }}</span>
              <span class="es-col-status">
                <span v-if="getStepStatus(s.step) === 'passed'" class="exec-badge pass">通过</span>
                <span v-else-if="getStepStatus(s.step) === 'failed'" class="exec-badge fail">失败</span>
                <span v-else-if="getStepStatus(s.step) === 'blocked'" class="exec-badge block">阻塞</span>
                <span v-else class="exec-badge pending">待验证</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 当前步骤操作区（执行中时显示） -->
        <div v-if="currentExecution && !isExecutionFinished()" class="exec-action-area">
          <div class="exec-current-label">
            当前步骤 {{ currentStepIndex + 1 }} / {{ caseDetail.test_steps?.length || 0 }}
          </div>
          <div class="exec-current-step">
            <div class="ecs-action"><strong>操作:</strong> {{ caseDetail.test_steps?.[currentStepIndex]?.action }}</div>
            <div class="ecs-expected"><strong>预期:</strong> {{ caseDetail.test_steps?.[currentStepIndex]?.expected }}</div>
          </div>
          <el-input v-model="actualResultInput" placeholder="实际结果（可选）" size="small" style="margin-bottom: 8px;" />
          <el-input v-model="stepRemarkInput" placeholder="备注（失败时建议填写）" size="small" style="margin-bottom: 12px;" />
          <div class="exec-step-btns">
            <el-button type="success" @click="submitStepResult('passed')" :loading="submittingStep" size="default">✓ 通过</el-button>
            <el-button type="danger" @click="submitStepResult('failed')" :loading="submittingStep" size="default">✗ 失败</el-button>
            <el-button @click="submitStepResult('blocked')" :loading="submittingStep" size="default">⊘ 阻塞</el-button>
          </div>
        </div>

        <!-- 执行结果概要 -->
        <div v-if="isExecutionFinished()" class="exec-result-summary">
          <div class="ers-title" :class="currentExecution.status">
            {{ currentExecution.status === 'passed' ? '✅ 用例通过' : '❌ 用例失败' }}
          </div>
          <div class="ers-stats">
            <span class="ers-stat pass">通过 {{ currentExecution.passed_steps }}</span>
            <span class="ers-stat fail">失败 {{ currentExecution.failed_steps }}</span>
            <span class="ers-stat block">阻塞 {{ currentExecution.blocked_steps }}</span>
          </div>
        </div>

        <!-- 历史执行记录 -->
        <div class="detail-section" v-if="executionHistory.length > 0">
          <div class="section-label">历史执行 ({{ executionHistory.length }})</div>
          <div class="exec-history-list">
            <div v-for="h in executionHistory" :key="h.id" class="exec-history-item">
              <span class="eh-status" :class="h.status">{{ h.status === 'passed' ? '通过' : h.status === 'failed' ? '失败' : '进行中' }}</span>
              <span class="eh-executor">{{ h.executor }}</span>
              <span class="eh-time">{{ formatExecTime(h.started_at) }}</span>
              <span class="eh-stats">{{ h.passed_steps }}/{{ h.total_steps }} 步通过</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="loading-detail">加载中...</div>
      <template #footer>
        <el-button @click="showExecuteDialog = false">关闭</el-button>
        <el-button v-if="!currentExecution" type="primary" @click="startExecution" :disabled="!caseDetail">开始执行</el-button>
      </template>
    </el-dialog>

    <!-- 导出用例弹窗 -->
    <el-dialog v-model="showExportDialog" title="导出测试用例" width="500px" destroy-on-close>
      <div class="export-options">
        <el-form label-position="top">
          <el-form-item label="导出模板">
            <el-select v-model="selectedExportTemplate" placeholder="选择导出模板" style="width: 100%;">
              <el-option label="默认模板（编号、名称、模块、优先级、类型、前置条件、创建人、时间）" :value="null" />
              <el-option v-for="t in exportTemplates" :key="t.id" :label="t.name" :value="t.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="导出范围">
            <div class="export-range">
              <el-tag v-if="selectedIds.size > 0" type="primary">已选 {{ selectedIds.size }} 条用例</el-tag>
              <el-tag v-else type="info">当前项目全部用例</el-tag>
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleExport" :loading="exporting">导出 Excel</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'TcgWorkspaceView' })

import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { projectApi, testCaseApi, fileApi, moduleApi, llmApi, skillApi, conversationApi, executionApi, knowledgeApi, connectConversationSSE } from '@/api/tcg'
import ChatMessageList from '@/components/tcg/chat/ChatMessageList.vue'
import ChatInputBar from '@/components/tcg/chat/ChatInputBar.vue'

// ============ 状态 ============
const copilotOpen = ref(true)
const drawerTab = ref('task')
const copilotInput = ref('')
const chatMessages = ref([])
const chatListRef = ref(null)
const chatInputRef = ref(null)
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({ name: '', description: '' })
const treeSearch = ref('')
const selectedCase = ref(null)

const projects = ref([])
const currentProject = ref(null)
const cases = ref([])
const modules = ref([])
const loadingCases = ref(false)

const addingModule = ref(false)
const addingParentId = ref(null)
const addingParentDepth = ref(0)
const newModuleName = ref('')
const moduleInputRef = ref(null)
const activeModuleId = ref(null)

const generating = ref(false)
const pendingFiles = ref([])
const kbStats = ref({ doc_chunks: 0, case_vectors: 0, total: 0 })
const kbRebuilding = ref(false)
const uploadedFileIds = ref([])

const currentTestPoints = ref([])
const confirmedPointIds = ref(new Set())
const generatedCases = ref([])
const selectedIds = ref(new Set()) // 批量选择

// 用例展开/执行/导出相关
const expandedCaseIds = ref(new Set())
const showExecuteDialog = ref(false)
const executingCase = ref(null)
const caseDetail = ref(null)
const currentExecution = ref(null)
const currentStepIndex = ref(0)
const executionHistory = ref([])
const loadingHistory = ref(false)
const submittingStep = ref(false)
const actualResultInput = ref('')
const stepRemarkInput = ref('')
const showExportDialog = ref(false)
const exportTemplates = ref([])
const selectedExportTemplate = ref(null)
const exporting = ref(false)

const supplementContent = ref('')
const editingPoint = ref(null)

let sseSource = null

// 对话 Tab 管理
const conversations = ref([])
const currentConvId = ref(null)
const convStateCache = new Map() // convId -> { chatMessages, testPoints, cases, sessionId, uploadedFiles, ... }

// 评审进度消息追踪
let reviewProgressMsg = null

const allModels = ref([])
const enabledSkills = ref([])

const genConfig = reactive({
  moduleName: '',
  userPrompt: '',
  textModelId: null,
  visionModelId: null,  // 视觉模型
})

// 计算属性：筛选出视觉模型
const visionModels = computed(() => allModels.value.filter(m => m.supports_vision || m.model_type === 'vision' || m.model_type === 'multimodal'))

// ============ 计算属性 ============
const canSend = computed(() => copilotInput.value.trim() || pendingFiles.value.length > 0)

const allSelected = computed(() => filteredCases.value.length > 0 && filteredCases.value.every(c => selectedIds.value.has(c.id)))

const hasSelected = computed(() => selectedIds.value.size > 0)

// 树节点展开状态（独立 reactive，不在 computed 中写入）
const treeExpandState = reactive({})

function isNodeOpen(nodeId) {
  return treeExpandState[nodeId] === true
}

function toggleTreeNode(nodeId) {
  treeExpandState[nodeId] = !treeExpandState[nodeId]
}

const moduleTreeMap = computed(() => {
  const map = {}
  for (const m of modules.value) {
    map[m.id] = { ...m, children: [], cases: [], caseCount: 0 }
  }
  const roots = []
  for (const id in map) {
    const node = map[id]
    if (node.parent_id && map[node.parent_id]) {
      map[node.parent_id].children.push(node)
    } else {
      roots.push(node)
    }
  }
  const uncategorized = []
  for (const c of cases.value) {
    const modName = c.module_name || '未分类'
    const found = Object.values(map).find(m => m.name === modName)
    if (found) {
      found.cases.push(c)
      found.caseCount = found.cases.length
    } else {
      uncategorized.push(c)
    }
  }
  if (uncategorized.length) {
    roots.push({
      id: '__uncategorized__', name: '未分类', children: [],
      cases: uncategorized, caseCount: uncategorized.length,
    })
  }
  return roots
})

const filteredTree = computed(() => {
  if (!treeSearch.value) return moduleTreeMap.value
  const q = treeSearch.value.toLowerCase()
  function filterNode(node) {
    const matchName = node.name.toLowerCase().includes(q)
    const matchedCases = (node.cases || []).filter(c => c.name?.toLowerCase().includes(q))
    const childResults = (node.children || []).map(filterNode).filter(Boolean)
    if (matchName || matchedCases.length || childResults.length) {
      treeExpandState[node.id] = true
      return { ...node, cases: matchName ? node.cases : matchedCases, children: childResults }
    }
    return null
  }
  return moduleTreeMap.value.map(filterNode).filter(Boolean)
})

const filteredCases = computed(() => {
  if (activeModuleId.value === '__uncategorized__') {
    const modNames = new Set(modules.value.map(m => m.name))
    return cases.value.filter(c => !c.module_name || !modNames.has(c.module_name))
  }
  if (activeModuleId.value) {
    const mod = modules.value.find(m => m.id === activeModuleId.value)
    if (mod) return cases.value.filter(c => c.module_name === mod.name)
  }
  return cases.value
})

const breadcrumbPath = computed(() => {
  if (!activeModuleId.value) return []
  const path = []
  let cur = modules.value.find(m => m.id === activeModuleId.value)
  while (cur) {
    path.unshift({ id: cur.id, name: cur.name })
    cur = modules.value.find(m => m.id === cur.parent_id)
  }
  return path
})

const flatModuleOptions = computed(() => {
  const result = []
  function walk(nodes, prefix = '') {
    for (const n of nodes) {
      const fullPath = prefix ? `${prefix} / ${n.name}` : n.name
      result.push({ id: n.id, name: n.name, fullPath })
      if (n.children?.length) walk(n.children, fullPath)
    }
  }
  walk(moduleTreeMap.value)
  return result
})

const supplementFeedback = ref('')

// ============ 生命周期 ============
onMounted(async () => {
  await Promise.all([fetchProjects(), fetchAllModels(), fetchSkills()])
  if (projects.value.length > 0) await selectProject(projects.value[0])
})

async function fetchSkills() {
  try {
    const res = await skillApi.list({ enabled_only: true })
    enabledSkills.value = res.data?.items || res.data?.data?.items || []
  } catch (e) {
    console.error('获取 Skills 失败:', e)
    enabledSkills.value = []
  }
}

// ============ 对话管理 ============
async function fetchConversations(projectId) {
  if (!projectId) return
  try {
    const res = await conversationApi.list(projectId)
    const data = res.data?.data || res.data
    conversations.value = data?.items || []
  } catch (e) {
    console.error('获取对话列表失败:', e)
    conversations.value = []
  }
}

async function syncConvConfig() {
  if (!currentConvId.value) return
  try {
    await conversationApi.updateConfig(currentConvId.value, {
      text_model_id: genConfig.textModelId || null,
      vision_model_id: genConfig.visionModelId || null,
    })
  } catch (e) { console.error('同步配置失败:', e) }
}

async function createNewConversation() {
  if (!currentProject.value) { ElMessage.warning('请先选择项目'); return }
  try {
    const res = await conversationApi.create({
      project_id: currentProject.value.id,
      text_model_id: genConfig.textModelId || null,
      vision_model_id: genConfig.visionModelId || null,
    })
    const data = res.data?.data || res.data
    const newConv = {
      id: data.conversation_id,
      title: '新对话',
      created_at: data.created_at,
      updated_at: data.created_at,
    }
    conversations.value.unshift(newConv)
    await switchConversation(newConv.id, true)
    drawerTab.value = 'task'
  } catch (e) {
    ElMessage.error('创建对话失败')
    console.error(e)
  }
}

function saveCurrentConvState() {
  if (!currentConvId.value) return
  convStateCache.set(currentConvId.value, {
    chatMessages: [...chatMessages.value],
    testPoints: [...currentTestPoints.value],
    confirmedPointIds: new Set(confirmedPointIds.value),
    generatedCases: [...generatedCases.value],
    uploadedFileIds: [...uploadedFileIds.value],
    generating: generating.value,
  })
}

async function switchConversation(convId, isNew = false) {
  if (convId === currentConvId.value && !isNew) return

  saveCurrentConvState()

  if (sseSource) { sseSource.close(); sseSource = null }
  reviewProgressMsg = null
  pendingFiles.value = []

  currentConvId.value = convId

  if (isNew) {
    chatMessages.value = []
    currentTestPoints.value = []
    confirmedPointIds.value = new Set()
    generatedCases.value = []
    uploadedFileIds.value = []
    generating.value = false
    return
  }

  const cached = convStateCache.get(convId)
  if (cached) {
    chatMessages.value = cached.chatMessages
    currentTestPoints.value = cached.testPoints
    confirmedPointIds.value = cached.confirmedPointIds
    generatedCases.value = cached.generatedCases
    uploadedFileIds.value = cached.uploadedFileIds
    generating.value = cached.generating
    nextTick(() => { chatListRef.value?.scrollToBottom() })
    return
  }

  chatMessages.value = []
  currentTestPoints.value = []
  confirmedPointIds.value = new Set()
  generatedCases.value = []
  uploadedFileIds.value = []
  generating.value = false

  try {
    const res = await conversationApi.getMessages(convId)
    const data = res.data?.data || res.data
    const msgs = data?.items || []
    chatMessages.value = msgs.map(m => {
      const meta = m.metadata || {}
      return {
        type: meta.ui_type || (m.role === 'user' ? 'user' : (m.role === 'assistant' ? 'assistant' : 'info')),
        content: m.content || '',
        points: meta.test_points || null,
        cases: meta.test_cases || null,
        _collapsed: false,
        time: new Date(m.created_at),
        ...(meta.extra || {}),
      }
    })
    nextTick(() => { chatListRef.value?.scrollToBottom() })
  } catch (e) {
    console.error('恢复对话失败:', e)
    chatMessages.value = []
  }
}

async function handleDeleteConversation(convId) {
  try {
    await ElMessageBox.confirm('确定删除此对话？', '提示', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await conversationApi.delete(convId)
    convStateCache.delete(convId)
    const idx = conversations.value.findIndex(c => c.id === convId)
    conversations.value.splice(idx, 1)
    if (currentConvId.value === convId) {
      if (sseSource) { sseSource.close(); sseSource = null }
      if (conversations.value.length > 0) {
        const next = conversations.value[Math.min(idx, conversations.value.length - 1)]
        await switchConversation(next.id)
      } else {
        await createNewConversation()
      }
    }
  } catch (e) {
    ElMessage.error('删除对话失败')
  }
}

function convTitle(conv) {
  return conv.title || '新对话'
}

function formatConvTime(t) {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const hm = `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
  if (isToday) return `今天 ${hm}`
  const yesterday = new Date(now); yesterday.setDate(now.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) return `昨天 ${hm}`
  return `${d.getMonth()+1}/${d.getDate()} ${hm}`
}

async function fetchKbStats() {
  if (!currentProject.value) return
  try {
    const res = await knowledgeApi.stats(currentProject.value.id)
    kbStats.value = res.data?.data || { doc_chunks: 0, case_vectors: 0, total: 0 }
  } catch { kbStats.value = { doc_chunks: 0, case_vectors: 0, total: 0 } }
}

async function rebuildKnowledgeBase() {
  if (!currentProject.value || kbRebuilding.value) return
  kbRebuilding.value = true
  try {
    const res = await knowledgeApi.build(currentProject.value.id)
    const count = res.data?.data?.indexed_count || 0
    ElMessage.success(`知识库重建完成，已索引 ${count} 条向量`)
    await fetchKbStats()
  } catch (e) {
    ElMessage.error(`知识库重建失败: ${e.message}`)
  } finally { kbRebuilding.value = false }
}

async function fetchAllModels() {
  try {
    const res = await llmApi.listModels()
    const data = res.data?.models || res.data?.data?.models || []
    allModels.value = data
    const defaultChat = data.find(m => m.is_default && m.model_type === 'chat')
      || data.find(m => m.model_type === 'chat')
      || data[0]
    if (defaultChat) genConfig.textModelId = defaultChat.id
    const defaultVision = data.find(m => m.supports_vision || m.model_type === 'vision' || m.model_type === 'multimodal')
    if (defaultVision && !genConfig.visionModelId) genConfig.visionModelId = defaultVision.id
  } catch (e) { console.error('获取模型列表失败:', e) }
}

onBeforeUnmount(() => { if (sseSource) sseSource.close() })

// ============ 项目管理 ============
async function fetchProjects() {
  try {
    const res = await projectApi.list({ page: 1, page_size: 100 })
    const data = res.data?.data || res.data || res
    projects.value = data.items || data || []
  } catch (e) { console.error('获取项目列表失败:', e) }
}

function handleProjectCommand(command) {
  if (command === '__create__') { showCreateDialog.value = true; return }
  const project = projects.value.find(p => p.id === command)
  if (project) selectProject(project)
}

async function selectProject(project) {
  currentProject.value = project
  activeModuleId.value = null
  await Promise.all([fetchCases(project.id), fetchModules(project.id), fetchConversations(project.id), fetchKbStats()])
  if (conversations.value.length > 0) {
    await switchConversation(conversations.value[0].id)
  } else {
    await createNewConversation()
  }
}

async function fetchCases(projectId) {
  if (!projectId) return
  loadingCases.value = true
  try {
    const res = await testCaseApi.list({ project_id: projectId, page: 1, page_size: 500 })
    const data = res.data?.data || res.data || res
    cases.value = data.items || data || []
    // 切换项目时清空选择状态
    selectedIds.value.clear()
  } catch (e) { cases.value = [] }
  finally { loadingCases.value = false }
}

async function fetchModules(projectId) {
  if (!projectId) return
  try {
    const res = await moduleApi.list(projectId)
    const data = res.data?.data || res.data || res
    modules.value = Array.isArray(data) ? data : []
  } catch (e) { modules.value = [] }
}

async function handleCreateProject() {
  if (!createForm.value.name.trim()) { ElMessage.warning('请输入项目名称'); return }
  creating.value = true
  try {
    const res = await projectApi.create(createForm.value)
    const newP = res.data?.data || res.data || res
    showCreateDialog.value = false
    createForm.value = { name: '', description: '' }
    await fetchProjects()
    if (newP?.id) await selectProject(newP)
    ElMessage.success('项目创建成功')
  } catch (e) { ElMessage.error('创建失败') }
  finally { creating.value = false }
}

// ============ 模块(目录)管理 ============
function onSelectModule(node) { activeModuleId.value = node.id }

function startAddModule(parentNode) {
  if (!currentProject.value) { ElMessage.warning('请先选择项目'); return }
  addingModule.value = true
  addingParentId.value = parentNode?.id || null
  addingParentDepth.value = parentNode ? getDepth(parentNode.id) + 1 : 0
  newModuleName.value = ''
  nextTick(() => moduleInputRef.value?.focus())
}

function getDepth(moduleId) {
  let depth = 0, cur = modules.value.find(m => m.id === moduleId)
  while (cur?.parent_id) { depth++; cur = modules.value.find(m => m.id === cur.parent_id) }
  return depth
}

let _addingLock = false
async function confirmAddModule() {
  if (_addingLock) return
  _addingLock = true
  const name = newModuleName.value.trim()
  addingModule.value = false
  if (!name || !currentProject.value) { _addingLock = false; return }
  try {
    await moduleApi.create({ project_id: currentProject.value.id, name, parent_id: addingParentId.value })
    await fetchModules(currentProject.value.id)
    ElMessage.success(`目录「${name}」创建成功`)
  } catch (e) { ElMessage.error(e.response?.data?.message || e.message) }
  finally { setTimeout(() => { _addingLock = false }, 300) }
}
function onModuleInputBlur() { setTimeout(() => confirmAddModule(), 50) }
function cancelAddModule() { addingModule.value = false; _addingLock = false }

async function handleDeleteModule(node) {
  if (!node.id) return
  try {
    await ElMessageBox.confirm(`确定删除目录「${node.name}」？`, '提示', { type: 'warning' })
    await moduleApi.delete(node.id)
    await fetchModules(currentProject.value.id)
    if (activeModuleId.value === node.id) activeModuleId.value = null
    ElMessage.success('删除成功')
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

// ============ 用例操作 ============
async function editCase(c) {
  try {
    const { value } = await ElMessageBox.prompt('修改用例名称', '编辑用例', { inputValue: c.name })
    if (value && value !== c.name) {
      await testCaseApi.update(c.id, { name: value })
      await fetchCases(currentProject.value.id)
      ElMessage.success('已更新')
    }
  } catch (_) {}
}

async function deleteCase(c) {
  try {
    await ElMessageBox.confirm(`确定删除用例「${c.name}」？`, '提示', { type: 'warning' })
    await testCaseApi.delete(c.id)
    await fetchCases(currentProject.value.id)
    ElMessage.success('已删除')
  } catch (_) {}
}

function toggleExpandCase(caseId) {
  const ids = new Set(expandedCaseIds.value)
  if (ids.has(caseId)) ids.delete(caseId)
  else ids.add(caseId)
  expandedCaseIds.value = ids
}

async function executeCase(c) {
  executingCase.value = c
  caseDetail.value = null
  currentExecution.value = null
  currentStepIndex.value = 0
  actualResultInput.value = ''
  stepRemarkInput.value = ''
  showExecuteDialog.value = true

  try {
    const res = await testCaseApi.get(c.id)
    caseDetail.value = res.data?.data || res.data
    await loadExecutionHistory(c.id)
  } catch (e) {
    ElMessage.error('获取用例详情失败')
  }
}

async function loadExecutionHistory(caseId) {
  loadingHistory.value = true
  try {
    const res = await executionApi.list({ case_id: caseId, page_size: 10 })
    executionHistory.value = (res.data?.data?.items) || []
  } catch (e) {
    executionHistory.value = []
  } finally {
    loadingHistory.value = false
  }
}

async function openExportDialog() {
  if (!currentProject.value) { ElMessage.warning('请先选择项目'); return }
  showExportDialog.value = true
  try {
    const res = await testCaseApi.listTemplates(currentProject.value.id)
    exportTemplates.value = res.data?.data || res.data || []
    if (exportTemplates.value.length > 0) {
      selectedExportTemplate.value = exportTemplates.value[0].id
    }
  } catch (e) {
    exportTemplates.value = []
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const params = {
      project_id: currentProject.value.id,
    }
    if (selectedExportTemplate.value) {
      params.template_id = selectedExportTemplate.value
    }
    if (selectedIds.value.size > 0) {
      params.case_ids = Array.from(selectedIds.value)
    }
    await testCaseApi.exportCases(params)
    ElMessage.success('导出成功')
    showExportDialog.value = false
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function startExecution() {
  if (!caseDetail.value || !currentProject.value) return
  try {
    const res = await executionApi.create({
      case_id: caseDetail.value.id,
      project_id: currentProject.value.id,
    })
    currentExecution.value = res.data?.data || res.data
    currentStepIndex.value = 0
    actualResultInput.value = ''
    stepRemarkInput.value = ''
    ElMessage.success('执行已开始，请逐步验证')
  } catch (e) {
    ElMessage.error('创建执行记录失败: ' + (e.response?.data?.message || e.message))
  }
}

async function submitStepResult(status) {
  if (!currentExecution.value) return
  const steps = caseDetail.value?.test_steps || []
  const step = steps[currentStepIndex.value]
  if (!step) return

  submittingStep.value = true
  try {
    const res = await executionApi.updateStep(currentExecution.value.id, step.step, {
      status,
      actual_result: actualResultInput.value,
      remark: stepRemarkInput.value,
    })
    currentExecution.value = res.data?.data || res.data
    actualResultInput.value = ''
    stepRemarkInput.value = ''

    if (currentStepIndex.value < steps.length - 1) {
      currentStepIndex.value++
    } else {
      await completeExecution()
    }
  } catch (e) {
    ElMessage.error('提交步骤结果失败')
  } finally {
    submittingStep.value = false
  }
}

async function completeExecution() {
  if (!currentExecution.value) return
  try {
    const res = await executionApi.complete(currentExecution.value.id, {})
    currentExecution.value = res.data?.data || res.data
    ElMessage.success(currentExecution.value.status === 'passed' ? '用例执行通过' : '用例执行完成（存在失败步骤）')
    await loadExecutionHistory(caseDetail.value.id)
  } catch (e) {
    ElMessage.error('完成执行失败')
  }
}

function getStepStatus(stepNum) {
  if (!currentExecution.value?.step_results) return 'pending'
  const sr = currentExecution.value.step_results.find(s => s.step === stepNum)
  return sr?.status || 'pending'
}

function isExecutionFinished() {
  return currentExecution.value && ['passed', 'failed'].includes(currentExecution.value.status)
}

function formatExecTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ============ 批量选择与删除 ============
function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value.clear()
  } else {
    selectedIds.value = new Set(filteredCases.value.map(c => c.id))
  }
}

function toggleSelect(id) {
  const ids = new Set(selectedIds.value)
  if (ids.has(id)) ids.delete(id)
  else ids.add(id)
  selectedIds.value = ids
}

async function batchDeleteCases() {
  if (selectedIds.value.size === 0) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.size} 条用例？`, '批量删除', { type: 'warning' })
    const ids = Array.from(selectedIds.value)
    await testCaseApi.batchDelete(ids)
    selectedIds.value.clear()
    await fetchCases(currentProject.value.id)
    ElMessage.success(`已删除 ${ids.length} 条用例`)
  } catch (_) {}
}

// ============ Copilot 对话式交互 ============
function triggerUpload() { chatInputRef.value?.triggerUpload() }

const IMAGE_RE = /\.(png|jpe?g|gif|webp)$/i

function onFilesSelected(e) {
  const files = Array.from(e.target?.files || e.target?.items || [])
  pendingFiles.value.push(...files.map(f => {
    const item = { uid: Date.now() + Math.random(), name: f.name, raw: f }
    if (IMAGE_RE.test(f.name)) {
      item.preview = URL.createObjectURL(f)
    }
    return item
  }))
  if (e.target?.value !== undefined) e.target.value = ''
  const imgCount = files.filter(f => IMAGE_RE.test(f.name)).length
  const docCount = files.length - imgCount
  if (chatMessages.value.length === 0) {
    const parts = []
    if (docCount > 0) parts.push(`${docCount} 个文档`)
    if (imgCount > 0) parts.push(`${imgCount} 张图片`)
    addChat('info', `已选择 ${parts.join('、')}，点击发送`)
  }
}
function removePendingFile(f) { pendingFiles.value = pendingFiles.value.filter(x => x.uid !== f.uid) }

function handleInputSend(text) {
  copilotInput.value = text || copilotInput.value
  handleCopilotSend()
}

async function handleCopilotSend() {
  if (!currentProject.value) { ElMessage.warning('请先选择项目'); return }
  const text = copilotInput.value.trim()
  const files = [...pendingFiles.value]

  if (!text && files.length === 0) return

  const images = files.filter(f => IMAGE_RE.test(f.name))
  const docs = files.filter(f => !IMAGE_RE.test(f.name))

  if (text) { addChat('user', text, null, null, images.length > 0 ? { _images: images.map(i => i.preview) } : null); copilotInput.value = '' }

  pendingFiles.value = []

  if (docs.length > 0) {
    addChat('info', `上传 ${docs.length} 个文件...`)
    generating.value = true
    try {
      const newIds = []
      for (const f of docs) {
        if (!f.raw || f.raw.size === 0) {
          addChat('error', `${f.name} 文件内容为空，已跳过`)
          continue
        }
        const res = await fileApi.upload(currentProject.value.id, f.raw)
        const data = res.data?.data || res.data
        if (data?.success === false) {
          addChat('error', `${f.name}: ${data.message || '上传失败'}`)
          continue
        }
        if (data?.id) newIds.push({ id: data.id, name: f.name })
        addChat('info', `${f.name} 上传成功`)
      }
      uploadedFileIds.value = newIds
      addChat('config', '请确认生成配置后点击「开始生成」：', null, null)
      genConfig.moduleName = activeModuleId.value
        ? modules.value.find(m => m.id === activeModuleId.value)?.name || ''
        : ''
    } catch (e) {
      addChat('error', `上传失败: ${e.message}`)
    } finally { generating.value = false }
  }

  if (images.length > 0) {
    generating.value = true
    try {
      const imageIds = []
      for (const img of images) {
        if (!img.raw || img.raw.size === 0) continue
        const res = await fileApi.upload(currentProject.value.id, img.raw)
        const data = res.data?.data || res.data
        if (data?.id) imageIds.push(data.id)
      }
      if (imageIds.length > 0) {
        await sendTextToConversation(text || '请分析这些图片的内容', imageIds)
      }
    } catch (e) {
      addChat('error', `图片上传失败: ${e.message}`)
      generating.value = false
    }
  } else if (text && docs.length === 0) {
    await sendTextToConversation(text)
  }
}

async function sendTextToConversation(text, imageIds = []) {
  if (!currentConvId.value) {
    await createNewConversation()
  } else {
    await syncConvConfig()
  }
  generating.value = true
  try {
    const payload = { content: text, file_ids: [] }
    if (imageIds.length > 0) payload.image_ids = imageIds
    const res = await conversationApi.sendMessage(currentConvId.value, payload)
    connectToConvSSE(currentConvId.value)
  } catch (e) {
    addChat('error', `发送失败: ${e.message}`)
    generating.value = false
  }
}


async function handleStartGeneration() {
  if (!currentProject.value || uploadedFileIds.value.length === 0) return
  generating.value = true
  copilotOpen.value = true

  const moduleName = genConfig.moduleName?.trim()
  if (moduleName && !modules.value.find(m => m.name === moduleName)) {
    try {
      await moduleApi.create({ project_id: currentProject.value.id, name: moduleName, parent_id: activeModuleId.value })
      await fetchModules(currentProject.value.id)
    } catch (_) {}
  }

  try {
    if (!currentConvId.value) {
      await createNewConversation()
    }
    if (genConfig.textModelId || genConfig.visionModelId) {
      await conversationApi.updateConfig(currentConvId.value, {
        text_model_id: genConfig.textModelId || null,
        vision_model_id: genConfig.visionModelId || null,
        selected_skills: enabledSkills.value.map(s => s.key),
      }).catch(() => {})
    }

    const fileIds = uploadedFileIds.value.map(f => f.id)
    addChat('info', '▶️ 开始解析文档并提取测试点...')
    await conversationApi.sendMessage(currentConvId.value, {
      content: genConfig.userPrompt || '',
      file_ids: fileIds,
    })
    connectToConvSSE(currentConvId.value)
  } catch (e) {
    addChat('error', `启动失败: ${e.message}`)
    generating.value = false
  }
}

function handleCancelGeneration() {
  generating.value = false
  if (sseSource) { sseSource.close(); sseSource = null }
  addChat('info', '⏹ 已终止')
}

function connectToConvSSE(convId) {
  if (sseSource) sseSource.close()
  reviewProgressMsg = null
  sseSource = connectConversationSSE(convId, {
    progress(data) {
      const msg = data.message || '处理中...'
      const reviewMatch = msg.match(/质量评分\s*(\d+)\/(\d+)/)
      if (reviewMatch) {
        if (!reviewProgressMsg) {
          chatMessages.value.push({ type: 'progress', content: msg, percent: data.percent || 0, _isReviewProgress: true, time: new Date() })
          reviewProgressMsg = chatMessages.value[chatMessages.value.length - 1]
        } else {
          reviewProgressMsg.content = msg
          reviewProgressMsg.percent = data.percent
        }
        nextTick(() => { chatListRef.value?.scrollToBottom() })
        return
      }
      reviewProgressMsg = null
      addChat('progress', msg, null, null, { percent: data.percent })
    },
    stage(data) { addChat('stage', data.message || data.stage) },
    thinking(data) { addChat('thinking', data.message, null, null, { detail: data.detail }) },
    skills(data) { addChat('skills', data.message, null, null, { skills: data.skills }) },
    thinking_stream(data) {
      const last = chatMessages.value[chatMessages.value.length - 1]
      if (last && last.type === 'reasoning') { last.content = data.content }
      else { addChat('reasoning', data.content, null, null, { _streaming: true }) }
    },
    thinking_done(data) {
      const msg = [...chatMessages.value].reverse().find(m => m.type === 'reasoning')
      if (msg) { msg.content = data.content; msg._streaming = false; msg._duration = data.duration }
      else { addChat('reasoning', data.content, null, null, { _streaming: false, _duration: data.duration }) }
    },
    content_stream(data) {
      const last = chatMessages.value[chatMessages.value.length - 1]
      if (last && last.type === 'assistant' && last._streaming) {
        last.content = data.content
      } else {
        addChat('assistant', data.content, null, null, { _streaming: true })
      }
      nextTick(() => { chatListRef.value?.scrollToBottom() })
    },
    content_done(data) {
      const msg = [...chatMessages.value].reverse().find(m => m.type === 'assistant' && m._streaming)
      if (msg) { msg.content = data.content; msg._streaming = false }
      else { addChat('assistant', data.content) }
    },
    usage(data) {
      const msg = [...chatMessages.value].reverse().find(m => m.type === 'assistant')
      if (msg) { msg._usage = { input_tokens: data.input_tokens || 0, output_tokens: data.output_tokens || 0, total_tokens: data.total_tokens || 0 } }
    },
    error(data) { addChat('error', data.message) },
    test_points(data) {
      currentTestPoints.value = data.test_points || []
      confirmedPointIds.value = new Set(currentTestPoints.value.map(tp => tp.id))
      addChat('test_points', `提取了 ${data.count} 个测试点，请选择后确认：`, data.test_points)
    },
    test_cases(data) {
      const casesWithStatus = (data.test_cases || []).map(c => ({ ...c, _reviewStatus: 'draft' }))
      generatedCases.value = casesWithStatus
      addChat('test_cases', `生成了 ${data.count} 条用例，请审查：`, null, casesWithStatus)
    },
    chat_response(data) {
      if (data.actions && data.actions.length) {
        addChat('action_confirm', data.content || '', null, null, { actions: data.actions, _acted: false })
      } else {
        const existing = [...chatMessages.value].reverse().find(m => m.type === 'assistant' && m.content === (data.content || data.message || ''))
        if (!existing) {
          addChat('assistant', data.content || data.message || '')
        }
      }
      generating.value = false
    },
    done(data) {
      if (data.cancelled) return
      generating.value = false
      if (data.success === false) addChat('error', '处理结束，请检查日志')
      else if (generatedCases.value.length > 0) addChat('done', '✅ 流程完成，请审查上方用例')
      reviewProgressMsg = null
    },
    onAgentEvent(data) {
      const action = data.action
      const agent = data.agent || ''
      const payload = data.data || {}

      const findCard = () => [...chatMessages.value].reverse().find(m => m.type === 'agent_card' && m._agentName === agent)

      if (action === 'agent_start') {
        chatMessages.value.push({
          type: 'agent_card',
          content: '',
          _agentName: agent,
          _agentIcon: (payload.message || '').match(/^([\p{Emoji}])/u)?.[1] || '⚙',
          _status: 'running',
          _elapsed: '',
          _thinking: '',
          _thinkingCollapsed: true,
          _logs: [],
          _collapsed: false,
          time: new Date(),
        })
        nextTick(() => { chatListRef.value?.scrollToBottom() })
      } else if (action === 'agent_progress') {
        const card = findCard()
        if (card) {
          const msg = payload.message || ''
          if (msg && !card._logs.includes(msg)) card._logs.push(msg)
        }
        nextTick(() => { chatListRef.value?.scrollToBottom() })
      } else if (action === 'agent_thinking') {
        const card = findCard()
        if (card) {
          card._thinking = payload.content || ''
          card._thinkingCollapsed = false
        }
        nextTick(() => { chatListRef.value?.scrollToBottom() })
      } else if (action === 'agent_done') {
        const card = findCard()
        if (card) {
          card._status = payload.success !== false ? 'completed' : 'failed'
          card._elapsed = payload.elapsed_ms ? `${(payload.elapsed_ms / 1000).toFixed(1)}s` : ''
          card._collapsed = true
        }
      } else if (action === 'agent_error') {
        const card = findCard()
        if (card) {
          card._status = 'failed'
          card._logs.push(`❌ ${payload.message || payload.error || '未知错误'}`)
        } else {
          addChat('error', payload.message || payload.error || '未知错误')
        }
      } else if (action === 'agent_handoff') {
        const card = findCard()
        if (card) card._logs.push(payload.message || `→ ${payload.target}`)
      } else if (action === 'agent_result') {
        const card = findCard()
        if (card && payload.message) card._logs.push(payload.message)
      }
    },
    onError() { generating.value = false; if (sseSource) { sseSource.close(); sseSource = null } },
  })
}

// ============ 测试点操作 ============
function toggleTestPoint(tp) {
  const ids = new Set(confirmedPointIds.value)
  ids.has(tp.id) ? ids.delete(tp.id) : ids.add(tp.id)
  confirmedPointIds.value = ids
}
function selectAllTestPoints() { confirmedPointIds.value = new Set(currentTestPoints.value.map(tp => tp.id)) }

async function confirmTestPoints() {
  if (confirmedPointIds.value.size === 0) return
  if (!currentConvId.value) return

  const confirmed = currentTestPoints.value.filter(tp => confirmedPointIds.value.has(tp.id))
  generating.value = true
  addChat('info', `✅ 已确认 ${confirmed.length} 个测试点，正在生成用例...`)
  try {
    await conversationApi.sendMessage(currentConvId.value, {
      content: '/confirm',
      file_ids: [],
      intent_override: 'confirm_test_points',
      metadata: { confirmed_points: confirmed },
    })
    connectToConvSSE(currentConvId.value)
  } catch (e) { addChat('error', `确认失败: ${e.message}`); generating.value = false }
}

function addTestPoint(pointData) {
  if (!pointData?.title?.trim()) return
  const data = pointData
  const id = `TP-${String(currentTestPoints.value.length + 1).padStart(3, '0')}`
  const tp = { id, ...data }
  currentTestPoints.value.push(tp)
  confirmedPointIds.value.add(id)
  const lastMsg = chatMessages.value.find(m => m.type === 'test_points')
  if (lastMsg) lastMsg.points = currentTestPoints.value
  ElMessage.success('测试点已添加')
}

// 编辑测试点
function editTestPoint(tp) {
  editingPoint.value = { ...tp }
}

function saveEditPoint() {
  if (!editingPoint.value) return
  const idx = currentTestPoints.value.findIndex(tp => tp.id === editingPoint.value.id)
  if (idx !== -1) {
    currentTestPoints.value[idx] = { ...editingPoint.value }
    const lastMsg = chatMessages.value.find(m => m.type === 'test_points')
    if (lastMsg) lastMsg.points = currentTestPoints.value
  }
  editingPoint.value = null
  ElMessage.success('测试点已更新')
}

function cancelEditPoint() {
  editingPoint.value = null
}

// 删除测试点
async function deleteTestPoint(tp) {
  try {
    await ElMessageBox.confirm(`确定删除测试点「${tp.title}」？`, '提示', { type: 'warning' })
    currentTestPoints.value = currentTestPoints.value.filter(t => t.id !== tp.id)
    confirmedPointIds.value.delete(tp.id)
    const lastMsg = chatMessages.value.find(m => m.type === 'test_points')
    if (lastMsg) lastMsg.points = currentTestPoints.value
    ElMessage.success('测试点已删除')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(`删除失败`)
  }
}

async function supplementAndReanalyze(text) {
  const content = text || supplementContent.value
  if (!currentConvId.value || !content?.trim()) return
  try {
    generating.value = true
    addChat('info', `📝 补充语料: ${content.slice(0, 50)}...，正在重新分析...`)
    const rejectedIds = currentTestPoints.value
      .filter(tp => !confirmedPointIds.value.has(tp.id))
      .map(tp => tp.id)
    await conversationApi.sendMessage(currentConvId.value, {
      content: '/modify-points',
      file_ids: [],
      intent_override: 'modify_test_points',
      metadata: {
        feedback: content,
        rejected_ids: rejectedIds,
      },
    })
    supplementContent.value = ''
    connectToConvSSE(currentConvId.value)
  } catch (e) { addChat('error', `补充失败: ${e.message}`); generating.value = false }
}

// ============ 用例审查 ============
function setReviewStatus(tc, status) {
  tc._reviewStatus = tc._reviewStatus === status ? null : status
  if (status === 'needs_revision') {
    chatListRef.value?.showFeedbackInput?.()
  }
}
function batchApproveAll() { generatedCases.value.forEach(c => { c._reviewStatus = 'approved' }) }

function submitReview() {
  const reviews = generatedCases.value.filter(c => c._reviewStatus).map(c => ({ case_id: c.id, status: c._reviewStatus }))
  if (reviews.length === 0) { ElMessage.warning('请至少审查一条用例'); return }
  const approved = reviews.filter(r => r.status === 'approved').length
  const needsRevision = reviews.filter(r => r.status === 'needs_revision').length
  const rejected = reviews.filter(r => r.status === 'rejected').length
  addChat('info', `📋 评审结果: ${approved} 条通过, ${needsRevision} 条需修改, ${rejected} 条废弃`)
  ElMessage.success('评审结果已提交')
}

async function submitReviewAndSave() {
  const approved = generatedCases.value.filter(c => c._reviewStatus === 'approved')
  if (approved.length === 0) { ElMessage.warning('请至少通过一条用例'); return }

  const targetModule = genConfig.moduleName?.trim()
    || (activeModuleId.value ? modules.value.find(m => m.id === activeModuleId.value)?.name : '')
    || '未分类'

  try {
    if (currentProject.value) {
      await testCaseApi.batchSave({
        project_id: currentProject.value.id,
        cases: approved,
        module_name: targetModule,
      })
    }
    addChat('done', `💾 已保存 ${approved.length} 条用例到「${targetModule}」`)
    ElMessage.success(`保存成功`)
    await fetchCases(currentProject.value?.id)
  } catch (e) { addChat('error', `保存失败: ${e.message}`) }
}

async function submitSupplementRegenerate(feedbackText) {
  if (!currentConvId.value) return
  const needsRevisionCases = generatedCases.value.filter(c => c._reviewStatus === 'needs_revision')
  if (needsRevisionCases.length === 0) { ElMessage.warning('请先选择需要修改的用例'); return }
  const feedback = feedbackText || supplementFeedback.value
  if (!feedback?.trim()) { ElMessage.warning('请输入补充话术'); return }

  try {
    const caseIds = needsRevisionCases.map(c => c.id)
    generating.value = true
    await conversationApi.sendMessage(currentConvId.value, {
      content: '/modify-cases',
      file_ids: [],
      intent_override: 'modify_cases',
      metadata: {
        feedback: feedback.trim(),
        rejected_ids: caseIds,
      },
    })
    supplementFeedback.value = ''
    addChat('info', `🔄 正在为 ${caseIds.length} 条用例补充话术重新生成...`)
    connectToConvSSE(currentConvId.value)
  } catch (e) { addChat('error', `重新生成失败: ${e.message}`); generating.value = false }
}

// ============ 工具函数 ============
function addChat(type, content, points = null, cases = null, extra = null) {
  chatMessages.value.push({ type, content, points, cases, _collapsed: false, ...(extra || {}), time: new Date() })
  nextTick(() => { chatListRef.value?.scrollToBottom() })
}


function statusLabel(s) {
  return { draft: '草稿', pending: '待审查', approved: '通过', rejected: '废弃', needs_revision: '需修改' }[s] || s || '—'
}


async function handleActionConfirm(msg, action) {
  msg._acted = true
  if (action.id === 'invoke_workflow') {
    addChat('info', '🚀 启动结构化生成流程...')
    await sendTextToConversation('/generate_from_chat')
  } else if (action.id === 'chat_generate') {
    addChat('info', '💬 好的，我直接在对话中为你分析...')
    await sendTextToConversation(action.followup || '请直接在对话中帮我分析并列出测试点和测试用例')
  } else if (action.id === 'upload_doc') {
    triggerUpload()
  }
}

</script>

<style scoped>
.tcg-layout { display: flex; height: 100%; width: 100%; background: #fff; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2937; overflow: hidden; }
button { cursor: pointer; border: none; outline: none; transition: opacity 0.2s; }
button:hover { opacity: 0.85; }
button:disabled { opacity: 0.4; cursor: not-allowed; }

/* 左侧栏 */
.sidebar { width: 260px; background: #fdfdfd; border-right: 1px solid #e5e7eb; display: flex; flex-direction: column; flex-shrink: 0; }
.project-header { padding: 16px; }
.proj-select { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 8px 12px; border-radius: 8px; }
.proj-select:hover { background: #f3f4f6; }
.proj-icon { font-size: 18px; flex-shrink: 0; }
.proj-info { flex: 1; min-width: 0; }
.proj-name { font-weight: 600; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.proj-arrow { font-size: 10px; color: #94a3b8; flex-shrink: 0; }
.search-box { padding: 0 16px 12px; }
.search-box input { width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; outline: none; box-sizing: border-box; }
.search-box input:focus { border-color: #6366f1; }

/* 目录树 */
.module-tree { flex: 1; overflow-y: auto; padding: 0 12px 12px; }
.tree-header { display: flex; justify-content: space-between; align-items: center; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; padding: 0 4px; }
.add-root-btn { background: none; font-size: 16px; color: #94a3b8; cursor: pointer; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 4px; }
.add-root-btn:hover { color: #6366f1; background: #eef2ff; }
.tree-empty { padding: 24px 12px; text-align: center; font-size: 13px; color: #94a3b8; }
.tree-node-folder {
  display: flex; align-items: center; padding: 5px 8px; border-radius: 6px;
  cursor: pointer; font-size: 13px; color: #475569; margin-bottom: 1px; position: relative;
}
.tree-node-folder:hover { background: #f5f3ff; }
.tree-node-folder.active { background: #ede9fe; color: #6d28d9; }
.tree-node-case {
  display: flex; align-items: center; padding: 4px 8px; border-radius: 5px;
  cursor: pointer; font-size: 12px; color: #64748b; margin-bottom: 1px;
}
.tree-node-case:hover { background: #f1f5f9; }
.tree-node-case.active { background: #ede9fe; color: #6d28d9; }
.node-indent { flex-shrink: 0; }
.node-arrow {
  width: 16px; height: 16px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; cursor: pointer; color: #94a3b8; transition: transform 0.15s; border-radius: 3px;
}
.node-arrow:hover { background: #e5e7eb; }
.node-arrow.open { transform: rotate(90deg); }
.node-icon { font-size: 13px; margin-right: 4px; flex-shrink: 0; }
.node-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-count { color: #b0b8c4; font-size: 11px; margin-left: 4px; flex-shrink: 0; }
.node-actions { display: none; gap: 2px; margin-left: 4px; flex-shrink: 0; }
.tree-node-folder:hover .node-actions { display: flex; }
.na-add, .na-del { font-size: 13px; color: #94a3b8; cursor: pointer; padding: 1px 3px; border-radius: 3px; line-height: 1; }
.na-add:hover { color: #6366f1; background: #eef2ff; }
.na-del:hover { color: #ef4444; background: #fef2f2; }
.add-module-row { padding: 4px 0; }
.add-module-input { width: 100%; padding: 6px 10px; border: 1.5px solid #6366f1; border-radius: 6px; font-size: 13px; outline: none; box-sizing: border-box; background: #fff; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }

/* 主工作区 */
.main-workspace { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.ws-header { height: 48px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
.breadcrumb { font-size: 13px; color: #6b7280; }
.ai-toggle-btn { background: #f3f4f6; color: #374151; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.ai-toggle-btn.is-open { background: #6366f1; color: white; }
.toolbar { padding: 12px 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.actions-left { display: flex; gap: 10px; }
.btn-primary { background: #6366f1; color: white; padding: 6px 16px; border-radius: 6px; font-size: 12px; font-weight: 500; }
.btn-outline { background: white; border: 1px solid #d1d5db; color: #374151; padding: 6px 14px; border-radius: 6px; font-size: 12px; }
.btn-danger { background: #fee2e2; border: 1px solid #fca5a5; color: #dc2626; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; }
.btn-danger:hover { background: #fecaca; border-color: #f87171; }
.btn-sm { padding: 4px 10px; font-size: 11px; }
.actions-right { font-size: 12px; color: #6b7280; display: flex; align-items: center; gap: 10px; }
.kb-stat { color: #8b5cf6; font-size: 11px; }

/* 用例表格 */
.table-container { flex: 1; overflow: auto; }
.case-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.case-table th { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-weight: 500; text-align: left; position: sticky; top: 0; background: #fafafa; z-index: 5; }
.case-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }
.case-table tbody tr { cursor: pointer; }
.case-table tbody tr:hover { background: #f9fafb; }
.case-table tbody tr.row-active { background: #eef2ff; }
.id-text { color: #6b7280; font-family: monospace; font-size: 11px; }
.name-text { font-weight: 500; color: #111827; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.priority { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.priority.P0 { background: #fee2e2; color: #b91c1c; }
.priority.P1 { background: #ffedd5; color: #c2410c; }
.priority.P2 { background: #e0f2fe; color: #0369a1; }
.steps-cell { color: #374151; line-height: 1.8; }
.step-row { white-space: pre-wrap; }
.expect-cell { color: #059669; font-size: 11px; line-height: 1.8; }
.expect-row { white-space: pre-wrap; }
.no-data { color: #d1d5db; }
.status-badge { padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 500; }
.status-badge.approved { background: #dcfce7; color: #166534; }
.status-badge.rejected { background: #fee2e2; color: #b91c1c; }
.status-badge.needs_revision { background: #fef3c7; color: #92400e; }
.status-badge.pending { background: #f3f4f6; color: #6b7280; }
.ops-cell { white-space: nowrap; }
.op-btn { background: none; font-size: 14px; padding: 2px 4px; border-radius: 4px; }
.op-btn:hover { background: #f3f4f6; }
.empty-table { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; color: #9ca3af; }
.empty-icon { font-size: 40px; margin-bottom: 8px; }
.empty-table p { margin: 3px 0; font-size: 13px; }
.empty-hint { font-size: 12px; color: #d1d5db; }

/* ==================== Copilot 抽屉 ==================== */
.ai-drawer {
  width: 520px; min-width: 420px; background: #ffffff; border-left: 1px solid #e5e7eb;
  display: flex; flex-direction: column; flex-shrink: 0;
  box-shadow: -4px 0 24px rgba(0,0,0,0.04);
}
.drawer-header {
  height: 44px; background: #fff; border-bottom: 1px solid #f0f0f0;
  display: flex; justify-content: space-between; align-items: center; padding: 0 12px; flex-shrink: 0;
}
.drawer-title-area { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1; }
.drawer-title {
  font-size: 14px; font-weight: 600; color: #1e293b;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.drawer-header-actions { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.header-icon-btn {
  width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center;
  color: #94a3b8; background: transparent; cursor: pointer; transition: all 0.15s; border: none;
}
.header-icon-btn:hover { background: #f3f4f6; color: #374151; }
.header-icon-btn.active { background: #ede9fe; color: #6d28d9; }

/* 历史会话面板 */
.history-panel { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; }
.history-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px 8px; flex-shrink: 0;
}
.history-count { font-size: 12px; color: #94a3b8; }
.history-new-btn {
  padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 500;
  color: #6d28d9; background: #f5f3ff; border: 1px solid #e9d5ff; cursor: pointer;
}
.history-new-btn:hover { background: #ede9fe; }
.history-list { flex: 1; overflow-y: auto; padding: 0 12px 12px; display: flex; flex-direction: column; gap: 4px; }
.history-list::-webkit-scrollbar { width: 3px; }
.history-list::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
.history-empty { text-align: center; padding: 48px 20px; }
.history-empty p { font-size: 13px; color: #94a3b8; margin: 0 0 12px; }
.history-start-btn {
  padding: 6px 16px; border-radius: 6px; font-size: 13px; font-weight: 500;
  color: #fff; background: #8b5cf6; cursor: pointer;
}
.history-start-btn:hover { background: #7c3aed; }
.history-card {
  display: flex; align-items: center; padding: 8px 12px; border-radius: 8px;
  cursor: pointer; transition: all 0.15s; gap: 8px;
}
.history-card:hover { background: #f5f3ff; }
.history-card.active { background: #ede9fe; }
.hcard-body { flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; }
.hcard-title {
  font-size: 13px; font-weight: 500; color: #1e293b;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;
}
.hcard-time { font-size: 11px; color: #94a3b8; white-space: nowrap; }
.hcard-del {
  width: 24px; height: 24px; border-radius: 5px; display: flex; align-items: center; justify-content: center;
  color: #94a3b8; background: transparent; cursor: pointer; flex-shrink: 0; opacity: 0; transition: opacity 0.15s;
}
.history-card:hover .hcard-del { opacity: 1; }
.hcard-del:hover { color: #ef4444; background: #fee2e2; }

/* 配置栏 */
.config-bar {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  background: #fafafa; border-bottom: 1px solid #f0f0f0; flex-shrink: 0; flex-wrap: wrap;
}
.cfg-select { flex: 1; min-width: 80px; }
.cfg-select :deep(.el-input__wrapper) { box-shadow: none !important; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 0 8px; height: 28px; }
.cfg-select :deep(.el-input__inner) { font-size: 12px; }

.skills-toggle {
  display: flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 6px;
  font-size: 12px; color: #6d28d9; background: #f5f3ff; cursor: pointer; white-space: nowrap;
  border: 1px solid #e9d5ff; flex-shrink: 0;
}
.skills-toggle:hover { background: #ede9fe; }
.skills-count {
  background: #8b5cf6; color: #fff; font-size: 10px; padding: 0 5px; border-radius: 8px; font-weight: 600;
}
.skills-popover { max-height: 300px; overflow-y: auto; }
.skills-pop-title { font-size: 12px; font-weight: 600; color: #334155; margin-bottom: 8px; }
.skill-info-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 4px 0; font-size: 13px; color: #475569;
}
.skills-pop-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb; text-align: right; }
.skills-manage-link { font-size: 12px; color: #8b5cf6; text-decoration: none; }
.skills-manage-link:hover { text-decoration: underline; }
.skills-empty { font-size: 12px; color: #94a3b8; }

.slide-enter-active, .slide-leave-active { transition: width 0.25s ease, opacity 0.25s ease; }
.slide-enter-from, .slide-leave-to { width: 0 !important; opacity: 0; overflow: hidden; }

/* 展开/收起按钮 */
.case-name-cell { display: inline-block; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle; }
.expand-btn { background: #e0f2fe; color: #0369a1; border: none; padding: 2px 8px; border-radius: 4px; font-size: 10px; margin-left: 8px; cursor: pointer; }
.expand-btn:hover { background: #bae6fd; }
.module-text, .precondition-cell, .creator-text { font-size: 11px; color: #6b7280; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 展开行样式 */
.expanded-row td { padding: 0 !important; border-bottom: 1px solid #e0f2fe !important; background: #f8fafc; }
.expanded-content { display: flex; padding: 12px 20px; gap: 24px; }
.expanded-section { flex: 1; }
.section-title { font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.steps-list, .expect-list { display: flex; flex-direction: column; gap: 6px; }
.step-item, .expect-item { display: flex; gap: 8px; font-size: 12px; }
.step-num { color: #94a3b8; min-width: 20px; }
.step-action { color: #374151; }
.step-expected { color: #059669; }

/* 执行用例弹窗 */
.execute-detail { font-size: 13px; max-height: 72vh; overflow-y: auto; }
.detail-header { margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e5e7eb; }
.detail-title { font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 8px; }
.detail-meta { display: flex; flex-wrap: wrap; gap: 12px; }
.meta-item { color: #6b7280; font-size: 12px; }
.detail-section { margin-bottom: 16px; }
.detail-section .section-label { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 8px; text-transform: uppercase; }
.section-content { color: #374151; line-height: 1.6; white-space: pre-wrap; }
.loading-detail { text-align: center; padding: 40px; color: #6b7280; }

/* 执行步骤表格 */
.exec-steps-table { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.exec-step-header { display: flex; background: #f9fafb; border-bottom: 1px solid #e5e7eb; font-size: 11px; font-weight: 600; color: #64748b; }
.exec-step-row { display: flex; border-bottom: 1px solid #f3f4f6; transition: background 0.2s; }
.exec-step-row:last-child { border-bottom: none; }
.exec-step-row.is-current { background: #eff6ff; border-left: 3px solid #3b82f6; }
.exec-step-row.is-passed { background: #f0fdf4; }
.exec-step-row.is-failed { background: #fef2f2; }
.exec-step-row.is-blocked { background: #fffbeb; }
.es-col-num { width: 36px; padding: 8px; text-align: center; color: #94a3b8; flex-shrink: 0; }
.es-col-action { flex: 2; padding: 8px 10px; color: #374151; border-left: 1px solid #f3f4f6; }
.es-col-expected { flex: 2; padding: 8px 10px; color: #059669; border-left: 1px solid #f3f4f6; }
.es-col-status { width: 64px; padding: 8px; text-align: center; flex-shrink: 0; border-left: 1px solid #f3f4f6; }
.exec-badge { font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
.exec-badge.pass { background: #dcfce7; color: #15803d; }
.exec-badge.fail { background: #fee2e2; color: #b91c1c; }
.exec-badge.block { background: #fef3c7; color: #92400e; }
.exec-badge.pending { background: #f1f5f9; color: #94a3b8; }

/* 当前步骤操作区 */
.exec-action-area { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
.exec-current-label { font-size: 12px; color: #3b82f6; font-weight: 600; margin-bottom: 8px; }
.exec-current-step { margin-bottom: 12px; }
.ecs-action, .ecs-expected { font-size: 13px; color: #374151; margin-bottom: 4px; line-height: 1.5; }
.exec-step-btns { display: flex; gap: 10px; }

/* 执行结果 */
.exec-result-summary { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 16px; text-align: center; }
.ers-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.ers-title.passed { color: #15803d; }
.ers-title.failed { color: #b91c1c; }
.ers-stats { display: flex; justify-content: center; gap: 20px; }
.ers-stat { font-size: 13px; font-weight: 500; }
.ers-stat.pass { color: #15803d; }
.ers-stat.fail { color: #b91c1c; }
.ers-stat.block { color: #92400e; }

/* 执行历史 */
.exec-history-list { display: flex; flex-direction: column; gap: 6px; }
.exec-history-item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: #f9fafb; border-radius: 6px; font-size: 12px; }
.eh-status { font-weight: 600; min-width: 40px; }
.eh-status.passed { color: #15803d; }
.eh-status.failed { color: #b91c1c; }
.eh-status.in_progress { color: #3b82f6; }
.eh-executor { color: #475569; }
.eh-time { color: #94a3b8; }
.eh-stats { margin-left: auto; color: #64748b; }

/* 导出弹窗 */
.export-options { padding: 8px 0; }
.export-range { display: flex; gap: 8px; align-items: center; }
</style>
