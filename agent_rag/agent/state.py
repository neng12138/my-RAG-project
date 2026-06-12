"""
Agent 状态定义 — LangGraph AgentState
"""
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """ReAct Agent 的状态结构"""
    messages: Annotated[list, add_messages]    # 对话历史（自动累加）
    query: str                                  # 当前用户查询
    tool_output: Optional[str]                  # 工具执行结果
    final_answer: Optional[str]                 # 最终回答
    iteration_count: int                        # 当前迭代次数（防止无限循环）
