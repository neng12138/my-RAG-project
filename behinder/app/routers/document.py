"""
路由 — 文档管理
"""
import asyncio
import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.config import settings
from app.db import crud
from app.schemas.document import DocumentOut
from app.utils.file_utils import validate_file_extension, save_upload_file
from app.services.document_service import process_document_async

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not validate_file_extension(file.filename):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持：pdf, txt, md, docx")

    # 保存文件
    file_path = await save_upload_file(file)

    # 创建数据库记录
    doc = await crud.create_document(db, name=file.filename, file_path=file_path)
    await db.commit()
    await db.refresh(doc)

    # 后台异步处理
    asyncio.create_task(
        process_document_async(
            doc_id=doc.id,
            file_path=file_path,
            collection_name="default",
            db_url=settings.database_url,
        )
    )

    return doc


@router.get("/list", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    return await crud.list_documents(db)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await crud.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 1. 删除物理文件
    file_path = doc.file_path
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[Document] 已删除物理文件: {file_path}")
        except OSError as e:
            print(f"[Document] 删除物理文件失败: {e}")

    # 2. 从 Chroma 向量库删除该文档的向量
    try:
        from agent_rag.rag.ingestion.embedder import (
            DashScopeEmbeddings,
            load_vectorstore,
        )
        embeddings = DashScopeEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )
        vs = load_vectorstore("default", settings.chroma_persist_dir, embeddings)
        # 按元数据 source_file 删除
        vs.delete(where={"source_file": doc.name})
        print(f"[Document] 已从 Chroma 删除文档向量: {doc.name}")
    except Exception as e:
        print(f"[Document] Chroma 删除失败（非致命）: {e}")

    # 3. 从 BM25 索引中移除该文档对应的 chunk
    try:
        from agent_rag.rag.ingestion.embedder import load_bm25_index, save_bm25_index
        import pickle
        from pathlib import Path as PathLib
        bm25, bm25_docs = load_bm25_index("default", settings.bm25_index_dir)
        if bm25_docs:
            # 过滤掉属于该文档的 chunk
            remaining = [d for d in bm25_docs if d.metadata.get("source_file") != doc.name]
            removed = len(bm25_docs) - len(remaining)
            if removed > 0 and remaining:
                # 重建 BM25 索引
                from rank_bm25 import BM25Okapi
                try:
                    import jieba
                    tokenized = [list(jieba.cut(d.page_content)) for d in remaining]
                except ImportError:
                    tokenized = [d.page_content.split() for d in remaining]
                new_bm25 = BM25Okapi(tokenized)
                save_bm25_index("default", settings.bm25_index_dir, new_bm25, remaining)
                print(f"[Document] 已重建 BM25 索引（移除 {removed} 个 chunk）")
            elif not remaining:
                # 全部删光了，删除索引文件
                for suffix in ["_bm25.pkl", "_docs.pkl"]:
                    p = PathLib(settings.bm25_index_dir) / f"default{suffix}"
                    if p.exists():
                        p.unlink()
                print(f"[Document] BM25 索引已清空（所有文档已删除）")
    except Exception as e:
        print(f"[Document] BM25 清理失败（非致命）: {e}")

    # 4. 删除数据库记录
    await crud.delete_document(db, doc_id)

    return {"message": "deleted"}
