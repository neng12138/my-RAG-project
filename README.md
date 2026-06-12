1. 项目概况
RAG 智能检索助手是一个基于检索增强生成（Retrieval-Augmented Generation）的智能问答系统。用户上传文档（PDF/TXT/Markdown/Word）后，系统自动将文档向量化并建立索引，用户在对话中提问时，Agent 自动检索知识库中的相关内容，结合大语言模型生成准确、有据可查的回答。

核心能力
文档上传与自动处理（分块 → 向量化 → 索引）
智能 Agent 自主决策是否需要检索知识库
混合检索（向量语义检索 + BM25 关键词检索）
重排序精排（阿里云百炼 qwen3-rerank）
流式 SSE 输出（逐 token 实时渲染）
会话管理（多轮对话 + 历史记录持久化）

ReAct Agent 工作流
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
