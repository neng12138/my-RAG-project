"""
HyDE — Hypothetical Document Embeddings
生成假设答案文档，用其 Embedding 做语义检索
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent_rag.prompts.hyde_prompt import HYDE_PROMPT


def generate_hyde_document(
    query: str,
    llm: ChatOpenAI,
) -> str:
    """
    基于用户查询生成假设性答案文档

    Args:
        query: 用户原始查询
        llm: LLM 实例

    Returns:
        假设文档文本
    """
    prompt = PromptTemplate.from_template(HYDE_PROMPT)
    chain = prompt | llm | StrOutputParser()
    try:
        result = chain.invoke({"query": query})
        return result.strip()
    except Exception as e:
        print(f"[HyDE] 生成失败，回退到原始查询: {e}")
        return query
