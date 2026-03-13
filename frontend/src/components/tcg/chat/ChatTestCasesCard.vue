<template>
  <div class="tc-card">
    <div class="tc-header">
      <span class="tc-icon">&#128221;</span>
      <span>测试用例生成报告 ({{ cases.length }} 条)</span>
    </div>
    <div class="tc-body">
      <div class="case-list">
        <div v-for="tc in cases" :key="tc.id" class="case-item" :class="tc._reviewStatus || 'pending'">
          <div class="case-hd">
            <span class="case-no">{{ tc.case_no }}</span>
            <span class="case-pri" :class="tc.priority">{{ tc.priority }}</span>
            <span class="case-name">{{ tc.name }}</span>
          </div>
          <div v-if="tc.test_steps?.length" class="case-steps">
            <div v-for="s in tc.test_steps" :key="s.step" class="case-step-row">
              {{ s.step }}. {{ s.action }} → {{ s.expected }}
            </div>
          </div>
          <div class="case-actions">
            <button :class="['act-btn', 'ok', { active: tc._reviewStatus === 'approved' }]" @click="$emit('set-status', tc, 'approved')">&#9989; 通过</button>
            <button :class="['act-btn', 'fix', { active: tc._reviewStatus === 'needs_revision' }]" @click="$emit('set-status', tc, 'needs_revision')">&#9888;&#65039; 修改</button>
            <button :class="['act-btn', 'no', { active: tc._reviewStatus === 'rejected' }]" @click="$emit('set-status', tc, 'rejected')">&#10060; 废弃</button>
          </div>
        </div>
      </div>

      <!-- 补充话术 -->
      <div v-if="showFeedback" class="feedback-area">
        <div class="feedback-header">
          <span>&#128161; 补充话术（说明需要如何修改用例）</span>
          <span class="feedback-close" @click="showFeedback = false">×</span>
        </div>
        <textarea v-model="feedbackText" placeholder="例如：需要增加边界值测试用例，覆盖更多异常场景..." rows="3"></textarea>
        <div class="feedback-tips">
          已选择 <strong>{{ needsRevisionCount }}</strong> 条用例需要修改
        </div>
      </div>

      <div class="tc-footer">
        <div class="footer-left">
          <button class="btn-ghost" @click="$emit('approve-all')">全部通过</button>
        </div>
        <div class="footer-right">
          <button v-if="showFeedback" class="btn-warning" @click="handleRegenerate" :disabled="!feedbackText.trim()">&#128260; 补充话术重新生成</button>
          <button class="btn-primary" @click="$emit('submit-review')" :disabled="!hasReviewed">&#128190; 提交评审结果</button>
          <button class="btn-success" @click="$emit('save')" :disabled="!hasApproved">&#9989; 保存入库</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  msg: { type: Object, required: true },
  cases: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'set-status', 'approve-all',
  'submit-review', 'save', 'regenerate',
])

const showFeedback = ref(false)
const feedbackText = ref('')

const hasReviewed = computed(() => props.cases.some(c => c._reviewStatus))
const hasApproved = computed(() => props.cases.some(c => c._reviewStatus === 'approved'))
const needsRevisionCount = computed(() => props.cases.filter(c => c._reviewStatus === 'needs_revision').length)

function handleRegenerate() {
  if (!feedbackText.value.trim()) return
  emit('regenerate', feedbackText.value)
  feedbackText.value = ''
  showFeedback.value = false
}

// 当外部设置 needs_revision 状态时自动显示反馈框
defineExpose({
  showFeedbackInput() { showFeedback.value = true },
})
</script>

<style scoped>
.tc-card {
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.1);
}

.tc-header {
  background: #dcfce7;
  color: #166534;
  font-weight: 600;
  font-size: 13px;
  padding: 12px 16px;
  border-bottom: 1px solid #bbf7d0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tc-icon { font-size: 14px; }

.tc-body { padding: 16px; }

.case-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.15s;
}

.case-item.draft { border-color: #8b5cf6; background: #f5f3ff; }
.case-item.approved { border-color: #22c55e; background: #f0fdf4; }
.case-item.rejected { border-color: #ef4444; background: #fef2f2; opacity: 0.65; }
.case-item.needs_revision { border-color: #f59e0b; background: #fffbeb; }

.case-hd {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.case-no { font-size: 11px; color: #94a3b8; font-weight: 700; font-family: monospace; }

.case-pri { padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.case-pri.P0 { background: #fee2e2; color: #b91c1c; }
.case-pri.P1 { background: #ffedd5; color: #c2410c; }
.case-pri.P2 { background: #e0f2fe; color: #0369a1; }

.case-name { font-size: 13px; font-weight: 600; color: #1e293b; flex: 1; }

.case-steps { font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 8px; }
.case-step-row { margin-bottom: 2px; }

.case-actions { display: flex; gap: 6px; }

.act-btn {
  padding: 3px 10px;
  border-radius: 5px;
  font-size: 11px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
}

.act-btn.ok.active { background: #dcfce7; border-color: #22c55e; color: #166534; }
.act-btn.fix.active { background: #fef3c7; border-color: #f59e0b; color: #92400e; }
.act-btn.no.active { background: #fee2e2; border-color: #ef4444; color: #b91c1c; }

/* 补充话术 */
.feedback-area {
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  margin-top: 12px;
}

.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #92400e;
  font-weight: 600;
}

.feedback-close { cursor: pointer; font-size: 16px; color: #b45309; }
.feedback-close:hover { color: #78350f; }

.feedback-area textarea {
  width: 100%;
  border: 1px solid #fcd34d;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 12px;
  resize: none;
  box-sizing: border-box;
  font-family: inherit;
}

.feedback-area textarea:focus { outline: none; border-color: #f59e0b; box-shadow: 0 0 0 1px #f59e0b; }

.feedback-tips { margin-top: 6px; font-size: 11px; color: #b45309; }

/* 底部 */
.tc-footer {
  padding: 12px 0 0;
  border-top: 1px solid #bbf7d0;
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.footer-left,
.footer-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-ghost {
  background: #f3f4f6;
  color: #4b5563;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
}

.btn-ghost:hover { background: #e5e7eb; }

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-primary:hover { background: #2563eb; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-success {
  background: #16a34a;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-success:hover { background: #15803d; }
.btn-success:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-warning {
  background: #f59e0b;
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  cursor: pointer;
}

.btn-warning:hover { background: #d97706; }
.btn-warning:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
