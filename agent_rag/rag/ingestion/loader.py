"""
文档加载器 — 支持 PDF / TXT / Markdown / Word
"""
import os
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    Docx2txtLoader,
)
from langchain_core.documents import Document

try:
    from langchain_community.document_loaders import PyMuPDFLoader
    _HAS_PYMUPDF = True
except ImportError:
    from langchain_community.document_loaders import PyPDFLoader
    _HAS_PYMUPDF = False


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def _load_text_file(file_path: str) -> list[Document]:
    """加载文本文件，自动尝试多种编码"""
    path = Path(file_path)
    encodings = ["utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"]
    for enc in encodings:
        try:
            loader = TextLoader(str(path), encoding=enc)
            docs = loader.load()
            if docs and docs[0].page_content.strip():
                return docs
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 兜底：用 latin-1（不报错但可能乱码）
    loader = TextLoader(str(path), encoding="latin-1")
    return loader.load()


def load_document(file_path: str) -> list[Document]:
    """
    根据文件扩展名自动选择加载器，返回 Document 列表
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件格式: {ext}，支持: {SUPPORTED_EXTENSIONS}")

    if ext == ".pdf":
        if _HAS_PYMUPDF:
            loader = PyMuPDFLoader(str(path))
        else:
            loader = PyPDFLoader(str(path))
    elif ext == ".txt":
        docs = _load_text_file(str(path))
        # 附加元数据
        for doc in docs:
            doc.metadata["source_file"] = path.name
            doc.metadata["file_path"] = str(path)
        return docs
    elif ext == ".md":
        docs = _load_text_file(str(path))
        for doc in docs:
            doc.metadata["source_file"] = path.name
            doc.metadata["file_path"] = str(path)
        return docs
    elif ext == ".docx":
        loader = Docx2txtLoader(str(path))
    else:
        raise ValueError(f"未处理的扩展名: {ext}")

    docs = loader.load()

    # 附加文件名元数据
    for doc in docs:
        doc.metadata["source_file"] = path.name
        doc.metadata["file_path"] = str(path)

    return docs
