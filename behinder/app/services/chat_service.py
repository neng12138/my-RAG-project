"""
聊天服务 — 调用 ReAct Agent 处理对话，支持流式输出
"""
import os
import sys
import json
import logging
from pathlib import Path

_PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))

from langchain_core.messages import HumanMessage, AIMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_agent():
    """获取已预热的 Agent（需在 lifespan 中先调用 initialize_agent）"""
    from agent_rag.agent.react_agent import get_agent
    agent, llm, embeddings = get_agent()
    return agent


async def _extract_content(chunk) -> str | None:
    """从 message chunk 中提取文本内容"""
    if hasattr(chunk, "content"):
        content = chunk.content
        # 字符串内容直接返回
        if isinstance(content, str) and content.strip():
            return content
        # 列表内容（多模态 / 结构化输出）
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif isinstance(block, str):
                    texts.append(block)
            result = "".join(texts)
            if result.strip():
                return result
    return None


async def stream_chat(
    session_id: str,
    message: str,
    history: list[dict],
):
    """
    流式调用 Agent，以 SSE 格式 yield token

    使用 astream_events API 获取更稳定的逐 token 流式输出。
    """
    agent = _get_agent()

    # 构造消息列表
    messages = []
    for h in history:
        if h["role"] == "user":
            messages.append(HumanMessage(content=h["content"]))
        else:
            messages.append(AIMessage(content=h["content"]))
    messages.append(HumanMessage(content=message))

    has_output = False
    try:
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2",
        ):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk is None:
                    continue
                content = await _extract_content(chunk)
                if content:
                    has_output = True
                    yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"

            elif kind == "on_chat_model_end":
                pass

    except Exception as e:
        logger.exception(f"Agent stream error for session {session_id}")
        yield f"data: {json.dumps({'type': 'error', 'content': f'AI 处理出错: {str(e)}'}, ensure_ascii=False)}\n\n"

    # 兜底：如果没有任何 token 输出，返回提示
    if not has_output:
        yield f"data: {json.dumps({'type': 'token', 'content': '抱歉，没有生成回复内容，请重试。'}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'content': ''}, ensure_ascii=False)}\n\n"
