"""
重排序 — 支持两种模式：
1. 阿里云百炼 API（qwen3-rerank 等）- 通过 HTTP 直接调用
2. 本地 CrossEncoder（BAAI/bge-reranker 等 - 备用）

阿里云百炼 Rerank API 文档：
https://help.aliyun.com/zh/model-studio/developer-reference/text-rerank-api
"""
import os
import httpx
from langchain_core.documents import Document

# ── 全局缓存（本地 CrossEncoder 模式） ──
_reranker_model = None
_reranker_model_name = None


def _is_dashscope_rerank(model_name: str) -> bool:
    """判断模型是否为阿里云百炼 API 重排模型"""
    name = model_name.lower()
    return "qwen" in name and "rerank" in name


async def _rerank_dashscope(
    query: str,
    documents: list[str],
    model_name: str,
    api_key: str,
    top_k: int,
) -> list[float]:
    """
    调用阿里云百炼 Rerank API（qwen3-rerank）

    正确格式（qwen3-rerank 模型）：
    POST https://dashscope.aliyuncs.com/compatible-api/v1/reranks

    Body:
    {
        "model": "qwen3-rerank",
        "query": "查询文本",
        "documents": ["文档1", "文档2", ...],
        "top_n": 3
    }

    返回格式：
    {
        "object": "list",
        "results": [
            {"index": 1, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.87},
            ...
        ],
        "model": "qwen3-rerank",
        "usage": {"total_tokens": 78}
    }
    """
    url = "https://dashscope.aliyuncs.com/compatible-api/v1/reranks"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "query": query,
        "documents": documents,
        "top_n": min(top_k, len(documents)),
    }

    # 使用 httpx.AsyncClient 避免阻塞事件循环
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # 将返回的 results 映射回原始索引的分数列表
    # 响应格式: {"results": [{"index": N, "relevance_score": float}, ...]}
    results = data["results"]
    scores = [0.0] * len(documents)
    for r in results:
        idx = r["index"]
        scores[idx] = r["relevance_score"]

    return scores


def get_reranker(model_name: str):
    """懒加载本地 CrossEncoder 模型（全局单例，备用）"""
    global _reranker_model, _reranker_model_name
    if _reranker_model is None or _reranker_model_name != model_name:
        try:
            from sentence_transformers import CrossEncoder
            _reranker_model = CrossEncoder(model_name)
            _reranker_model_name = model_name
            print(f"[Reranker] 本地模型加载成功: {model_name}")
        except Exception as e:
            print(f"[Reranker] 加载本地模型失败: {e}")
            _reranker_model = None
    return _reranker_model


async def rerank(
    query: str,
    candidates: list[tuple[Document, float]],
    model_name: str,
    top_k: int = 5,
    api_key: str = None,
) -> list[tuple[Document, float]]:
    """
    使用重排序模型对候选文档重新精排

    Args:
        query: 用户查询
        candidates: 混合检索结果 [(Document, score), ...]
        model_name: 重排序模型名
                      支持 "qwen3-rerank"（阿里云 API）或 HuggingFace 模型名（本地）
        top_k: 精排后返回数量
        api_key: 阿里云百炼 API Key（API 模式必填，不传则读环境变量 OPENAI_API_KEY）

    Returns:
        精排后的 [(Document, rerank_score), ...]
    """
    if not candidates:
        return []

    # ── 模式 1：阿里云百炼 API 重排 ──
    if _is_dashscope_rerank(model_name):
        if api_key is None:
            # 优先读 DASHSCOPE_API_KEY，兼容 OPENAI_API_KEY
            api_key = os.environ.get("DASHSCOPE_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("[Reranker] 未找到 API Key，降级为原始顺序")
            return candidates[:top_k]

        docs = [doc for doc, _ in candidates]
        doc_texts = [doc.page_content for doc in docs]

        try:
            scores = await _rerank_dashscope(query, doc_texts, model_name, api_key, top_k)
            # 按分数降序排列
            indexed = sorted(
                enumerate(scores),
                key=lambda x: x[1],
                reverse=True,
            )
            return [(docs[i], s) for i, s in indexed[:top_k]]
        except Exception as e:
            print(f"[Reranker] API 调用失败: {e}，降级为原始顺序")
            return candidates[:top_k]

    # ── 模式 2：本地 CrossEncoder 重排（备用） ──
    reranker = get_reranker(model_name)

    if reranker is None:
        print("[Reranker] 本地模型未加载，使用原始顺序")
        return candidates[:top_k]

    docs = [doc for doc, _ in candidates]
    pairs = [(query, doc.page_content) for doc in docs]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(docs, scores.tolist()),
        key=lambda x: x[1],
        reverse=True,
    )

    return ranked[:top_k]
