<template>
  <div class="app-layout">
    <Sidebar @open-docs="showUpload = true" />
    <main class="main-content">
      <HomeView />
    </main>
    <!-- UploadPanel 统一由 HomeView 管理（通过 provide/inject 共享 showUpload 状态） -->
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import HomeView from '@/views/HomeView.vue'

const showUpload = ref(false)
// 提供给 HomeView 注入，统一控制 UploadPanel
provide('showUpload', showUpload)
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  /* Firefox 滚动条兼容 */
  scrollbar-width: thin;
  scrollbar-color: #d0d0d0 transparent;
}

body {
  background: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  color: #1a1a1a;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 2px; }

.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
