"""
文本分块 — 递归字符分块
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))


def split_documents(
    documents: list[Document],
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Document]:
    """
    使用 RecursiveCharacterTextSplitter 对文档进行递归分块

    Args:
        documents: 原始文档列表
        chunk_size: 每块的最大字符数
        chunk_overlap: 块间重叠字符数

    Returns:
        分块后的 Document 列表
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)

    # 为每个 chunk 添加索引信息
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["chunk_total"] = len(chunks)

    return chunks
