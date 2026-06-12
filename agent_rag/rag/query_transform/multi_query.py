"""
多查询扩展 — 从不同角度生成多个检索查询
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent_rag.prompts.hyde_prompt import MULTI_QUERY_PROMPT


def generate_multi_queries(
    query: str,
    llm: ChatOpenAI,
    num_queries: int = 3,
) -> list[str]:
    """
    生成多个检索查询，扩大召回面

    Args:
        query: 用户原始查询
        llm: LLM 实例
        num_queries: 生成数量

    Returns:
        查询列表（包含原始查询）
    """
    prompt = PromptTemplate.from_template(MULTI_QUERY_PROMPT)
    chain = prompt | llm | StrOutputParser()

    try:
        result = chain.invoke({"query": query})
        queries = [q.strip() for q in result.strip().split("\n") if q.strip()]
        # 限制数量，并确保包含原始查询
        queries = queries[:num_queries]
    except Exception as e:
        print(f"[MultiQuery] 生成失败: {e}")
        queries = []

    # 原始查询放首位
    all_queries = [query] + [q for q in queries if q != query]
    return all_queries
