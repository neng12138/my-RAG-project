<template>
  <div class="sidebar">
    <!-- Logo区 -->
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-icon">🔍</span>
        <span class="logo-text">RAG 助手</span>
      </div>
      <button class="new-chat-btn" @click="handleNewChat" title="新建对话">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="session-list">
      <div v-if="store.sessions.length === 0" class="empty-tip">
        暂无对话，点击 + 开始
      </div>

      <div
        v-for="s in store.sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: store.currentSessionId === s.id }"
        @click="store.switchSession(s.id)"
      >
        <span class="session-title">{{ s.title }}</span>
        <button
          class="del-btn"
          @click.stop="store.deleteSession(s.id)"
          title="删除"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 底部：文档管理入口 -->
    <div class="sidebar-footer">
      <button class="doc-btn" @click="$emit('openDocs')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>
        </svg>
        知识库管理
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useChatStore } from '@/stores/chatStore'

const emit = defineEmits(['openDocs'])
const store = useChatStore()

onMounted(() => store.loadSessions())

async function handleNewChat() {
  await store.createSession()
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  background: #f7f7f8;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e5e5;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 12px;
  border-bottom: 1px solid #e5e5e5;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1a1a1a;
  font-size: 15px;
  font-weight: 600;
}

.logo-icon { font-size: 18px; }

.new-chat-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #e8e8e8;
  color: #666;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, color 0.2s;
}
.new-chat-btn:hover { background: #ddd; color: #333; }

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 6px;
  scrollbar-width: thin;
  scrollbar-color: #ccc transparent;
}

.empty-tip {
  text-align: center;
  color: #aaa;
  font-size: 12px;
  padding: 24px 0;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  color: #555;
  font-size: 13px;
  margin-bottom: 2px;
  transition: background 0.15s;
}
.session-item:hover { background: #e8e8e8; color: #1a1a1a; }
.session-item.active { background: #e0e0e0; color: #1a1a1a; }

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.del-btn {
  display: none;
  border: none;
  background: none;
  color: #999;
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
}
.session-item:hover .del-btn { display: flex; }
.del-btn:hover { color: #ef4444; }

.sidebar-footer {
  padding: 10px 8px;
  border-top: 1px solid #e5e5e5;
}

.doc-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: none;
  background: none;
  color: #666;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.doc-btn:hover { background: #e8e8e8; color: #1a1a1a; }
</style>
