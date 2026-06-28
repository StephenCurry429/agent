# -*- coding: utf-8 -*-
"""
RAG 向量存储模块

管理 ChromaDB 向量数据库，支持文档索引和多种检索算法融合。
"""

import os
import math
from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)

from core import logger
from core.config import settings

# 数据目录
RAG_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "rag"
)
CHROMA_DIR = os.path.join(RAG_DATA_DIR, "chroma")
DOCS_DIR = os.path.join(RAG_DATA_DIR, "docs")

_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100

# embedding 失败缓存：只尝试一次，避免重复重试噪声
_embeddings_failed = False
_embeddings_instance = None


def _get_embeddings():
    """获取 embedding 模型，依次尝试多个来源直到成功。失败后缓存，不再重试。"""
    global _embeddings_failed, _embeddings_instance

    if _embeddings_instance is not None:
        return _embeddings_instance
    if _embeddings_failed:
        raise RuntimeError("Embedding 已确认不可用（缓存）")

    # 尝试的 embedding 模型候选项
    candidates = [
        ("text-embedding-3-small", settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL),
        ("text-embedding-ada-002", settings.OPENAI_API_KEY, settings.OPENAI_BASE_URL),
        ("text-embedding-3-small", settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_API_BASE),
    ]

    for model, key, base in candidates:
        if key and base:
            try:
                emb = OpenAIEmbeddings(model=model, api_key=key, base_url=base)
                # 快速验证能否正常调用
                emb.embed_query("test")
                logger.info(f"RAG Embedding: {model} @ {base}")
                _embeddings_instance = emb
                return emb
            except Exception as e:
                logger.warning(f"RAG Embedding 尝试 {model} @ {base} 失败: {e}")
                continue

    # ── HuggingFace 本地模型（无需外部 API） ──
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        local_models = [
            "BAAI/bge-small-zh-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2",
        ]
        for model_name in local_models:
            try:
                logger.info(f"尝试本地 Embedding: {model_name}")
                emb = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={"device": "cpu"},
                    encode_kwargs={"normalize_embeddings": True},
                )
                emb.embed_query("test")
                logger.info(f"RAG Embedding: {model_name} (本地)")
                _embeddings_instance = emb
                return emb
            except Exception as e:
                logger.warning(f"本地 Embedding {model_name} 失败: {e}")
                continue
    except ImportError:
        logger.warning("langchain_huggingface 未安装，跳过本地 embedding")

    _embeddings_failed = True
    raise RuntimeError(
        "无法初始化 Embedding 模型：所有候选项均失败。"
        "请确保 OPENAI_API_KEY / DEEPSEEK_API_KEY 已配置，且 API 支持 embedding，"
        "或安装 langchain_huggingface 使用本地模型。"
    )


_reranker_cache = None


def _get_reranker(model_name: str = "BAAI/bge-reranker-base"):
    """延迟加载 Cross-Encoder 重排模型（单例）。"""
    global _reranker_cache
    if _reranker_cache is None:
        from sentence_transformers import CrossEncoder
        logger.info(f"RAG: 加载 Cross-Encoder 模型 {model_name} ...")
        _reranker_cache = CrossEncoder(model_name)
        logger.info(f"RAG: Cross-Encoder 模型加载完成")
    return _reranker_cache


class RAGStore:
    """
    RAG 向量存储管理器。

    支持：
    - TXT / PDF / DOCX / MD 文件索引
    - 语义检索
    - 文档列表管理
    """

    def __init__(self):
        os.makedirs(DOCS_DIR, exist_ok=True)
        os.makedirs(CHROMA_DIR, exist_ok=True)

        self._embeddings = None
        self._embeddings_available = True
        self._vectorstore: Optional[Chroma] = None
        # BM25 纯文本后备：当 embedding 不可用时，内存中保存原始 chunk
        self._raw_chunks: List = []

    @property
    def embeddings(self):
        if self._embeddings is None:
            try:
                self._embeddings = _get_embeddings()
            except RuntimeError as e:
                logger.warning(f"RAG: Embedding 不可用，仅启用 BM25 检索: {e}")
                self._embeddings_available = False
                self._embeddings = None
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None and self._embeddings_available and self.embeddings is not None:
            self._vectorstore = Chroma(
                persist_directory=CHROMA_DIR,
                embedding_function=self.embeddings,
            )
        return self._vectorstore

    def _load_file(self, file_path: str) -> list:
        """根据文件扩展名加载文档。"""
        ext = os.path.splitext(file_path)[1].lower()
        loaders = {
            ".txt": TextLoader,
            ".md": UnstructuredMarkdownLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
        }
        loader_cls = loaders.get(ext)
        if not loader_cls:
            raise ValueError(f"不支持的文件格式: {ext}")
        loader = loader_cls(file_path, encoding="utf-8")
        return loader.load()

    def add_document(self, file_path: str) -> int:
        """
        添加文档到向量存储。

        Returns:
            添加的分块数量
        """
        docs = self._load_file(file_path)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=_CHUNK_SIZE,
            chunk_overlap=_CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(docs)

        # 添加文件来源元数据
        filename = os.path.basename(file_path)
        for chunk in chunks:
            chunk.metadata["source"] = filename

        if self._embeddings_available:
            try:
                self.vectorstore.add_documents(chunks)
                logger.info(f"RAG: 已索引文档 {filename}，共 {len(chunks)} 个分块")
            except Exception as e:
                logger.warning(f"RAG: 向量索引失败，存入纯文本后备: {e}")
                self._raw_chunks.extend(chunks)
        else:
            # Embedding 不可用，存入内存纯文本后备
            self._raw_chunks.extend(chunks)
            logger.info(f"RAG (BM25): 已缓存文档 {filename}，共 {len(chunks)} 个分块")
        return len(chunks)

    def search(self, query: str, k: int = 4) -> List[str]:
        """
        语义搜索文档。

        Returns:
            相关文本片段列表
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def search_with_scores(self, query: str, k: int = 4) -> list:
        """带相似度分数的语义搜索。"""
        return self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

    # ═══════════════════════════════════════════════════════════════
    # 检索算法融合引擎
    # ═══════════════════════════════════════════════════════════════

    def _get_all_chunks(self) -> List:
        """获取所有文档分块（向量库 + 内存后备）。"""
        docs = list(self._raw_chunks)  # 先纳入内存后备

        try:
            collection = self._vectorstore._collection if self._vectorstore else None
            if collection:
                result = collection.get(include=["documents", "metadatas"])
                from langchain_core.documents import Document
                for i, text in enumerate(result.get("documents", [])):
                    meta = result.get("metadatas", [{}])[i] if i < len(result.get("metadatas", [])) else {}
                    docs.append(Document(page_content=text, metadata=meta))
        except Exception as e:
            logger.warning(f"RAG: 获取向量分块失败: {e}")

        return docs

    def _build_bm25_index(self, docs: List) -> dict:
        """
        构建轻量级 BM25 索引。

        BM25 是一种基于词频和逆文档频率的经典关键词检索算法，
        擅长精确词匹配，能捕捉到语义向量容易遗漏的关键词命中。

        返回索引字典供 _bm25_score 使用。
        """
        doc_count = len(docs)
        # 对每个分词统计 DF（包含该词的文档数）和 TF
        df = {}          # {term: 包含该词的文档数}
        term_freqs = []  # [ {term: freq_in_doc} ]

        for doc in docs:
            tokens = self._tokenize(doc.page_content)
            tf = {}
            seen = set()
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            for t in tf:
                if t not in seen:
                    df[t] = df.get(t, 0) + 1
                    seen.add(t)
            term_freqs.append(tf)

        # 预计算 IDF（不带平滑的经典形式）
        k1 = 1.5  # BM25 词频饱和度
        b = 0.75  # 文档长度归一化

        avg_dl = sum(len(self._tokenize(d.page_content)) for d in docs) / max(doc_count, 1)

        return {
            "df": df,
            "term_freqs": term_freqs,
            "avg_dl": avg_dl,
            "doc_count": doc_count,
            "k1": k1,
            "b": b,
        }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文 jieba 精确分词 + 英文小写。"""
        import re
        import jieba

        result = []
        # 用 jieba 精确模式分中文
        words = jieba.lcut(text)
        for w in words:
            w = w.strip()
            if not w:
                continue
            # 纯英文/数字 => 小写
            if re.match(r'^[a-zA-Z0-9]+$', w):
                result.append(w.lower())
            # 中文词条直接加入
            elif re.search(r'[\u4e00-\u9fff]', w):
                result.append(w)
            else:
                result.append(w.lower() if w.isascii() else w)
        return result

    def _bm25_score(self, query: str, idx: dict) -> List[float]:
        """对每个文档计算 BM25 得分。"""
        if not idx or idx["doc_count"] == 0:
            return []

        doc_count = idx["doc_count"]
        df = idx["df"]
        term_freqs = idx["term_freqs"]
        avg_dl = idx["avg_dl"]
        k1 = idx["k1"]
        b = idx["b"]

        qtokens = self._tokenize(query)
        scores = [0.0] * doc_count

        for t in qtokens:
            n = df.get(t, 0)
            if n == 0:
                continue
            idf = math.log((doc_count - n + 0.5) / (n + 0.5) + 1.0)
            for i, tf_map in enumerate(term_freqs):
                f = tf_map.get(t, 0)
                if f == 0:
                    continue
                dl = sum(tf_map.values())
                numerator = f * (k1 + 1)
                denominator = f + k1 * (1 - b + b * dl / avg_dl)
                scores[i] += idf * numerator / denominator

        return scores

    def bm25_search(self, query: str, k: int = 4) -> List[Tuple[dict, float]]:
        """
        BM25 关键词检索。

        基于词频-逆文档频率进行精确关键词匹配，
        能发现语义检索中易遗漏的专有名词 / 术语。
        """
        docs = self._get_all_chunks()
        if not docs:
            return []

        idx = self._build_bm25_index(docs)
        scores = self._bm25_score(query, idx)
        if not scores:
            return []

        # 归一化到 [0, 1]
        max_s = max(scores) if scores else 1
        min_s = min(scores) if scores else 0
        if max_s > min_s:
            scores = [(s - min_s) / (max_s - min_s) for s in scores]
        else:
            scores = [1.0 if s > 0 else 0.0 for s in scores]

        ranked = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )
        return [({"content": d.page_content, "source": d.metadata.get("source", "")}, s)
                for d, s in ranked[:k]]

    def semantic_search_with_meta(self, query: str, k: int = 8) -> List[Tuple[dict, float]]:
        """带元数据的语义搜索，返回统一格式。"""
        if not self._embeddings_available or self.vectorstore is None:
            raise RuntimeError("Embedding 不可用，语义检索无法执行")
        results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)
        return [({"content": d.page_content, "source": d.metadata.get("source", ""),
                  "score": r}) for d, r in results]

    def mmr_search(self, query: str, k: int = 4, lambda_param: float = 0.6) -> List[Tuple[dict, float]]:
        """
        MMR（最大边际相关性）检索。

        在保持相关性的同时，惩罚与已选结果相似的新增结果，
        从而增加检索结果的多样性，避免冗余。

        Args:
            k: 返回结果数
            lambda_param: 0~1；越接近 1 越侧重相关性，越接近 0 越侧重多样性
        """
        # 先拉取候选池（多一些）
        candidates = self.semantic_search_with_meta(query, k=k * 3)
        if len(candidates) <= k:
            return candidates

        selected = [candidates[0]]
        remaining = candidates[1:]

        # 预计算候选间相似度（用文本长度归一化的简单Jaccard模拟，
        # 真实环境应使用 embedding 余弦距离）
        def jaccard_sim(a: str, b: str) -> float:
            set_a = set(self._tokenize(a))
            set_b = set(self._tokenize(b))
            if not set_a or not set_b:
                return 0.0
            return len(set_a & set_b) / len(set_a | set_b)

        while len(selected) < k and remaining:
            mmr_scores = []
            for i, cand in enumerate(remaining):
                relevance = cand[1]
                max_redun = max(
                    jaccard_sim(cand[0]["content"], sel[0]["content"])
                    for sel in selected
                )
                mmr = lambda_param * relevance - (1 - lambda_param) * max_redun
                mmr_scores.append((i, mmr))

            best_idx, _ = max(mmr_scores, key=lambda x: x[1])
            selected.append(remaining.pop(best_idx))

        return selected

    def rrf_fusion(
        self,
        semantic_results: List[Tuple[dict, float]],
        bm25_results: List[Tuple[dict, float]],
        k: int = 4,
        rrf_k: int = 60,
        semantic_weight: float = 0.6,
    ) -> List[Tuple[dict, float]]:
        """
        RRF（倒数秩融合）算法。

        将语义检索和 BM25 关键词检索的结果按排名融合，
        兼顾语义理解和精确匹配。不同算法的排名贡献通过倒数合并，
        无需关心各自评分的量纲差异。

        Args:
            semantic_results: 语义检索结果
            bm25_results: BM25 检索结果
            k: 返回结果数
            rrf_k: RRF 平滑常数（默认 60，业界常用值）
            semantic_weight: 语义检索权重 (0~1)，BM25 权重 = 1 - 该值
        """
        # 用内容哈希去重 + 累积 RRF 分数
        rrf_map = {}
        content_map = {}

        def add_rank(results, weight, prefix):
            for rank, (item, score) in enumerate(results, 1):
                key = item["content"][:200]  # 用前200字符作为去重键
                if key not in rrf_map:
                    rrf_map[key] = 0.0
                    content_map[key] = item
                rrf_map[key] += weight / (rrf_k + rank)

        add_rank(semantic_results, semantic_weight, "sem")
        add_rank(bm25_results, 1 - semantic_weight, "bm25")

        merged = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)
        return [
            (content_map[key], score) for key, score in merged[:k]
        ]

    def _rrf_multi_fusion(
        self,
        result_sets: List[List[Tuple[dict, float]]],
        weights: list,
        k: int = 4,
        rrf_k: int = 60,
    ) -> List[Tuple[dict, float]]:
        """N 路 RRF 融合（支持任意数量检索器）。

        Args:
            result_sets: 多组检索结果列表
            weights: 每组结果的权重（长度须与 result_sets 一致）
        """
        rrf_map = {}
        content_map = {}

        for idx, results in enumerate(result_sets):
            for rank, (item, _score) in enumerate(results, 1):
                key = item["content"][:200]
                if key not in rrf_map:
                    rrf_map[key] = 0.0
                    content_map[key] = item
                rrf_map[key] += weights[idx] / (rrf_k + rank)

        merged = sorted(rrf_map.items(), key=lambda x: x[1], reverse=True)
        return [
            (content_map[key], score) for key, score in merged[:k]
        ]

    def fused_search(
        self,
        query: str,
        k: int = 4,
        strategy: str = "hybrid",
        semantic_weight: float = 0.6,
        expand_query: bool = True,
        cross_encode_rerank: bool = True,
    ) -> List[Tuple[dict, float]]:
        """
        融合检索：根据策略组合多种算法。

        策略选项:
          - "semantic"   : 纯语义向量检索
          - "bm25"       : 纯 BM25 关键词检索
          - "mmr"        : MMR 多样性检索（基于语义 + 去重）
          - "hybrid"     : [推荐] RRF 融合语义 + BM25
          - "all"        : 三路融合（语义 + MMR + BM25）

        增强选项:
          - expand_query: 是否启用多面查询扩展（提高召回）
          - cross_encode_rerank: 是否用 Cross-Encoder 精排（提高精度）
        """
        strategy = strategy.lower()

        # --- 查询扩展：生成多个变体提高召回 ---
        queries = self._expand_query(query) if expand_query else [query]

        # --- 对每个查询变体检索并融合 ---
        all_results = []
        for q in queries:
            all_results.append(self._run_strategy(q, k, strategy, semantic_weight))

        if len(all_results) == 1:
            final = all_results[0]
        else:
            # 多查询结果 RRF 融合
            final = self._rrf_multi_fusion(
                all_results,
                weights=[1.0] * len(all_results),
                k=k * 2,
            )

        # --- Cross-Encoder 精排 ---
        if final and cross_encode_rerank:
            final = self._cross_encoder_rerank(query, final, k=k)

        return final[:k]

    def _run_strategy(
        self,
        query: str,
        k: int,
        strategy: str,
        semantic_weight: float,
    ) -> List[Tuple[dict, float]]:
        """执行单个检索策略（不包含扩展和重排）。"""
        if strategy == "semantic":
            try:
                return self.semantic_search_with_meta(query, k)
            except Exception as e:
                logger.warning(f"语义检索失败，回退到 BM25: {e}")
                return self.bm25_search(query, k)

        if strategy == "bm25":
            return self.bm25_search(query, k)

        if strategy == "mmr":
            try:
                return self.mmr_search(query, k)
            except Exception as e:
                logger.warning(f"MMR 检索失败，回退到 BM25: {e}")
                return self.bm25_search(query, k)

        if strategy == "hybrid":
            bm = self.bm25_search(query, k * 2)
            try:
                sem = self.semantic_search_with_meta(query, k * 2)
            except Exception as e:
                logger.warning(f"语义检索失败，hybrid 退回 BM25: {e}")
                return bm[:k]
            return self.rrf_fusion(sem, bm, k=k, semantic_weight=semantic_weight)

        if strategy == "all":
            bm = self.bm25_search(query, k * 2)
            sem = []
            mmr = []
            try:
                sem = self.semantic_search_with_meta(query, k * 2)
                mmr = self.mmr_search(query, k * 2, lambda_param=0.7)
            except Exception as e:
                logger.warning(f"语义/MMR 失败，all 退回 BM25: {e}")
                return bm[:k]
            return self._rrf_multi_fusion(
                [sem, mmr, bm],
                weights=[0.4, 0.2, 0.4],
                k=k,
            )

        logger.warning(f"RAG: 未知检索策略 {strategy}，回退到 all")
        return self._run_strategy(query, k, "all", semantic_weight)

    @staticmethod
    def _expand_query(query: str) -> List[str]:
        """查询扩展：生成多个视角的查询变体以提高召回率。

        策略：
        - 原始查询
        - 去掉疑问词/语气词的核心查询
        - 关键词拆解查询（按标点拆分）
        """
        import re
        variants = [query]

        # 去掉常见疑问词和语气词
        stripped = re.sub(
            r'[，,。！!？?\s]+|请问|请|帮我|一下|有没有|是什么|怎么|如何|吗|呢|吧|啊|呀|哦|的|了',
            ' ', query,
        ).strip()
        if stripped and stripped != query and len(stripped) >= 2:
            variants.append(stripped)

        # 按标点拆成多个子问题
        parts = re.split(r'[，,。！!？?\s；;]+', query)
        parts = [p.strip() for p in parts if len(p.strip()) >= 3]
        for p in parts:
            if p not in variants:
                variants.append(p)

        # 去重，最多 3 个变体
        seen = set()
        unique = []
        for v in variants:
            if v not in seen:
                seen.add(v)
                unique.append(v)
        return unique[:3]

    def _cross_encoder_rerank(
        self,
        query: str,
        candidates: List[Tuple[dict, float]],
        k: int = 4,
    ) -> List[Tuple[dict, float]]:
        """用 Cross-Encoder 模型对候选结果精排。

        基于 BAAI/bge-reranker-base 或类似模型，
        将 query 与每个候选文档构成 query-doc 对打分。
        """
        if len(candidates) <= k:
            return candidates

        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            logger.warning("RAG: sentence-transformers 未安装，跳过 Cross-Encoder 重排")
            return candidates

        try:
            # 使用中文友好的 reranker（首次下载约 1.1GB）
            model_name = os.getenv("RAG_RERANKER_MODEL", "BAAI/bge-reranker-base")
            reranker = _get_reranker(model_name)

            pairs = [(query, item["content"][:512]) for item, _score in candidates]
            scores = reranker.predict(pairs)

            # 按 Cross-Encoder 得分重排
            reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
            result = [(item, float(score)) for (item, _orig), score in reranked[:k]]
            logger.info(
                f"RAG: Cross-Encoder 重排 {len(candidates)} → {len(result)} "
                f"(top: {result[0][1]:.4f})"
            )
            return result
        except Exception as e:
            logger.warning(f"RAG: Cross-Encoder 重排失败，使用原始排序: {e}")
            return candidates[:k]

    def list_documents(self) -> List[dict]:
        """列出已索引的文档。"""
        if not os.path.exists(DOCS_DIR):
            return []
        files = os.listdir(DOCS_DIR)
        return [
            {
                "name": f,
                "size": os.path.getsize(os.path.join(DOCS_DIR, f)),
                "path": os.path.join(DOCS_DIR, f),
            }
            for f in files
            if os.path.isfile(os.path.join(DOCS_DIR, f))
        ]

    def delete_document(self, filename: str) -> bool:
        """从向量存储中删除文档的所有分块。"""
        try:
            vs = self.vectorstore
            collection = vs._collection
            collection.delete(where={"source": filename})
            # 删除源文件
            file_path = os.path.join(DOCS_DIR, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.info(f"RAG: 已删除文档 {filename}")
            return True
        except Exception as e:
            logger.error(f"RAG: 删除文档失败 {filename}: {e}")
            return False

    def clear(self):
        """清空所有文档和向量数据。"""
        import shutil
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
        if os.path.exists(DOCS_DIR):
            shutil.rmtree(DOCS_DIR)
        os.makedirs(DOCS_DIR, exist_ok=True)
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self._vectorstore = None
        logger.info("RAG: 已清空所有数据")


# 全局单例
_rag_store: Optional[RAGStore] = None


def get_rag_store() -> RAGStore:
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore()
    return _rag_store
