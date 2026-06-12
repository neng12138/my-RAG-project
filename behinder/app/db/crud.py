"""
数据库 CRUD 操作
"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models import Session, Message, Document


# ============================================================
# Session CRUD
# ============================================================

async def create_session(db: AsyncSession, title: str = "新对话") -> Session:
    s = Session(title=title)
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def list_sessions(db: AsyncSession) -> list[Session]:
    result = await db.execute(
        select(Session).order_by(Session.updated_at.desc())
    )
    return list(result.scalars().all())


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(delete(Session).where(Session.id == session_id))
    return result.rowcount > 0


# ============================================================
# Message CRUD
# ============================================================

async def add_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    sources: list | None = None,
) -> Message:
    m = Message(
        session_id=session_id,
        role=role,
        content=content,
        sources=json.dumps(sources, ensure_ascii=False) if sources else None,
    )
    db.add(m)
    await db.flush()
    await db.refresh(m)
    return m


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


# ============================================================
# Document CRUD
# ============================================================

async def create_document(
    db: AsyncSession, name: str, file_path: str, collection_name: str = "default"
) -> Document:
    doc = Document(name=name, file_path=file_path, collection_name=collection_name)
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def update_document_status(
    db: AsyncSession,
    doc_id: str,
    status: str,
    chunk_count: int = 0,
    error_message: str | None = None,
) -> None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if doc:
        doc.status = status
        doc.chunk_count = chunk_count
        if error_message is not None:
            doc.error_message = error_message[:500]  # 限制长度


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())


async def delete_document(db: AsyncSession, doc_id: str) -> bool:
    result = await db.execute(delete(Document).where(Document.id == doc_id))
    return result.rowcount > 0


async def get_document(db: AsyncSession, doc_id: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()
