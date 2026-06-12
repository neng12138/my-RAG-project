"""
Pydantic Schemas — 会话相关
"""
from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
