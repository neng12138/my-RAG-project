"""
LangGraph RAG 工具链图（可独立调试）
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from agent_rag.agent.state import AgentState


def create_simple_rag_graph(rag_tool_fn):
    """
    创建一个简单的 RAG 工具链图（主要用于调试和独立测试）

    Args:
        rag_tool_fn: callable，接收 query 返回 str

    Returns:
        compiled LangGraph
    """

    def run_rag(state: AgentState) -> AgentState:
        query = state["query"]
        result = rag_tool_fn(query)
        state["tool_output"] = result
        return state

    graph = StateGraph(AgentState)
    graph.add_node("rag", run_rag)
    graph.add_edge(START, "rag")
    graph.add_edge("rag", END)

    return graph.compile()
