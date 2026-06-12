"""
文档服务 — 处理文档上传、解析、入库
"""
import os
import sys
import asyncio
from pathlib import Path

# 将 agent_rag 包加入路径
_PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import crud
from app.core.config import settings


async def process_document_async(
    doc_id: str,
    file_path: str,
    collection_name: str,
    db_url: str,
):
    """
    后台异步处理文档（分块 + 向量化 + BM25 索引）
    在独立任务中运行，不阻塞请求
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    # 创建独立的数据库连接
    engine = create_async_engine(db_url, connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        from agent_rag.rag.ingestion.loader import load_document
        from agent_rag.rag.ingestion.splitter import split_documents
        from agent_rag.rag.ingestion.embedder import embed_and_store, get_embeddings

        # 加载文档
        docs = load_document(file_path)

        # 检查是否成功提取到内容
        total_content_len = sum(len(d.page_content.strip()) for d in docs)
        if total_content_len == 0:
            raise ValueError(
                "无法从文件中提取文本内容。\n"
                "可能原因：\n"
                "1. PDF 是扫描版（图片格式），需要 OCR 才能识别文字\n"
                "2. 文件已损坏或为空\n"
                "3. 文件编码不支持"
            )

        # 分块
        chunks = split_documents(
            docs,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        if not chunks:
            raise ValueError("文档分块失败：分块数量为 0，请检查文档内容是否有效")

        # Embedding 模型
        embeddings = get_embeddings(
            settings.openai_api_key,
            settings.openai_base_url,
            settings.embedding_model,
        )

        # 向量化 + BM25 入库（同步操作，用 run_in_executor 避免阻塞）
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: embed_and_store(
                chunks,
                collection_name,
                settings.chroma_persist_dir,
                settings.bm25_index_dir,
                embeddings,
            ),
        )

        # 更新状态
        async with session_factory() as session:
            await crud.update_document_status(session, doc_id, "done", len(chunks))
            await session.commit()

    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"[DocumentService] 处理文档 {doc_id} 失败: {err_msg}")
        async with session_factory() as session:
            await crud.update_document_status(
                session, doc_id, "failed", error_message=err_msg
            )
            await session.commit()
    finally:
        await engine.dispose()
