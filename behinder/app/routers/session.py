"""
路由 — 会话管理
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.db import crud
from app.schemas.session import SessionCreate, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/create", response_model=SessionOut)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = await crud.create_session(db, title=body.title)
    return session


@router.get("/list", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await crud.list_sessions(db)


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    await crud.delete_session(db, session_id)
    return {"message": "deleted"}
