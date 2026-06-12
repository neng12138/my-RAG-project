"""
Embedding 模型封装 — 使用阿里云百炼 dashscope SDK
支持 text-embedding-v2 / text-embedding-v3 等模型
"""
import os
import dashscope


class DashScopeEmbeddings:
    """
    阿里云百炼 Embedding 模型封装
    实现 langchain Embeddings 接口，可直接替换 OpenAIEmbeddings

    DashScope SDK 响应格式：
    单文本: {"output": {"embeddings": [{"embedding": [...], "text_index": 0}]}}
    批量:   返回 list，每个元素同单文本结构
    """

    def __init__(self, model: str = "text-embedding-v2", api_key: str = None):
        """
        Args:
            model: 百炼 embedding 模型名，如 text-embedding-v2
            api_key: 百炼 API Key，为 None 则读环境变量
        """
        self.model = model
        if api_key:
            dashscope.api_key = api_key
        elif os.environ.get("DASHSCOPE_API_KEY"):
            dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
        elif os.environ.get("OPENAI_API_KEY"):
            dashscope.api_key = os.environ["OPENAI_API_KEY"]

    def embed_query(self, text: str) -> list[float]:
        """对单条文本生成向量"""
        result = dashscope.TextEmbedding.call(
            model=self.model,
            input=text,
        )
        return result.output["embeddings"][0]["embedding"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """批量对文档生成向量

        DashScope 批量调用返回单个 result 对象，
        output.embeddings 是一个列表，每项包含 text_index + embedding
        """
        result = dashscope.TextEmbedding.call(
            model=self.model,
            input=texts,
        )
        # 按 text_index 排序确保顺序
        embeddings_list = sorted(
            result.output["embeddings"],
            key=lambda x: x.get("text_index", 0),
        )
        return [item["embedding"] for item in embeddings_list]


# —- 工厂函数（与原有 OpenAIEmbeddings 初始化方式对齐） -—
def get_embeddings(api_key: str, base_url: str, model: str) -> DashScopeEmbeddings:
    """
    获取 Embedding 模型实例
    base_url 参数保留用于接口兼容，实际不使用（dashscope SDK 固定走官方端点）
    """
    return DashScopeEmbeddings(model=model, api_key=api_key)


# —- 向量库 + BM25 加载工具 -—
def load_vectorstore(collection_name: str, chroma_persist_dir: str, embeddings):
    """
    加载或创建 Chroma 向量存储

    Args:
        collection_name: collection 名称
        chroma_persist_dir: Chroma 持久化目录
        embeddings: Embedding 模型实例

    Returns:
        Chroma vectorstore 实例
    """
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection_name,
        persist_directory=chroma_persist_dir,
        embedding_function=embeddings,
    )


def load_bm25_index(collection_name: str, bm25_index_dir: str):
    """
    加载或创建 BM25 索引

    Args:
        collection_name: 索引名称
        bm25_index_dir: BM25 索引目录

    Returns:
        (bm25_instance, documents_list) 或 (None, [])
    """
    import pickle
    from pathlib import Path

    index_file = Path(bm25_index_dir) / f"{collection_name}_bm25.pkl"
    docs_file = Path(bm25_index_dir) / f"{collection_name}_docs.pkl"

    if index_file.exists() and docs_file.exists():
        try:
            with open(index_file, "rb") as f:
                bm25 = pickle.load(f)
            with open(docs_file, "rb") as f:
                docs = pickle.load(f)

            # 兼容旧数据：旧代码存储的是 page_content 字符串而非 Document 对象
            # 自动检测并转换为 Document 类型
            if docs and isinstance(docs[0], str):
                from langchain_core.documents import Document
                print(f"[BM25] 检测到旧格式数据（字符串），自动转换为 Document 对象")
                docs = [Document(page_content=s) for s in docs]

            return bm25, docs
        except Exception as e:
            print(f"[BM25] 加载索引失败: {e}")

    return None, []


def embed_and_store(
    chunks: list,
    collection_name: str,
    chroma_persist_dir: str,
    bm25_index_dir: str,
    embeddings,
):
    """
    向量化 + Chroma 入库 + BM25 索引构建

    Args:
        chunks: LangChain Document 列表
        collection_name: Chroma collection 名称
        chroma_persist_dir: Chroma 持久化目录
        bm25_index_dir: BM25 索引目录
        embeddings: Embedding 模型实例
    """
    import pickle
    from pathlib import Path
    from rank_bm25 import BM25Okapi
    from langchain_chroma import Chroma

    # ── 向量入库 ──
    vectorstore = Chroma(
        collection_name=collection_name,
        persist_directory=chroma_persist_dir,
        embedding_function=embeddings,
    )
    vectorstore.add_documents(chunks)

    # ── BM25 分词 + 索引 ──
    print(f"[Embedder] 开始分词，{len(chunks)} 个文本块...")
    # 使用 jieba 中文分词（简单 split() 对中文无效）
    try:
        import jieba
        _tokenize = lambda text: list(jieba.cut(text))
    except ImportError:
        print("[Embedder] jieba 未安装，回退到空格分词（中文检索效果差）")
        _tokenize = lambda text: text.split()

    # 先加载已有 BM25 索引（如果存在），实现增量追加而非覆盖
    existing_bm25, existing_docs = load_bm25_index(collection_name, bm25_index_dir)
    if existing_bm25 is not None and existing_docs:
        print(f"[Embedder] 检测到已有 BM25 索引（{len(existing_docs)} 篇文档），将追加合并")
        all_docs = list(existing_docs)
        # 从已有 BM25 重建 tokenized 列表
        # BM25Okapi 不暴露内部 token 序列，需要从文档重新分词
        all_tokenized = []
        for doc in existing_docs:
            tokens = _tokenize(doc.page_content)
            tokens = [t.strip() for t in tokens if t.strip()]
            if tokens:
                all_tokenized.append(tokens)
            else:
                # 如果此文档无法分词，仍保留（与下面逻辑一致）
                pass
    else:
        all_tokenized = []
        all_docs = []

    # 追加新 chunk
    for chunk in chunks:
        tokens = _tokenize(chunk.page_content)
        # 过滤空 token
        tokens = [t.strip() for t in tokens if t.strip()]
        if tokens:
            all_tokenized.append(tokens)
            all_docs.append(chunk)
        else:
            # 即使无法分词也保留文档（后续可通过向量检索找到）
            # 但 BM25 索引中不包含
            pass

    # 用合并后的数据重建 BM25 索引
    bm25 = BM25Okapi(all_tokenized) if all_tokenized else None

    # 持久化
    Path(bm25_index_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(bm25_index_dir) / f"{collection_name}_bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    with open(Path(bm25_index_dir) / f"{collection_name}_docs.pkl", "wb") as f:
        # 存储完整 Document 对象（而非 page_content 字符串）
        # 否则 hybrid_retriever 中调用 doc.page_content 会抛出 AttributeError
        pickle.dump(all_docs, f)

    print(f"[Embedder] 入库完成：{len(chunks)} 块 → Chroma，BM25 总索引 {len(all_docs)} 篇")


def save_bm25_index(collection_name: str, bm25_index_dir: str, bm25, docs):
    """
    保存 BM25 索引和文档列表到磁盘

    Args:
        collection_name: 索引名称
        bm25_index_dir: BM25 索引目录
        bm25: BM25Okapi 实例
        docs: Document 对象列表
    """
    import pickle
    from pathlib import Path

    Path(bm25_index_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(bm25_index_dir) / f"{collection_name}_bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    with open(Path(bm25_index_dir) / f"{collection_name}_docs.pkl", "wb") as f:
        pickle.dump(docs, f)
