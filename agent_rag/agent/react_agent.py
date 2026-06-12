"""
ReAct Agent — 基于 LangGraph 的主 Agent

初始化策略：在 FastAPI lifespan 中调用 initialize_agent() 预热，
后续 get_agent() 直接返回已构建好的实例（无锁竞争）。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent_rag.rag.ingestion.embedder import DashScopeEmbeddings
from agent_rag.prompts.agent_prompt import AGENT_SYSTEM_PROMPT
from agent_rag.tools.rag_tool import create_default_rag_tool

# 全局单例（由 initialize_agent 填充）
_agent_instance = None
_llm_instance = None
_embeddings_instance = None


def build_react_agent(settings):
    """
    构建 LangGraph ReAct Agent

    Args:
        settings: 配置对象（来自 behinder/app/core/config.py）

    Returns:
        (agent, llm, embeddings)
    """
    # ── 初始化 LLM ──
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.llm_model,
        temperature=0.3,
        streaming=True,
    )

    # ── 初始化 Embedding 模型（阿里云百炼 dashscope SDK） ──
    embeddings = DashScopeEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )

    # ── 创建 RAG 工具 ──
    rag_tool = create_default_rag_tool(llm, embeddings, settings)
    tools = [rag_tool]

    # ── 构建 ReAct Agent ──
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=AGENT_SYSTEM_PROMPT,
    )

    return agent, llm, embeddings


async def initialize_agent(settings):
    """
    预热 Agent 单例（在 FastAPI lifespan 中调用）

    通过提前构建避免首次请求时的懒加载延迟和竞态条件。
    """
    global _agent_instance, _llm_instance, _embeddings_instance
    if _agent_instance is None:
        print("[Agent] 正在预热 Agent（首次构建）...")
        _agent_instance, _llm_instance, _embeddings_instance = build_react_agent(settings)
        print("[Agent] Agent 预热完成")
    return _agent_instance, _llm_instance, _embeddings_instance


def get_agent():
    """
    获取 Agent 单例（必须在 initialize_agent 之后调用）

    Returns:
        (agent, llm, embeddings)
    """
    if _agent_instance is None:
        raise RuntimeError(
            "Agent 尚未初始化，请确保在 FastAPI lifespan 中调用了 initialize_agent()"
        )
    return _agent_instance, _llm_instance, _embeddings_instance
