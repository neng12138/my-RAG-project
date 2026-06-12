"""
向量相似度检索
"""
from langchain_core.documents import Document
from langchain_chroma import Chroma


def vector_retrieve(
    query: str,
    vectorstore: Chroma,
    top_k: int = 10,
) -> list[tuple[Document, float]]:
    """
    向量相似度检索，返回 (Document, similarity_score) 列表

    Args:
        query: 查询字符串
        vectorstore: Chroma 向量库实例
        top_k: 返回数量

    Returns:
        [(Document, score), ...]  score 越高越相关，score 归一化到 [0, 1] 区间
    """
    results = vectorstore.similarity_search_with_relevance_scores(query, k=top_k)

    # Chroma 的 relevance_score 可能为负值或 >1（取决于 embedding 空间）
    # 用 min-max 归一化将其映射到 [0, 1] 区间，保证 RRF 融合稳定
    if results:
        scores = [s for _, s in results]
        min_s = min(scores)
        max_s = max(scores)
        if max_s > min_s:
            normalized = [
                (doc, (s - min_s) / (max_s - min_s))
                for doc, s in results
            ]
            return normalized
        elif max_s > 0:
            # 所有分数相同且为正 → 归一化到 1.0
            return [(doc, 1.0) for doc, _ in results]
        else:
            # 所有分为 0 或负数 → 保持原值
            return results

    return results
