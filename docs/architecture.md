# RAG 智能检索助手 — 架构与技术栈文档

> 版本：v1.0 | 日期：2026-06-12

---

## 目录

1. [项目概况](#1-项目概况)
2. [技术栈](#2-技术栈)
3. [项目目录结构](#3-项目目录结构)
4. [整体架构](#4-整体架构)
5. [API 端点](#5-api-端点)
6. [数据库模型](#6-数据库模型)
7. [RAG 管线详解](#7-rag-管线详解)
8. [配置说明](#8-配置说明)
9. [启动方式](#9-启动方式)

---

## 1. 项目概况

**RAG 智能检索助手**是一个基于检索增强生成（Retrieval-Augmented Generation）的智能问答系统。用户上传文档（PDF/TXT/Markdown/Word）后，系统自动将文档向量化并建立索引，用户在对话中提问时，Agent 自动检索知识库中的相关内容，结合大语言模型生成准确、有据可查的回答。

### 核心能力

- 文档上传与自动处理（分块 → 向量化 → 索引）
- 智能 Agent 自主决策是否需要检索知识库
- 混合检索（向量语义检索 + BM25 关键词检索）
- 重排序精排（阿里云百炼 qwen3-rerank）
- 流式 SSE 输出（逐 token 实时渲染）
- 会话管理（多轮对话 + 历史记录持久化）

---

## 2. 技术栈

### 2.1 前端

| 技术 | 用途 |
|------|------|
| Vue 3（组合式 API） | 渐进式前端框架 |
| Vite 5 | 构建工具与开发服务器 |
| Pinia 2 | 状态管理 |
| Axios | HTTP 客户端 |
| marked + highlight.js | Markdown 渲染 + 代码高亮 |

### 2.2 后端

| 技术 | 用途 |
|------|------|
| FastAPI | 异步 Web 框架 |
| Uvicorn | ASGI 服务器 |
| Pydantic 2 + pydantic-settings | 数据校验与配置管理 |
| SQLAlchemy 2 + aiosqlite | 异步 ORM + SQLite 驱动 |
| httpx + aiofiles | 异步 HTTP + 异步文件 I/O |

### 2.3 AI / RAG 框架

| 技术 | 用途 |
|------|------|
| LangChain 1.x | RAG 链路编排 |
| langchain-openai | LLM 调用（OpenAI 兼容接口） |
| langchain-chroma | Chroma 向量库集成 |
| langchain-community | 文档加载器 |
| LangGraph 1.x | ReAct Agent 状态机 |
| Chroma 1.x | 向量数据库（本地持久化） |
| rank-bm25 | BM25 关键词检索 |
| jieba | 中文分词 |
| sentence-transformers | 本地 Cross-Encoder（备用重排序） |
| dashscope SDK | 阿里云百炼 Embedding API |

### 2.4 文档解析

| 技术 | 用途 |
|------|------|
| PyMuPDF (fitz) | PDF 文档解析（优先） |
| python-docx | Word 文档解析 |
| pypdf | PDF 解析（回退方案） |

### 2.5 模型配置（阿里云百炼 DashScope）

| 用途 | 模型 | 调用方式 |
|------|------|----------|
| 对话生成（主 LLM） | qwen-plus | OpenAI 兼容接口 `ChatOpenAI` |
| 文本向量化 | text-embedding-v2 (1536维) | DashScope SDK |
| 重排序 | qwen3-rerank | HTTP POST `/compatible-api/v1/reranks` |

---

## 3. 项目目录结构

```
case01/
│
├── .gitignore                      # Git 忽略规则
│
├── docs/
│   └── architecture.md             # 本文档
│
├── behinder/                       # 【后端 — FastAPI】
│   ├── .env                        # 环境变量（API Key 等敏感信息）
│   ├── .env.example                # 环境变量模板
│   ├── requirements.txt            # Python 依赖清单
│   └── app/
│       ├── main.py                 # FastAPI 入口（lifespan / router / CORS）
│       ├── core/
│       │   ├── config.py           # 全局配置（读取 .env）
│       │   └── dependencies.py     # 依赖注入（DB Session）
│       ├── routers/
│       │   ├── chat.py             # 聊天路由
│       │   ├── document.py         # 文档管理路由
│       │   └── session.py          # 会话管理路由
│       ├── services/
│       │   ├── chat_service.py     # 聊天业务逻辑
│       │   └── document_service.py # 文档后台异步处理
│       ├── schemas/
│       │   ├── chat.py             # 聊天 Pydantic 模型
│       │   ├── document.py         # 文档 Pydantic 模型
│       │   └── session.py          # 会话 Pydantic 模型
│       ├── db/
│       │   ├── base.py             # SQLAlchemy 异步引擎
│       │   ├── models.py           # ORM 模型
│       │   └── crud.py             # 数据库 CRUD
│       └── utils/
│           └── file_utils.py       # 文件上传/验证工具
│
├── agent_rag/                      # 【Agent + RAG 核心模块】
│   ├── agent/
│   │   ├── react_agent.py          # LangGraph ReAct Agent 构建
│   │   └── state.py                # Agent 状态定义
│   ├── tools/
│   │   └── rag_tool.py             # RAG 工具封装（完整链路）
│   ├── graph/
│   │   └── rag_graph.py            # 独立 RAG 图
│   ├── rag/
│   │   ├── ingestion/
│   │   │   ├── loader.py           # 多格式文档加载
│   │   │   ├── splitter.py         # 文本分块
│   │   │   └── embedder.py         # 向量化 + Chroma 入库 + BM25 索引
│   │   ├── retrieval/
│   │   │   ├── vector_retriever.py # Chroma 向量检索
│   │   │   ├── bm25_retriever.py   # BM25 关键词检索
│   │   │   └── hybrid_retriever.py # RRF 融合
│   │   ├── rerank/
│   │   │   └── reranker.py         # 重排序
│   │   └── query_transform/
│   │       ├── hyde.py             # HyDE 假设文档生成
│   │       └── multi_query.py      # 多查询扩展
│   └── prompts/
│       ├── agent_prompt.py         # Agent 系统提示词
│       ├── hyde_prompt.py          # HyDE + Multi-Query 提示词
│       └── summarize_prompt.py     # 摘要生成提示词
│
├── fronter/                        # 【前端 — Vue 3 + Vite】
│   ├── package.json
│   ├── vite.config.js              # Vite 配置（API 代理）
│   ├── index.html
│   └── src/
│       ├── main.js                 # Vue 应用入口
│       ├── App.vue                 # 根组件
│       ├── api/
│       │   ├── request.js          # Axios 实例
│       │   ├── chat.js             # 会话 API
│       │   └── document.js         # 文档 API
│       ├── stores/
│       │   ├── chatStore.js        # 聊天状态管理
│       │   └── documentStore.js    # 文档状态管理
│       ├── components/
│       │   ├── ChatMessage.vue     # 消息气泡
│       │   ├── ChatInput.vue       # 输入框
│       │   ├── Sidebar.vue         # 侧边栏
│       │   └── UploadPanel.vue     # 文档上传面板
│       └── views/
│           └── HomeView.vue        # 主聊天页面
│
└── data/                           
    ├── app.db                      # SQLite 数据库
    ├── chroma/                     # Chroma 向量库持久化
    ├── bm25/                       # BM25 索引序列化
    └── uploads/                    # 上传的原始文件
```

---

## 4. 整体架构

### 4.1 三层架构

```
┌──────────────────────────────────────────────────────────────────┐
│                    前端 (Vue 3 + Pinia)                           │
│   Sidebar │ ChatMessage + ChatInput │ UploadPanel                │
└───────────────────────────────┬──────────────────────────────────┘
                                │ HTTP REST + SSE (流式)
                                │ Vite Proxy: /api → :8000
┌───────────────────────────────┼──────────────────────────────────┐
│                    后端 (FastAPI)                                 │
│                                                                  │
│  Routers:  /api/chat  /api/documents  /api/sessions              │
│  Services: chat_service.py  document_service.py                  │
│  DB:       SQLAlchemy + aiosqlite                                │
│                                                                  │
│  生命周期:  建表 + 迁移 + Agent 预热                              │
└───────────────────────────────┬──────────────────────────────────┘
                                │ 直接导入调用
┌───────────────────────────────┼──────────────────────────────────┐
│                  agent_rag 模块                                   │
│                                                                  │
│  LangGraph ReAct Agent (react_agent.py)                          │
│  ├── LLM: ChatOpenAI (qwen-plus)                                 │
│  ├── Tool: rag_search_and_summarize (rag_tool.py)                │
│  │    ├── HyDE 查询改写                                          │
│  │    ├── 向量检索 (Chroma) + BM25 检索 (rank-bm25 + jieba)     │
│  │    ├── RRF 融合                                               │
│  │    ├── 重排序 (qwen3-rerank)                                  │
│  │    └── LLM 摘要生成                                           │
│  └── System Prompt (agent_prompt.py)                             │
└──────────────────────────────────────────────────────────────────┘

持久化存储:
  ├── SQLite (data/app.db)         — 会话、消息、文档元数据
  ├── Chroma (data/chroma/)        — 向量嵌入
  └── BM25 pickle (data/bm25/)     — 关键词索引
```

### 4.2 ReAct Agent 工作流

```
用户提问
    │
    ▼
[Agent Node]  LLM 思考 (Thought)
    │
    ├── 需要检索 ──→ [rag_search_and_summarize Tool]
    │                    ├── HyDE 查询改写
    │                    ├── 混合检索 (向量 + BM25)
    │                    ├── RRF 融合
    │                    ├── 重排序
    │                    └── 摘要生成
    │                    │
    │                    └──→ 返回摘要 (Observation)
    │                         │
    │                         └──→ 回到 Agent Node (再次思考)
    │
    └── 直接回答 ──→ [最终回答] (SSE 流式输出)
```

### 4.3 前端组件通信

```
App.vue
├── provide('showUpload', ref)           ← 共享状态
│
├── Sidebar.vue
│   ├── @openDocs → 打开上传面板
│   ├── 调用 chatStore (会话 CRUD)
│   └── chatStore.switchSession()
│
└── HomeView.vue
    ├── inject('showUpload')             ← 接收共享状态
    ├── ChatMessage.vue
    │   └── marked + highlight.js 渲染
    ├── ChatInput.vue
    │   ├── @send → handleSend()
    │   └── @uploadClick → 打开上传面板
    └── UploadPanel.vue
        ├── @close → 关闭上传面板
        └── 调用 documentStore (上传/轮询/删除)
```

---

## 5. API 端点

### 5.1 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | API 根信息 |
| GET | `/health` | 健康检查 |

### 5.2 聊天对话 `/api/chat`

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| POST | `/api/chat/send` | 发送消息（SSE 流式） | `{ session_id, message, stream? }` |
| GET | `/api/chat/history/{session_id}` | 获取历史消息 | — |

SSE 事件格式：

```json
{"type": "token", "content": "这是"}
{"type": "done", "content": ""}
{"type": "error", "content": "错误信息"}
```

### 5.3 文档管理 `/api/documents`

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| POST | `/api/documents/upload` | 上传文档（异步处理） | Multipart `file` |
| GET | `/api/documents/list` | 文档列表 | — |
| DELETE | `/api/documents/{doc_id}` | 删除文档 | — |

### 5.4 会话管理 `/api/sessions`

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| POST | `/api/sessions/create` | 创建会话 | `{ title }` |
| GET | `/api/sessions/list` | 会话列表 | — |
| DELETE | `/api/sessions/{session_id}` | 删除会话 | — |

---

## 6. RAG 管线详解

### 6.1 文档入库流程

```
用户上传文件 (PDF/TXT/Markdown/Word)
    │
    ├── 1. 格式校验 (validate_file_extension)
    ├── 2. 保存到 data/uploads/{uuid}.ext
    ├── 3. 创建数据库记录 (status=processing)
    │
    └── 4. 后台异步任务 (asyncio.create_task)
            ├── loader.load_document()   → 按扩展名选择加载器
            ├── splitter.split_documents() → RecursiveCharacterTextSplitter (chunk=512, overlap=64)
            ├── embedder.get_embeddings()  → DashScope text-embedding-v2
            └── embedder.embed_and_store() → Chroma 向量化 + BM25 索引 (jieba分词)
                    │
                    └── 更新 DB: status=done/failed, chunk_count
```

### 6.2 查询检索流程

```
用户提问 (raw_query)
    │
    ├── Step 1: HyDE 查询改写
    │   └── LLM 生成"假设答案文档" (200-400字)
    │       └── 用假设文档 Embedding 代替原始 query Embedding
    │
    ├── Step 2: 混合检索
    │   ├── 向量检索 (Chroma 语义相似度, top_k=10)
    │   ├── BM25 检索 (jieba 分词 + BM25Okapi, top_k=10)
    │   └── RRF 融合 (Reciprocal Rank Fusion, k=60)
    │       └── 公式: score(d) = SUM( 1 / (60 + rank_i(d)) )
    │       └── 结果: TopK=20 去重排序
    │
    ├── Step 3: 重排序
    │   ├── 主力: 阿里云百炼 qwen3-rerank API
    │   ├── 备用: 本地 CrossEncoder (sentence-transformers)
    │   └── 降级: 保持原始顺序
    │   └── 结果: TopK=5 最相关片段
    │
    └── Step 4: 摘要生成
        └── LLM 基于 Top5 片段生成结构化摘要 (200-600字)
            └── 附引用来源（文档名 + 块编号）
            └── 返回给 Agent 作为 Observation
```

### 6.3 文档删除清理

```
DELETE /api/documents/{doc_id}
    │
    ├── 1. 删除物理文件 (data/uploads/{file})
    ├── 2. 从 Chroma 删除向量 (vs.delete)
    ├── 3. 从 BM25 索引移除对应文档 (过滤 docs → 重建 BM25Okapi)
    └── 4. 删除数据库记录
```

### 6.4 组件调用关系

| 组件 | 输入 | 输出 | 调用方 |
|------|------|------|--------|
| `loader.py` | 文件路径 | `List[Document]` | `document_service.py` |
| `splitter.py` | `List[Document]` | 分块后的 `List[Document]` | `document_service.py` |
| `embedder.py` | chunks + collection | Chroma 向量 + BM25 pickle | `document_service.py` |
| `hyde.py` | query + LLM | 假设文档字符串 | `rag_tool.py` |
| `vector_retriever.py` | query + vs + k | `[(Document, score)]` | `rag_tool.py` |
| `bm25_retriever.py` | query + bm25 + docs + k | `[(Document, score)]` | `rag_tool.py` |
| `hybrid_retriever.py` | 两路结果 | RRF 融合结果 | `rag_tool.py` |
| `reranker.py` | query + candidates + k | 重排序结果 | `rag_tool.py` |
| `rag_tool.py` | query | 摘要字符串 | Agent (LangGraph) |
| `react_agent.py` | settings | Agent 实例 | `main.py` (lifespan) |

---

## 7. 配置说明

### 7.1 环境变量 (behinder/.env)

```env
# LLM 配置（阿里云百炼兼容模式）
OPENAI_API_KEY=your_dashscope_api_key_here
DASHSCOPE_API_KEY=your_dashscope_api_key_here
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.7-plus

# 嵌入与重排序
EMBEDDING_MODEL=text-embedding-v2
RERANKER_MODEL=qwen3-rerank

# RAG 参数
CHUNK_SIZE=512
CHUNK_OVERLAP=64
BM25_TOP_K=10
VECTOR_TOP_K=10
RERANK_TOP_K=5

# 服务配置
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 7.2 数据目录

所有运行时数据自动存储在项目根目录的 `data/` 下：

| 路径 | 内容 |
|------|------|
| `data/app.db` | SQLite 数据库 |
| `data/chroma/` | Chroma 向量库持久化 |
| `data/bm25/` | BM25 索引序列化文件 |
| `data/uploads/` | 上传的原始文件 |

路径通过 `config.py` 动态计算（基于 `__file__` 解析项目根目录），支持任意目录 clone 后直接运行。

---

## 8. 启动方式

```bash
# 1. 安装依赖
cd behinder
pip install -r requirements.txt

cd fronter
npm install

# 2. 配置环境变量
编辑 behinder/.env，填入 API Key

# 3. 启动后端 (终端 1)
cd behinder
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. 启动前端 (终端 2)
cd fronter
npm run dev

# 5. 访问 http://localhost:5173
```

---

## 关键设计特点

| 特点 | 说明 |
|------|------|
| **ReAct Agent** | Agent 自主决策是否检索，适应混合场景 |
| **HyDE 增强** | LLM 生成假设答案提升向量检索召回率 |
| **混合检索** | BM25 + 向量双路召回，RRF 融合互补 |
| **重排序** | qwen3-rerank API 精排，失败自动降级 |
| **异步全链路** | FastAPI async + httpx + asyncio.create_task，全程非阻塞 |
| **流式 SSE** | agent.astream_events v2 实现逐 token 输出 |
| **Agent 预热** | lifespan 中提前构建，避免首次请求延迟 |
| **增量索引** | BM25 新文档追加合并，支持累积索引 |
| **安全防护** | XSS 过滤 + 消息校验 + 文件格式白名单 |
| **路径自适应** | 所有路径基于 `__file__` 动态计算，clone 即用 |
