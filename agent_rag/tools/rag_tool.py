"""
RAG 工具 — rag_search_and_summarize
封装完整 RAG 链路：Query改写(HyDE) → 混合检索 → 重排序 → 摘要生成
"""
import os
import sys

from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 路径处理，确保模块可被正确导入
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from agent_rag.rag.ingestion.embedder import load_vectorstore, load_bm25_index
from agent_rag.rag.query_transform.hyde import generate_hyde_document
from agent_rag.rag.retrieval.hybrid_retriever import hybrid_retrieve
from agent_rag.rag.rerank.reranker import rerank
from agent_rag.prompts.summarize_prompt import SUMMARIZE_PROMPT


# ────────────────────────────────────────────────────────────
# 工具描述（详细、清晰）
# ────────────────────────────────────────────────────────────
RAG_TOOL_DESCRIPTION = """
【工具名称】rag_search_and_summarize

【功能简述】
从已上传的知识库文档中检索与用户问题最相关的内容，并生成结构化摘要供你参考后作答。

【完整执行流程】
1. Query 改写与扩展（HyDE）：LLM 根据用户问题生成"假设性答案文档"，利用其语义更接近答案的特性提升检索召回率
2. 混合检索（BM25 + 向量相似度）：使用关键词检索和语义向量检索两路并行检索，各取 Top10，共 20 个候选片段
3. RRF 融合去重：通过 Reciprocal Rank Fusion 算法合并两路结果，综合排名
4. 重排序（Qwen3-Rerank API）：调用阿里云百炼 rerank API 对候选片段精排，取最相关 Top5
5. 摘要生成：将 Top5 片段交给 LLM 生成结构化摘要，包含核心内容和引用来源

【使用时机 — 以下情况必须调用本工具】
✅ 用户询问已上传文档中的具体内容、数据、结论、定义
✅ 用户提出专业性问题，需要参考知识库才能准确回答
✅ 用户使用"查找"、"搜索"、"根据文档"、"知识库中"等关键词
✅ 用户提问涉及特定领域知识，仅凭通用知识无法准确回答
✅ 用户询问某个概念、方法或流程的详细说明

【不应使用本工具的情况】
❌ 用户进行日常问候、闲聊（如"你好"、"今天天气怎么样"）
❌ 用户询问你的能力或使用方法
❌ 问题是通用常识，完全不需要检索文档
❌ 用户明确要求直接回答而不需要检索

【输入参数说明】
- query (str): 用户的原始问题（必填），将作为检索的起点

【输出说明】
返回格式化字符串，包含：
- 基于知识库内容生成的摘要（直接回答用户问题）
- 引用来源列表（文档名称和片段位置）
- 如果知识库中无相关内容，明确告知

【重要说明】
本工具返回的是摘要，你（Agent）需要基于此摘要为用户生成最终的、连贯的回答。
不要直接把摘要原文返回给用户，要整合摘要内容给出流畅的回答。
"""


def create_rag_tool(
    collection_name: str,
    chroma_persist_dir: str,
    bm25_index_dir: str,
    llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
    reranker_model: str,
    api_key: str = None,
    bm25_top_k: int = 10,
    vector_top_k: int = 10,
    rerank_top_k: int = 5,
):
    """
    工厂函数：创建绑定特定知识库的 RAG 工具

    Args:
        collection_name: Chroma collection 名称
        chroma_persist_dir: Chroma 持久化目录
        bm25_index_dir: BM25 索引目录
        llm: LLM 实例
        embeddings: Embedding 模型实例
        reranker_model: 重排序模型名称
        api_key: 阿里云百炼 API Key（rerank API 需要用，为 None 则读环境变量）
        bm25_top_k: BM25 召回数
        vector_top_k: 向量召回数
        rerank_top_k: 重排序后保留数

    Returns:
        LangChain Tool
    """
    # 加载检索组件
    vectorstore = load_vectorstore(collection_name, chroma_persist_dir, embeddings)
    bm25, bm25_docs = load_bm25_index(collection_name, bm25_index_dir)

    # 摘要链
    summarize_prompt = PromptTemplate.from_template(SUMMARIZE_PROMPT)
    summarize_chain = summarize_prompt | llm | StrOutputParser()

    # 保存 api_key 到闭包
    _api_key = api_key

    async def _rag_search(query: str) -> str:
        """执行完整 RAG 检索流程，返回摘要字符串"""
        try:
            # ── Step1: Query 改写 ──
            hyde_doc = generate_hyde_document(query, llm)
            # HyDE：用假设文档做向量检索
            from agent_rag.rag.retrieval.vector_retriever import vector_retrieve
            hyde_vector_results = vector_retrieve(hyde_doc, vectorstore, top_k=vector_top_k)

            # 原始查询也做向量检索
            orig_vector_results = vector_retrieve(query, vectorstore, top_k=vector_top_k)

            # 合并向量结果（简单去重）
            seen = set()
            merged_vector = []
            for doc, score in hyde_vector_results + orig_vector_results:
                key = hash(doc.page_content)
                if key not in seen:
                    seen.add(key)
                    merged_vector.append((doc, score))

            # ── Step2: BM25 检索 ──
            if bm25 is not None and bm25_docs:
                from agent_rag.rag.retrieval.bm25_retriever import bm25_retrieve
                bm25_results = bm25_retrieve(query, bm25, bm25_docs, top_k=bm25_top_k)
            else:
                bm25_results = []

            # ── Step3: RRF 融合 ──
            from agent_rag.rag.retrieval.hybrid_retriever import reciprocal_rank_fusion
            fused = reciprocal_rank_fusion(bm25_results, merged_vector[:vector_top_k], top_k=20)

            if not fused:
                return "知识库中未找到相关内容，请先上传文档后再进行检索。"

            # ── Step4: 重排序 ──
            reranked = await rerank(query, fused, reranker_model, top_k=rerank_top_k, api_key=_api_key)

            # ── Step5: 摘要生成 ──
            context_parts = []
            sources = []
            for i, (doc, score) in enumerate(reranked):
                source_file = doc.metadata.get("source_file", "未知文档")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                context_parts.append(
                    f"[片段{i+1}] 来源：{source_file}（块#{chunk_idx}）\n{doc.page_content}"
                )
                sources.append(f"{source_file}（块#{chunk_idx}）")

            context = "\n\n---\n\n".join(context_parts)
            summary = await summarize_chain.ainvoke({"context": context, "query": query})

            # 附加引用来源
            sources_text = "\n".join(f"  • {s}" for s in sources)
            return f"{summary}\n\n**引用来源：**\n{sources_text}"

        except Exception as e:
            return f"检索过程发生错误: {str(e)}"

    # 创建 LangChain Tool（支持 async 函数）
    from langchain_core.tools import StructuredTool
    rag_tool = StructuredTool.from_function(
        coroutine=_rag_search,
        name="rag_search_and_summarize",
        description=RAG_TOOL_DESCRIPTION,
    )
    return rag_tool


def create_default_rag_tool(
    llm: ChatOpenAI,
    embeddings: OpenAIEmbeddings,
    settings,
) -> object:
    """
    使用 settings 配置创建默认 RAG 工具（用于 Agent 初始化）
    """
    return create_rag_tool(
        collection_name="default",
        chroma_persist_dir=settings.chroma_persist_dir,
        bm25_index_dir=settings.bm25_index_dir,
        llm=llm,
        embeddings=embeddings,
        reranker_model=settings.reranker_model,
        api_key=settings.openai_api_key,
        bm25_top_k=settings.bm25_top_k,
        vector_top_k=settings.vector_top_k,
        rerank_top_k=settings.rerank_top_k,
    )
