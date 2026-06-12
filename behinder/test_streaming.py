"""
测试流式输出
用法: python test_streaming.py
"""
import os
import sys
import asyncio
from pathlib import Path

# Path setup
_BEHINDER = Path(__file__).resolve().parent
_PROJ_ROOT = _BEHINDER.parent
sys.path.insert(0, str(_PROJ_ROOT))
os.chdir(str(_BEHINDER))

from app.core.config import Settings
from langchain_core.messages import HumanMessage
from agent_rag.agent.react_agent import build_react_agent


async def test_streaming():
    settings = Settings()

    print(f"LLM Model: {settings.llm_model}")
    print(f"Base URL: {settings.openai_base_url}")

    print("Building Agent...")
    agent, llm, embeddings = build_react_agent(settings)
    print("Agent built OK")

    # Test 1: astream_events
    messages = [HumanMessage(content="你好，请用一句话介绍你自己")]
    print("\n=== Test 1: astream_events (v2) ===")

    token_count = 0
    full_content = ""

    async for event in agent.astream_events({"messages": messages}, version="v2"):
        kind = event.get("event", "")
        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content"):
                content = chunk.content
                if isinstance(content, str) and content:
                    token_count += 1
                    full_content += content
                    print(content, end="", flush=True)

    print(f"\n\nTokens: {token_count}, Chars: {len(full_content)}")
    print(f"Content: {full_content[:200]}")
    assert full_content, "FAIL: astream_events produced no tokens!"
    print("PASS: astream_events")

    # Test 2: stream_mode="messages"
    print("\n=== Test 2: stream_mode='messages' ===")
    full_content2 = ""
    async for chunk in agent.astream({"messages": messages}, stream_mode="messages"):
        if isinstance(chunk, tuple):
            msg, _ = chunk
        else:
            msg = chunk
        if hasattr(msg, "content") and isinstance(msg.content, str):
            full_content2 += msg.content
            print(msg.content, end="", flush=True)

    print(f"\nChars: {len(full_content2)}")
    assert full_content2, "FAIL: stream_mode=messages produced no content!"
    print("PASS: stream_mode=messages")

    print("\n=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_streaming())
