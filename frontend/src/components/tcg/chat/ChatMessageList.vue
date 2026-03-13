<template>
  <div class="chat-message-list" ref="scrollRef">
    <div class="chat-inner">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="chat-welcome">
        <div class="welcome-icon">&#129302;</div>
        <h3>X-Run 智能助手</h3>
        <p>我可以和你对话、回答问题，也能帮你生成测试用例</p>
        <div class="welcome-hints">
          <span class="hint-chip" @click="$emit('hint', '帮我分析一下登录功能的测试点')">&#128172; 帮我分析登录功能的测试点</span>
          <span class="hint-chip" @click="$emit('hint', '如何设计接口测试策略？')">&#128214; 如何设计接口测试策略？</span>
          <span class="hint-chip" @click="$emit('upload')">&#128206; 上传需求文档生成用例</span>
        </div>
      </div>

      <!-- 消息分发 -->
      <template v-for="(msg, i) in messages" :key="i">
        <ChatUserMessage v-if="msg.type === 'user'" :msg="msg" />

        <ChatAgentCard v-else-if="msg.type === 'agent_card'" :msg="msg" />

        <ChatStageCard v-else-if="msg.type === 'stage'" :msg="msg" />

        <ChatSkillCard v-else-if="msg.type === 'skills'" :msg="msg" />

        <ChatThinkingCard v-else-if="msg.type === 'thinking' || msg.type === 'reasoning'" :msg="msg" />

        <ChatProgressText v-else-if="msg.type === 'progress'" :msg="msg" />

        <ChatErrorCard v-else-if="msg.type === 'error'" :msg="msg" />

        <ChatDoneMessage v-else-if="msg.type === 'done'" :msg="msg" />

        <ChatConfigCard
          v-else-if="msg.type === 'config'"
          :msg="msg"
          :config="config"
          :module-options="moduleOptions"
          :generating="generating"
          @start="$emit('start-generation')"
          @update:config="$emit('update:config', $event)"
        />

        <ChatTestPointsCard
          v-else-if="msg.type === 'test_points' && msg.points"
          :msg="msg"
          :points="msg.points"
          :confirmed-ids="confirmedPointIds"
          :confirmed-count="confirmedPointIds.size"
          :editing-point="editingPoint"
          @toggle="$emit('toggle-point', $event)"
          @confirm="$emit('confirm-points')"
          @select-all="$emit('select-all-points')"
          @add="$emit('add-point', $event)"
          @edit="$emit('edit-point', $event)"
          @delete="$emit('delete-point', $event)"
          @supplement="$emit('supplement', $event)"
          @save-edit="$emit('save-edit-point')"
          @cancel-edit="$emit('cancel-edit-point')"
          @update:editingPoint="$emit('update:editingPoint', $event)"
        />

        <ChatTestCasesCard
          v-else-if="msg.type === 'test_cases' && msg.cases"
          ref="testCasesCardRef"
          :msg="msg"
          :cases="msg.cases"
          @set-status="(tc, status) => $emit('set-review-status', tc, status)"
          @approve-all="$emit('approve-all')"
          @submit-review="$emit('submit-review')"
          @save="$emit('save-cases')"
          @regenerate="$emit('regenerate', $event)"
        />

        <ChatActionConfirm
          v-else-if="msg.type === 'action_confirm'"
          :msg="msg"
          @action="(m, a) => $emit('action-confirm', m, a)"
        />

        <ChatAssistantMessage v-else-if="msg.type === 'assistant'" :msg="msg" />

        <!-- info / 兜底 -->
        <ChatProgressText v-else :msg="msg" />
      </template>
    </div>

    <!-- 新建对话按钮（消息区底部） -->
    <div v-if="messages.length > 0 && !generating" class="new-conv-area">
      <button class="new-conv-btn" @click="$emit('new-conversation')">
        &#10024; 开启新对话 →
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import ChatUserMessage from './ChatUserMessage.vue'
import ChatAgentCard from './ChatAgentCard.vue'
import ChatStageCard from './ChatStageCard.vue'
import ChatSkillCard from './ChatSkillCard.vue'
import ChatThinkingCard from './ChatThinkingCard.vue'
import ChatProgressText from './ChatProgressText.vue'
import ChatErrorCard from './ChatErrorCard.vue'
import ChatDoneMessage from './ChatDoneMessage.vue'
import ChatConfigCard from './ChatConfigCard.vue'
import ChatTestPointsCard from './ChatTestPointsCard.vue'
import ChatTestCasesCard from './ChatTestCasesCard.vue'
import ChatActionConfirm from './ChatActionConfirm.vue'
import ChatAssistantMessage from './ChatAssistantMessage.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  generating: { type: Boolean, default: false },
  config: { type: Object, default: () => ({}) },
  moduleOptions: { type: Array, default: () => [] },
  confirmedPointIds: { type: Set, default: () => new Set() },
  editingPoint: { type: Object, default: null },
})

defineEmits([
  'hint', 'upload', 'new-conversation',
  'start-generation', 'update:config',
  'toggle-point', 'confirm-points', 'select-all-points',
  'add-point', 'edit-point', 'delete-point', 'supplement',
  'save-edit-point', 'cancel-edit-point', 'update:editingPoint',
  'set-review-status', 'approve-all', 'submit-review', 'save-cases', 'regenerate',
  'action-confirm',
])

const scrollRef = ref(null)
const testCasesCardRef = ref(null)

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  })
}

watch(() => props.messages.length, () => scrollToBottom())

defineExpose({
  scrollToBottom,
  showFeedbackInput() { testCasesCardRef.value?.showFeedbackInput?.() },
})
</script>

<style scoped>
@import './chat-theme.css';

.chat-message-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  background: var(--chat-bg);
  -webkit-overflow-scrolling: touch;
}

.chat-message-list::-webkit-scrollbar { width: 4px; }
.chat-message-list::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

.chat-inner {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: min-content;
}

/* 空状态 */
.chat-welcome {
  text-align: center;
  padding: 48px 20px;
  flex-shrink: 0;
}

.welcome-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.chat-welcome h3 {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px;
}

.chat-welcome p {
  font-size: 13px;
  color: #94a3b8;
  margin: 0 0 16px;
}

.welcome-hints {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  margin-top: 16px;
}

.hint-chip {
  display: inline-block;
  padding: 8px 18px;
  border-radius: 18px;
  font-size: 13px;
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s;
}

.hint-chip:hover {
  background: #ede9fe;
  border-color: #c4b5fd;
  color: #6d28d9;
}

/* 新建对话按钮 */
.new-conv-area {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.new-conv-btn {
  padding: 8px 20px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  color: #6d28d9;
  background: #f5f3ff;
  border: 1px solid #e9d5ff;
  cursor: pointer;
  transition: all 0.15s;
}

.new-conv-btn:hover {
  background: #ede9fe;
  border-color: #c4b5fd;
}
</style>
