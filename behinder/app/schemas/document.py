"""
Pydantic Schemas — 文档相关
"""
from pydantic import BaseModel
from datetime import datetime


class DocumentOut(BaseModel):
    id: str
    name: str
    status: str
    chunk_count: int
    error_message: str | None = None
    collection_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
