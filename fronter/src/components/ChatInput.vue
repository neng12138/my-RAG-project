<template>
  <div class="input-area">
    <div class="input-container" :class="{ focused }">
      <!-- 文件上传按钮 -->
      <button class="icon-btn" @click="$emit('uploadClick')" title="上传文档">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>

      <!-- 文本输入 -->
      <textarea
        ref="textareaRef"
        v-model="inputText"
        class="textarea"
        :placeholder="placeholder"
        :rows="1"
        :disabled="disabled"
        @focus="focused = true"
        @blur="focused = false"
        @keydown.enter.exact.prevent="handleSend"
        @keydown.shift.enter="handleNewline"
        @input="autoResize"
      ></textarea>

      <!-- 发送按钮 -->
      <button
        class="send-btn"
        :class="{ active: canSend }"
        :disabled="!canSend"
        @click="handleSend"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
        </svg>
      </button>
    </div>
    <div class="hint">Enter 发送 · Shift+Enter 换行</div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: '向 RAG 助手发消息...' },
})

const emit = defineEmits(['send', 'uploadClick'])

const inputText = ref('')
const focused = ref(false)
const textareaRef = ref(null)

const canSend = computed(() => inputText.value.trim().length > 0 && !props.disabled)

function handleSend() {
  if (!canSend.value) return
  const text = inputText.value.trim()
  inputText.value = ''
  nextTick(() => resetTextareaHeight())
  emit('send', text)
}

function handleNewline() {
  // Shift+Enter 换行，由 textarea 默认行为处理
}

function autoResize() {
  const ta = textareaRef.value
  if (!ta) return
  ta.style.height = 'auto'
  ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
}

function resetTextareaHeight() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}
</script>

<style scoped>
.input-area {
  padding: 12px 20px 16px;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 14px;
  padding: 10px 12px;
  transition: border-color 0.2s;
}
.input-container.focused {
  border-color: #4f46e5;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: #999;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}
.icon-btn:hover { color: #555; background: #e8e8e8; }

.textarea {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: #1a1a1a;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  min-height: 24px;
  max-height: 200px;
  font-family: inherit;
  overflow-y: auto;
  scrollbar-width: thin;
}
.textarea::placeholder { color: #bbb; }
.textarea:disabled { opacity: 0.5; cursor: not-allowed; }

.send-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #e8e8e8;
  color: #bbb;
  border-radius: 8px;
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}
.send-btn.active {
  background: #4f46e5;
  color: #fff;
  cursor: pointer;
}
.send-btn.active:hover { background: #4338ca; }

.hint {
  text-align: center;
  color: #ccc;
  font-size: 11px;
  margin-top: 6px;
}
</style>
