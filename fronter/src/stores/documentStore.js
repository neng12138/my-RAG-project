import { defineStore } from 'pinia'
import { ref } from 'vue'
import { documentApi } from '@/api/document'

// 存储轮询定时器引用，便于清理
const _pollTimers = new Map()

export const useDocumentStore = defineStore('document', () => {
  const documents = ref([])
  const uploading = ref(false)

  async function loadDocuments() {
    documents.value = await documentApi.list()
  }

  async function uploadDocument(file) {
    uploading.value = true
    try {
      const fd = new FormData()
      fd.append('file', file)
      const doc = await documentApi.upload(fd)
      documents.value.unshift(doc)
      // 轮询状态（带最大重试次数）
      pollDocStatus(doc.id)
      return doc
    } finally {
      uploading.value = false
    }
  }

  function pollDocStatus(docId) {
    // 清除该文档已有的定时器（防止重复）
    if (_pollTimers.has(docId)) {
      clearInterval(_pollTimers.get(docId))
    }

    let retries = 0
    const maxRetries = 30 // 30 * 2秒 = 60秒超时

    const timer = setInterval(async () => {
      retries++
      if (retries > maxRetries) {
        clearInterval(timer)
        _pollTimers.delete(docId)
        // 超时后标记为失败
        const idx = documents.value.findIndex((d) => d.id === docId)
        if (idx !== -1) {
          documents.value[idx].status = 'failed'
          documents.value[idx].error_message = '处理超时，请重试'
        }
        return
      }

      try {
        const list = await documentApi.list()
        const found = list.find((d) => d.id === docId)
        if (found) {
          const idx = documents.value.findIndex((d) => d.id === docId)
          if (idx !== -1) documents.value[idx] = found
          if (found.status !== 'processing') {
            clearInterval(timer)
            _pollTimers.delete(docId)
          }
        }
      } catch {
        clearInterval(timer)
        _pollTimers.delete(docId)
      }
    }, 2000)

    _pollTimers.set(docId, timer)
  }

  function stopPolling(docId) {
    if (_pollTimers.has(docId)) {
      clearInterval(_pollTimers.get(docId))
      _pollTimers.delete(docId)
    }
  }

  function stopAllPolling() {
    for (const [docId, timer] of _pollTimers) {
      clearInterval(timer)
    }
    _pollTimers.clear()
  }

  async function deleteDocument(id) {
    await documentApi.delete(id)
    stopPolling(id)
    documents.value = documents.value.filter((d) => d.id !== id)
  }

  return { documents, uploading, loadDocuments, uploadDocument, deleteDocument, stopAllPolling }
})
