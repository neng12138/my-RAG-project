"""
BM25 关键词检索
"""
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


def bm25_retrieve(
    query: str,
    bm25: BM25Okapi,
    docs: list[Document],
    top_k: int = 10,
) -> list[tuple[Document, float]]:
    """
    BM25 检索，返回 (Document, score) 列表，按分数降序

    Args:
        query: 查询字符串
        bm25: BM25Okapi 实例
        docs: 与 bm25 对应的文档列表
        top_k: 返回数量

    Returns:
        [(Document, bm25_score), ...]
    """
    # 使用 jieba 中文分词（与入库时保持一致）
    try:
        import jieba
        tokens = list(jieba.cut(query))
    except ImportError:
        tokens = query.split()
    tokenized_query = [t.strip() for t in tokens if t.strip()]
    scores = bm25.get_scores(tokenized_query)

    # 获取 top_k 索引
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    results = [(docs[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    return results
