"""
FastAPI 应用入口
"""
import os
import sys
from pathlib import Path

# 确保 agent_rag 包可以被导入
_PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.core.config import settings
from app.db.base import engine, Base
from app.routers import chat, document, session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # 迁移：为 documents 表添加 error_message 列（如果不存在）
        def _migrate_add_error_message(conn_sync):
            try:
                result = conn_sync.execute(text("PRAGMA table_info(documents)"))
                columns = [row[1] for row in result.fetchall()]
                if "error_message" not in columns:
                    conn_sync.execute(
                        text("ALTER TABLE documents ADD COLUMN error_message TEXT")
                    )
                    print("[OK] Added error_message column to documents table")
            except Exception as e:
                print(f"[WARN] Migration check failed: {e}")

        await conn.run_sync(_migrate_add_error_message)

    # 预热 Agent（避免首次请求延迟 + 避免竞态条件）
    try:
        from agent_rag.agent.react_agent import initialize_agent
        await initialize_agent(settings)
    except Exception as e:
        print(f"[WARN] Agent warmup failed: {e}")

    print("[OK] Application startup complete")
    yield
    await engine.dispose()


app = FastAPI(
    title="RAG 智能检索助手 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router)
app.include_router(document.router)
app.include_router(session.router)


@app.get("/")
async def root():
    return {"message": "RAG 智能检索助手 API 运行中", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}
