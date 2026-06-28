# -*- coding: utf-8 -*-
"""
RAG 检索工具

提供基于向量数据库的文档多策略融合检索。
"""

from langchain.tools import tool

from .vector_store import get_rag_store


@tool
def rag_search_tool(query: str) -> str:
    """从已上传的知识库文档中检索相关内容（增强融合检索）。

    实现多算法融合（BM25+语义+MMR）+ 查询扩展 + Cross-Encoder 精排，
    自动从多个角度检索同一问题并融合排序，大幅提高召回率和精度。

    适用场景：
    - 用户询问关于已上传文档（PDF/Word/Markdown/文本文件）的问题
    - 需要在文档中查找特定信息
    - 对内部文档进行问答

    Args:
        query: 自然语言查询问题

    Returns:
        检索到的相关内容片段，含相似度信息和融合得分
    """
    store = get_rag_store()

    # 检查是否有文档
    docs = store.list_documents()
    if not docs:
        return "知识库为空。请先上传文档（支持 PDF / Word / Markdown / TXT 格式）。"

    try:
        # 使用 Hybrid 融合检索：RRF 融合语义 + BM25
        results = store.fused_search(query, k=4, strategy="hybrid")
        if not results:
            return "未检索到相关内容，请尝试换个问法。"

        lines = ["知识库检索结果（Hybrid 融合: 语义 + BM25）："]
        for i, (item, score) in enumerate(results, 1):
            source = item.get("source", "未知")
            content = item.get("content", "")[:500]
            lines.append(f"\n[{i}] 来源: {source} (融合得分: {score:.4f})")
            lines.append(f"{content}")

        return "\n".join(lines)

    except Exception as e:
        return f"RAG 检索失败: {str(e)}"
