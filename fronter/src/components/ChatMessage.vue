<template>
  <div class="message-wrap" :class="msg.role">
    <!-- 用户消息 -->
    <div v-if="msg.role === 'user'" class="user-bubble">
      <span class="content">{{ msg.content }}</span>
    </div>

    <!-- AI 消息 -->
    <div v-else class="assistant-wrap">
      <div class="avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 12h8M12 8v8" stroke="white" stroke-width="2" fill="none"/>
        </svg>
      </div>
      <div class="assistant-body">
        <div
          v-if="msg.thinking"
          class="thinking"
        >
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <div
          v-else
          class="content markdown-body"
          v-html="renderMarkdown(msg.content)"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// 全局 marked 配置（模块级别，只执行一次）
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

const props = defineProps({
  msg: { type: Object, required: true },
})

/**
 * 渲染 Markdown 并过滤 XSS 攻击向量
 * - 移除 <script> 标签
 * - 移除 on* 事件属性
 * - 移除 javascript: 协议链接
 * - 移除 <iframe>/<object>/<embed> 标签
 */
function renderMarkdown(text) {
  if (!text) return ''
  let html = marked.parse(text)
  // 移除危险标签
  html = html.replace(/<script[\s\S]*?<\/script>/gi, '')
  html = html.replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
  html = html.replace(/<object[\s\S]*?<\/object>/gi, '')
  html = html.replace(/<embed[\s\S]*?>/gi, '')
  // 移除 on* 事件属性（含各种引号/无引号）
  html = html.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')
  // 移除 javascript: 协议
  html = html.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"')
  return html
}
</script>

<style scoped>
.message-wrap {
  padding: 4px 0;
}

/* 用户消息 */
.user-bubble {
  display: flex;
  justify-content: flex-end;
  padding: 2px 0 2px 60px;
}
.user .content {
  background: #e8e8f0;
  color: #1a1a1a;
  padding: 10px 16px;
  border-radius: 18px 18px 4px 18px;
  font-size: 14px;
  line-height: 1.6;
  max-width: 80%;
  word-break: break-word;
  white-space: pre-wrap;
}

/* AI 消息 */
.assistant-wrap {
  display: flex;
  gap: 12px;
  padding: 2px 60px 2px 0;
  align-items: flex-start;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.assistant-body {
  flex: 1;
  min-width: 0;
}

.content {
  color: #1a1a1a;
  font-size: 14px;
  line-height: 1.75;
}

/* 思考中动画 */
.thinking {
  display: flex;
  gap: 5px;
  padding: 12px 0;
}
.dot {
  width: 7px;
  height: 7px;
  background: #4f46e5;
  border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

/* Markdown 样式 */
.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  color: #1a1a1a;
  margin: 16px 0 8px;
  font-weight: 600;
}
.markdown-body :deep(code) {
  background: #f0f0f0;
  color: #e74c3c;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.markdown-body :deep(pre) {
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 8px 0;
}
.markdown-body :deep(pre code) {
  background: none;
  color: #333;
  padding: 0;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid #4f46e5;
  padding-left: 12px;
  color: #666;
  margin: 8px 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) { padding-left: 20px; margin: 6px 0; }
.markdown-body :deep(li) { margin: 3px 0; }
.markdown-body :deep(table) { width: 100%; border-collapse: collapse; margin: 8px 0; }
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #ddd;
  padding: 6px 12px;
  text-align: left;
}
.markdown-body :deep(th) { background: #f5f5f5; }
.markdown-body :deep(a) { color: #4f46e5; }
</style>
