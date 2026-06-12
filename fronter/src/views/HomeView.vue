<template>
  <div class="home-view">
    <!-- 空状态欢迎页 -->
    <div v-if="!store.currentSessionId" class="welcome">
      <div class="welcome-icon">🔍</div>
      <h2>RAG 智能检索助手</h2>
      <p>上传你的文档，开始智能问答</p>
      <div class="welcome-actions">
        <button class="btn-primary" @click="handleCreateSession">开始新对话</button>
        <button class="btn-secondary" @click="showUpload = true">上传文档</button>
      </div>
    </div>

    <!-- 聊天区域 -->
    <template v-else>
      <!-- 消息流 -->
      <div ref="msgContainerRef" class="messages-container">
        <div class="messages-inner">
          <div v-if="store.messages.length === 0" class="chat-empty">
            <p>向我提问，我将在你的知识库中为你检索答案</p>
          </div>
          <ChatMessage
            v-for="msg in store.messages"
            :key="msg.id"
            :msg="msg"
          />
        </div>
      </div>

      <!-- 输入框 -->
      <ChatInput
        :disabled="store.isLoading"
        @send="handleSend"
        @upload-click="showUpload = true"
      />
    </template>

    <!-- 文档管理面板 -->
    <UploadPanel v-if="showUpload" @close="showUpload = false" />
  </div>
</template>

<script setup>
import { ref, nextTick, watch, inject } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'
import UploadPanel from '@/components/UploadPanel.vue'
import { API_BASE } from '@/api/request'

const store = useChatStore()
// 从 App.vue 注入共享的 showUpload 状态（Sidebar 和 ChatInput 统一控制）
const showUpload = inject('showUpload', ref(false))
const msgContainerRef = ref(null)

// 消息更新时自动滚到底部（深度监听内容变化，支持流式输出滚动）
watch(
  () => store.messages,
  () => nextTick(scrollToBottom),
  { deep: true },
)

function scrollToBottom() {
  if (msgContainerRef.value) {
    msgContainerRef.value.scrollTop = msgContainerRef.value.scrollHeight
  }
}

async function handleCreateSession() {
  try {
    await store.createSession()
  } catch (e) {
    // 后端不可达时静默处理，用户可看到欢迎页不变
    console.error('创建会话失败:', e)
  }
}

async function handleSend(text) {
  if (!store.currentSessionId) return

  // 添加用户消息
  store.addMessage('user', text)

  // 添加 AI 占位消息（思考中）
  store.addMessage('assistant', '')
  const lastIdx = store.messages.length - 1
  store.messages[lastIdx].thinking = true
  store.setLoading(true)

  await nextTick()
  scrollToBottom()

  try {
    const response = await fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: store.currentSessionId,
        message: text,
        stream: true,
      }),
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    store.messages[lastIdx].thinking = false
    store.messages[lastIdx].content = ''

    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        // 处理剩余的 buffer
        if (buffer.startsWith('data:')) {
          try {
            const dataStr = buffer.slice(5).trim()
            if (dataStr) {
              const data = JSON.parse(dataStr)
              if (data.type === 'token' && data.content) {
                store.appendToLastAssistant(data.content)
              }
            }
          } catch {}
        }
        break
      }

      buffer += decoder.decode(value, { stream: true })

      // 按 \n\n 分割 SSE 事件
      while (buffer.includes('\n\n')) {
        const idx = buffer.indexOf('\n\n')
        const raw = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)

        if (!raw.startsWith('data:')) continue

        try {
          const dataStr = raw.slice(5).trim()
          if (!dataStr) continue
          const data = JSON.parse(dataStr)

          if (data.type === 'token' && data.content) {
            store.appendToLastAssistant(data.content)
            await nextTick()
            scrollToBottom()
          } else if (data.type === 'error') {
            store.messages[lastIdx].content = `❌ ${data.content}`
          }
          // done 事件不中断循环，让 while 继续读
        } catch {}
      }
    }
  } catch (e) {
    store.messages[lastIdx].thinking = false
    store.messages[lastIdx].content = `❌ 请求失败：${e.message}`
  } finally {
    store.setLoading(false)
  }
}
</script>

<style scoped>
.home-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
  overflow: hidden;
}

/* 欢迎页 */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #999;
}
.welcome-icon { font-size: 48px; }
.welcome h2 { color: #1a1a1a; font-size: 22px; margin: 0; }
.welcome p { font-size: 14px; margin: 0; }
.welcome-actions { display: flex; gap: 12px; margin-top: 8px; }

.btn-primary {
  padding: 10px 24px;
  background: #4f46e5;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background: #4338ca; }

.btn-secondary {
  padding: 10px 24px;
  background: #f5f5f5;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-secondary:hover { background: #eee; color: #333; }

/* 消息流 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #ccc transparent;
}

.messages-inner {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px 16px;
}

.chat-empty {
  text-align: center;
  color: #999;
  font-size: 14px;
  padding: 40px 0;
}
</style>
