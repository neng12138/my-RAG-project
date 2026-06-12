"""
Pydantic Schemas — 聊天相关
"""
import json
from pydantic import BaseModel, field_validator
from datetime import datetime


class ChatSendRequest(BaseModel):
    session_id: str
    message: str
    stream: bool = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    sources: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("sources", mode="before")
    @classmethod
    def parse_sources(cls, v):
        """从数据库读取时 sources 是 JSON 字符串，需转换为 list"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v
