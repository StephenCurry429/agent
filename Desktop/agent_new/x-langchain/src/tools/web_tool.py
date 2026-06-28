from typing import Any, Dict, List, Optional
import re

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# ── 侧通道：存储最近一次搜索的原始元数据，供 app.py 提取 ──
_last_search_meta: List[Dict[str, str]] = []

def get_last_search_meta() -> List[Dict[str, str]]:
    """返回最近一次搜索的 title/url/snippet 元数据。"""
    return _last_search_meta

# ── 正规网站白名单 ──
REPUTABLE_DOMAINS = [
    "wikipedia.org", "wikiwand.com", "britannica.com",
    "baike.baidu.com", "zhihu.com", "zh.wikisource.org",
    "gov.cn", "gov", "edu.cn", "edu",
    "github.com", "stackoverflow.com", "pypi.org", "npmjs.com",
    "python.org", "nodejs.org", "rust-lang.org", "golang.org",
    "news.qq.com", "163.com", "sina.com.cn", "people.com.cn",
    "xinhuanet.com", "cctv.com", "thepaper.cn",
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com",
    "nytimes.com", "wsj.com", "economist.com",
    "arxiv.org", "scholar.google.com", "semanticscholar.org",
    "ieee.org", "acm.org", "springer.com", "nature.com",
    "science.org", "cell.com", "plos.org",
    "docs.python.org", "developer.mozilla.org", "learn.microsoft.com",
]

BLOCKED_PATTERNS = [
    r"porn", r"xxx", r"adult", r"gambling", r"casino",
    r"crack", r"warez", r"torrent", r"pirate",
]


def _is_reputable(url: str) -> bool:
    if not url:
        return False
    url_lower = url.lower()
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, url_lower):
            return False
    for domain in REPUTABLE_DOMAINS:
        if domain in url_lower:
            return True
    return False


def _search_bing(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """直接请求 Bing 搜索，返回结果列表。"""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    resp = requests.get(
        "https://www.bing.com/search",
        params={"q": query, "count": max_results},
        headers=headers,
        timeout=3,
    )
    resp.raise_for_status()
    html = resp.text

    results: List[Dict[str, str]] = []

    # ── 提取所有 <h2> 内的标题链接（Bing 标准结构） ──
    h2_blocks = re.findall(
        r'<h2[^>]*>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>\s*</h2>',
        html, re.DOTALL,
    )
    for url, raw_title in h2_blocks:
        title = re.sub(r'<[^>]+>', '', raw_title).strip()
        # 跳过无意义链接（锚点、js、短标题）
        if not title or len(title) < 3:
            continue
        if url.startswith("javascript:") or "#" == url:
            continue
        if title in {"上一页", "下一页", "Next", "Previous", "更多", "More"}:
            continue
        results.append({"title": title, "href": url, "body": ""})

    # ── 补充摘要（从附近上下文中提取） ──
    snippet_patterns = [
        r'<(?:p|div)[^>]*class="[^"]*(?:b_caption|b_snippet|b_lineclamp|b_algoSlug)[^"]*"[^>]*>(.*?)</(?:p|div)>',
        r'<p[^>]*>(.*?)</p>',
    ]
    for i, r in enumerate(results):
        if r["body"]:
            continue
        # 在原始 HTML 中按标题定位，向后找摘要
        pos = html.find(r["href"])
        if pos < 0:
            continue
        nearby = html[pos:pos + 2000]
        for pat in snippet_patterns:
            m = re.search(pat, nearby, re.DOTALL)
            if m:
                snippet = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                snippet = re.sub(r'\s+', ' ', snippet)
                if len(snippet) > 20:
                    results[i]["body"] = snippet[:300]
                    break

    # ── 兜底：如果 h2 没找到足够结果，用 b_algo 解析 ──
    if len(results) < 2:
        for block in re.finditer(
            r'<li\s[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL
        ):
            blk = block.group(1)
            parsed = _parse_result_block(blk)
            if parsed and parsed not in results:
                results.append(parsed)
            if len(results) >= max_results:
                break

    return results[:max_results]


def _parse_result_block(blk: str) -> Optional[Dict[str, str]]:
    """从 HTML 块中提取标题、链接、摘要（兜底方案）。"""
    # 优先找 h2 内的标题链接
    h2_match = re.search(
        r'<h2[^>]*>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>\s*</h2>',
        blk, re.DOTALL,
    )
    if h2_match:
        url = h2_match.group(1)
        title = re.sub(r'<[^>]+>', '', h2_match.group(2)).strip()
        if title and len(title) >= 3:
            snippet = _extract_snippet(blk)
            return {"title": title, "href": url, "body": snippet}

    # 兜底：取文本最长的 <a> 标签（跳过 cite/breadcrumb）
    links = re.findall(
        r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', blk, re.DOTALL
    )
    if not links:
        return None
    best = max(links, key=lambda x: len(re.sub(r'<[^>]+>', '', x[1]).strip()))
    url = best[0]
    title = re.sub(r'<[^>]+>', '', best[1]).strip()
    if not title or len(title) < 3:
        return None
    snippet = _extract_snippet(blk)
    return {"title": title, "href": url, "body": snippet}


def _extract_snippet(html_block: str) -> str:
    """从 HTML 块中提取文本摘要。"""
    for pat in [
        r'<(?:p|div)[^>]*class="[^"]*(?:b_caption|b_snippet|b_lineclamp|b_algoSlug)[^"]*"[^>]*>(.*?)</(?:p|div)>',
        r'<p[^>]*>(.*?)</p>',
    ]:
        m = re.search(pat, html_block, re.DOTALL)
        if m:
            snippet = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            snippet = re.sub(r'\s+', ' ', snippet)
            if len(snippet) > 20:
                return snippet[:300]
    return ""


def _tokenize(text: str) -> List[str]:
    """简单中文分词。"""
    try:
        import jieba
        return list(jieba.cut(text))
    except ImportError:
        return re.findall(r'[\u4e00-\u9fff]{2,}|\w+', text.lower())


def _keyword_score(query: str, result: Dict[str, str]) -> float:
    """计算搜索结果与查询的关键词匹配得分 (0~1)。"""
    q_tokens = set(_tokenize(query.lower()))
    if not q_tokens:
        return 0.5
    text = f"{result.get('title', '')} {result.get('body', '')}".lower()
    t_tokens = set(_tokenize(text))
    overlap = q_tokens & t_tokens
    return len(overlap) / len(q_tokens) if q_tokens else 0.5


def _rerank_results(query: str, results: List[Dict[str, str]],
                    top_k: int = 6) -> List[Dict[str, str]]:
    """基于关键词 + 域名权重对搜索结果重排序。"""
    scored = []
    for r in results:
        href = r.get("href", "")
        ks = _keyword_score(query, r)
        # 正规网站加分
        domain_bonus = 0.15 if _is_reputable(href) else 0.0
        score = ks + domain_bonus
        scored.append((r, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in scored[:top_k]]


def _rag_retrieve(query: str, k: int = 3) -> Optional[List[Dict[str, str]]]:
    """
    从本地 RAG 知识库检索相关内容（1.5s 超时保护）。
    返回 [{"title": source, "href": "", "body": content}, ...] 或 None。
    """
    import threading
    result_container: list = []

    def _do_retrieve():
        try:
            from rag.vector_store import get_rag_store
            store = get_rag_store()
            docs = store.list_documents()
            if not docs or not store._embeddings_available:
                return
            results = store.fused_search(
                query, k=k, strategy="bm25",
                expand_query=False,       # 跳过查询扩展（省时）
                cross_encode_rerank=False, # 跳过 Cross-Encoder（省时+省资源）
            )
            if not results:
                return
            for item, score in results:
                source = item.get("source", "本地文档")
                content = item.get("content", "")[:400]
                result_container.append({
                    "title": f"[RAG] {source}",
                    "href": "",
                    "body": content,
                })
        except Exception:
            pass

    t = threading.Thread(target=_do_retrieve, daemon=True)
    t.start()
    t.join(timeout=1.5)
    return result_container if result_container else None



class WebSearchArgs(BaseModel):
    query: str = Field(..., description="搜索查询词")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "从正规网站检索互联网信息，融合本地知识库（RAG）和历史记忆"
        "（仅限百科、政府、权威媒体、学术、开发文档等可信来源）"
    )
    args_schema: type[WebSearchArgs] = WebSearchArgs

    def _run(self, query: str) -> str:
        """RAG 增强搜索：Bing + 本地知识库 → 融合重排序。"""
        global _last_search_meta
        _last_search_meta = []

        try:
            # ── Step 1: Bing 搜索 ──
            web_results = _search_bing(query, max_results=5)

            # ── Step 2: 本地 RAG 检索（带超时，可选） ──
            rag_results = _rag_retrieve(query, k=3)

            # ── Step 3: 融合 ──
            all_results = list(web_results)
            if rag_results:
                all_results = rag_results + all_results

            if not all_results:
                _last_search_meta = []
                return "查询结果：0条匹配。请告知用户未查询到相关公开信息。"

            # 重排序
            ranked = _rerank_results(query, all_results, top_k=5)

            # 正规网站优先
            reputable = [r for r in ranked if _is_reputable(r.get("href", ""))
                         or r.get("title", "").startswith("[RAG]")]
            other = [r for r in ranked if r not in reputable]
            final_results = (reputable + other)[:5]

            # ── 存入侧通道（供前端搜索资源渲染）──
            for r in final_results:
                _last_search_meta.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

            # ── Agent 内部使用（纯事实内容，不含URL和格式前缀）──
            facts: List[str] = []
            for r in final_results:
                title = r.get("title", "")
                body = r.get("body", "")
                if body:
                    facts.append(f"[{title}] {body[:250]}")
                else:
                    facts.append(f"[{title}] 获取摘要失败")

            return "\n\n".join(facts)

        except Exception as e:
            _last_search_meta = []
            return f"搜索时发生错误: {str(e)}"


if __name__ == "__main__":
    tool = WebSearchTool()
    print(tool._run("Python programming"))
