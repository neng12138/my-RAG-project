"""
混合检索 — BM25 + 向量检索，使用 RRF 融合
"""
from langchain_core.documents import Document
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

from .bm25_retriever import bm25_retrieve
from .vector_retriever import vector_retrieve


def reciprocal_rank_fusion(
    bm25_results: list[tuple[Document, float]],
    vector_results: list[tuple[Document, float]],
    k: int = 60,
    top_k: int = 20,
) -> list[tuple[Document, float]]:
    """
    RRF (Reciprocal Rank Fusion) 融合两路检索结果

    公式: score(d) = Σ 1 / (k + rank_i(d))

    Args:
        bm25_results: BM25 检索结果 [(doc, score), ...]
        vector_results: 向量检索结果 [(doc, score), ...]
        k: 平滑因子（默认 60）
        top_k: 返回数量

    Returns:
        融合后的 [(Document, rrf_score), ...] 降序
    """
    rrf_scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    def get_doc_id(doc: Document) -> str:
        # 用 page_content 的哈希作为唯一标识
        return str(hash(doc.page_content))

    # BM25 排名贡献
    for rank, (doc, _) in enumerate(bm25_results):
        doc_id = get_doc_id(doc)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    # 向量检索排名贡献
    for rank, (doc, _) in enumerate(vector_results):
        doc_id = get_doc_id(doc)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    # 排序并返回 top_k
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(doc_map[doc_id], score) for doc_id, score in sorted_items]


def hybrid_retrieve(
    query: str,
    vectorstore: Chroma,
    bm25: BM25Okapi,
    bm25_docs: list[Document],
    bm25_top_k: int = 10,
    vector_top_k: int = 10,
    fusion_top_k: int = 20,
) -> list[tuple[Document, float]]:
    """
    混合检索主函数

    Args:
        query: 查询字符串
        vectorstore: Chroma 向量库
        bm25: BM25Okapi 实例
        bm25_docs: BM25 对应文档列表
        bm25_top_k: BM25 召回数
        vector_top_k: 向量召回数
        fusion_top_k: 融合后返回数

    Returns:
        [(Document, rrf_score), ...]
    """
    bm25_results = bm25_retrieve(query, bm25, bm25_docs, top_k=bm25_top_k)
    vector_results = vector_retrieve(query, vectorstore, top_k=vector_top_k)

    fused = reciprocal_rank_fusion(
        bm25_results, vector_results, top_k=fusion_top_k
    )
    return fused
