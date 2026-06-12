import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sessionApi } from '@/api/chat'
import { v4 as uuidv4 } from 'uuid'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref([])
  const currentSessionId = ref(null)
  const messages = ref([])   // { id, role, content, thinking }
  const isLoading = ref(false)

  const currentSession = computed(() =>
    sessions.value.find((s) => s.id === currentSessionId.value)
  )

  async function loadSessions() {
    try {
      const data = await sessionApi.list()
      sessions.value = data
    } catch (e) {
      console.error(e)
    }
  }

  async function createSession() {
    try {
      const data = await sessionApi.create()
      sessions.value.unshift(data)
      switchSession(data.id)
      return data
    } catch (e) {
      console.error('创建会话失败:', e)
      throw e
    }
  }

  function switchSession(id) {
    currentSessionId.value = id
    messages.value = []
  }

  async function deleteSession(id) {
    await sessionApi.delete(id)
    sessions.value = sessions.value.filter((s) => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = null
      messages.value = []
    }
  }

  function addMessage(role, content) {
    messages.value.push({ id: uuidv4(), role, content, thinking: false })
  }

  function appendToLastAssistant(token) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += token
    }
  }

  function setLoading(v) {
    isLoading.value = v
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    currentSession,
    loadSessions,
    createSession,
    switchSession,
    deleteSession,
    addMessage,
    appendToLastAssistant,
    setLoading,
  }
})
