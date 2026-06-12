"""
路由 — 聊天对话（SSE 流式输出）
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db import crud
from app.schemas.chat import ChatSendRequest, MessageOut
from app.services.chat_service import stream_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send")
async def send_message(
    body: ChatSendRequest,
    db: AsyncSession = Depends(get_db),
):
    # 验证会话存在
    session = await crud.get_session(db, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 验证消息非空
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 获取历史消息
    msgs = await crud.get_messages(db, body.session_id)
    history = [{"role": m.role, "content": m.content} for m in msgs]

    # 保存用户消息
    await crud.add_message(db, body.session_id, "user", body.message)
    await db.commit()

    # 收集完整回答（用于保存）
    collected_answer = []

    async def event_generator():
        async for chunk in stream_chat(body.session_id, body.message, history):
            yield chunk
            # 提取 token 内容
            try:
                data_str = chunk.replace("data: ", "").strip()
                if data_str:
                    data = json.loads(data_str)
                    if data.get("type") == "token":
                        collected_answer.append(data.get("content", ""))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # 解析失败只记录日志，不中断流
                logger.debug(f"SSE chunk 解析失败（非致命）: {e}")

        # 流结束后保存 AI 回答
        if collected_answer:
            full_answer = "".join(collected_answer)
            from app.db.base import AsyncSessionLocal
            try:
                async with AsyncSessionLocal() as save_db:
                    await crud.add_message(save_db, body.session_id, "assistant", full_answer)
                    await save_db.commit()
            except Exception as e:
                logger.warning(f"保存 AI 回答失败: {e}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}", response_model=list[MessageOut])
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = await crud.get_messages(db, session_id)
    return msgs
