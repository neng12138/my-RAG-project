<template>
  <div class="upload-overlay" @click.self="$emit('close')">
    <div class="upload-panel">
      <div class="panel-header">
        <h3>知识库管理</h3>
        <button class="close-btn" @click="$emit('close')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- 上传区域 -->
      <div
        class="drop-zone"
        :class="{ dragover }"
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="handleDrop"
        @click="fileInputRef.click()"
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <p>点击或拖拽文件到此处上传</p>
        <p class="sub">支持 PDF、TXT、Markdown、Word</p>
        <input
          ref="fileInputRef"
          type="file"
          accept=".pdf,.txt,.md,.docx"
          multiple
          style="display:none"
          @change="handleFileSelect"
        />
      </div>

      <!-- 上传进度 -->
      <div v-if="docStore.uploading" class="uploading-tip">
        <span class="spin">⟳</span> 正在处理文档...
      </div>

      <!-- 文档列表 -->
      <div class="doc-list">
        <div v-if="docStore.documents.length === 0" class="empty">暂无文档</div>
        <div
          v-for="doc in docStore.documents"
          :key="doc.id"
          class="doc-item"
        >
          <div class="doc-info">
            <span class="doc-name">{{ doc.name }}</span>
            <span class="doc-meta">{{ doc.chunk_count }} 块 · {{ formatStatus(doc.status) }}</span>
            <span v-if="doc.status === 'failed' && doc.error_message" class="doc-error">
              ⚠️ {{ doc.error_message }}
            </span>
          </div>
          <div class="doc-actions">
            <span class="status-badge" :class="doc.status">{{ statusText(doc.status) }}</span>
            <button class="del-btn" @click="docStore.deleteDocument(doc.id)">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDocumentStore } from '@/stores/documentStore'

const emit = defineEmits(['close'])
const docStore = useDocumentStore()
const fileInputRef = ref(null)
const dragover = ref(false)

onMounted(() => docStore.loadDocuments())

async function handleDrop(e) {
  dragover.value = false
  const files = Array.from(e.dataTransfer.files)
  for (const f of files) await docStore.uploadDocument(f)
}

async function handleFileSelect(e) {
  const files = Array.from(e.target.files)
  for (const f of files) await docStore.uploadDocument(f)
  e.target.value = ''
}

function formatStatus(s) {
  return { processing: '处理中', done: '已就绪', failed: '失败' }[s] || s
}

function statusText(s) {
  return { processing: '处理中', done: '就绪', failed: '失败' }[s] || s
}
</script>

<style scoped>
.upload-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 16px;
  width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e5e5;
}
.panel-header h3 { color: #1a1a1a; font-size: 15px; margin: 0; }

.close-btn {
  border: none;
  background: none;
  color: #999;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
}
.close-btn:hover { color: #333; background: #f0f0f0; }

.drop-zone {
  margin: 16px 20px;
  border: 1.5px dashed #d0d0d0;
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.drop-zone:hover, .drop-zone.dragover {
  border-color: #4f46e5;
  background: #f0efff;
}
.drop-zone p { color: #666; font-size: 13px; margin: 8px 0 0; }
.drop-zone .sub { color: #aaa; font-size: 11px; margin-top: 4px; }

.uploading-tip {
  text-align: center;
  color: #666;
  font-size: 13px;
  padding: 8px;
}
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.doc-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 16px;
}
.empty { text-align: center; color: #aaa; font-size: 13px; padding: 20px 0; }

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  margin-bottom: 6px;
  background: #fafafa;
}
.doc-info { flex: 1; min-width: 0; }
.doc-name { display: block; color: #333; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-meta { display: block; color: #aaa; font-size: 11px; margin-top: 2px; }
.doc-error { display: block; color: #f56c6c; font-size: 11px; margin-top: 4px; line-height: 1.4; max-height: 48px; overflow-y: auto; }
.doc-actions { display: flex; align-items: center; gap: 8px; }

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.status-badge.done { background: #e6f7e6; color: #52c41a; }
.status-badge.processing { background: #e6f0ff; color: #4f8ef7; }
.status-badge.failed { background: #ffe6e6; color: #f56c6c; }

.del-btn {
  border: none;
  background: none;
  color: #bbb;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}
.del-btn:hover { color: #f56c6c; background: #ffe6e6; }
</style>
