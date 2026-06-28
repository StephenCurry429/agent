# -*- coding: utf-8 -*-
"""
语义会话记忆模块

将每轮对话存入向量库，新问题时语义检索相关历史对话，
实现跨会话、跨时间的智能记忆召回。

核心流程:
1. 存储: 每轮对话 → embedding → ChromaDB
2. 检索: 当前问题 → 语义检索 + 关键词匹配 → Top-K 相关历史
3. 注入: 历史记忆作为 SystemMessage 插入上下文
"""

import os
import re
import time
import uuid
import json
from typing import List, Optional, Dict, Tuple

import jieba

from .config import settings
from .logger import logger

# 记忆存储目录
_MEMORY_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "semantic_memory"
)
_MEMORY_CHROMA_DIR = os.path.join(_MEMORY_DATA_DIR, "chroma")
_MEMORY_JSON_PATH = os.path.join(_MEMORY_DATA_DIR, "memories.jsonl")

# 检索配置
MEMORY_RETRIEVAL_K = 4         # 每次检索返回的记忆条数
MEMORY_MAX_STORE = 1000        # 最多存储 N 条记忆
MEMORY_MIN_SCORE = 0.35        # 最低相关性阈值（低于此不注入）


def _get_shared_embeddings():
    """从 RAG 模块获取共享的 embedding 实例，避免重复加载。"""
    try:
        from rag.vector_store import _get_embeddings
        return _get_embeddings()
    except Exception:
        logger.warning("语义记忆: 无法获取共享 embedding，语义检索不可用")
        return None


def _tokenize_keywords(text: str) -> List[str]:
    """提取中文关键词用于 BM25 后备检索。"""
    words = jieba.lcut(text)
    result = []
    for w in words:
        w = w.strip()
        if not w or len(w) == 1:
            continue
        # 过滤语气词、标点
        if re.match(r'^[，,。！!？?\s；;：:、\d]+$', w):
            continue
        result.append(w)
    return list(set(result))  # 去重


class SemanticMemory:
    """
    语义会话记忆管理器。

    每个记忆条目结构:
        {
            "id": "mem-xxx",
            "session_id": "sess-xxx",
            "query": "用户问题",
            "response_summary": "AI 回答的前 300 字",
            "timestamp": 1234567890.0,
            "topics": ["话题1", "话题2"],
        }

    存储: JSONL 文件 + ChromaDB 向量库
    检索: 语义相似度 + 关键词匹配 → 加权融合
    """

    def __init__(self):
        os.makedirs(_MEMORY_DATA_DIR, exist_ok=True)
        os.makedirs(_MEMORY_CHROMA_DIR, exist_ok=True)

        self._embeddings = None
        self._embeddings_available = True
        self._vectorstore = None
        self._memory_cache: List[dict] = []  # 内存缓存，BM25 后备

        self._load_memories()

    def _load_memories(self):
        """从 JSONL 文件恢复记忆缓存。"""
        if not os.path.exists(_MEMORY_JSON_PATH):
            return
        try:
            with open(_MEMORY_JSON_PATH, "r", encoding="utf-8") as f:
                self._memory_cache = [json.loads(line) for line in f if line.strip()]
            logger.info(f"语义记忆: 从文件恢复 {len(self._memory_cache)} 条记忆")
        except Exception as e:
            logger.warning(f"语义记忆: 恢复失败 {e}")

    def _save_memories(self):
        """保存记忆到 JSONL 文件。"""
        try:
            with open(_MEMORY_JSON_PATH, "w", encoding="utf-8") as f:
                for m in self._memory_cache[-MEMORY_MAX_STORE:]:
                    f.write(json.dumps(m, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"语义记忆: 持久化失败 {e}")

    @property
    def embeddings(self):
        if self._embeddings is None and self._embeddings_available:
            try:
                self._embeddings = _get_shared_embeddings()
            except Exception:
                self._embeddings_available = False
        return self._embeddings

    @property
    def vectorstore(self):
        if self._vectorstore is None and self._embeddings_available and self.embeddings:
            try:
                from langchain_chroma import Chroma
                self._vectorstore = Chroma(
                    persist_directory=_MEMORY_CHROMA_DIR,
                    embedding_function=self.embeddings,
                    collection_name="semantic_memory",
                )
            except Exception as e:
                logger.warning(f"语义记忆: ChromaDB 初始化失败 {e}")
                self._embeddings_available = False
        return self._vectorstore

    def _extract_topics(self, text: str) -> List[str]:
        """从文本中提取关键词作为话题标签。"""
        return _tokenize_keywords(text)[:5]

    def add_memory(self, session_id: str, query: str, response: str) -> str:
        """
        存储一条对话记忆。

        Returns:
            记忆 ID
        """
        mem_id = f"mem-{uuid.uuid4().hex[:12]}"
        topics = self._extract_topics(query)

        memory = {
            "id": mem_id,
            "session_id": session_id,
            "query": query,
            "response_summary": response[:300],
            "timestamp": time.time(),
            "topics": topics,
        }

        # 写入内存缓存
        self._memory_cache.append(memory)
        if len(self._memory_cache) > MEMORY_MAX_STORE:
            self._memory_cache = self._memory_cache[-MEMORY_MAX_STORE:]

        # 写入向量库
        if self._embeddings_available and self.vectorstore:
            try:
                from langchain_core.documents import Document
                doc = Document(
                    page_content=f"Q: {query}\nA: {response[:300]}",
                    metadata={"memory_id": mem_id, "session_id": session_id,
                               "timestamp": str(time.time())},
                )
                self.vectorstore.add_documents([doc])
            except Exception as e:
                logger.warning(f"语义记忆: 向量写入失败 {e}")

        # 持久化到 JSONL（每 10 条写一次，降低 IO）
        if len(self._memory_cache) % 10 == 0:
            self._save_memories()

        logger.info(f"语义记忆: 已存储 [{mem_id}] topic={topics[:3]}")
        return mem_id

    def retrieve(self, query: str, k: int = MEMORY_RETRIEVAL_K) -> List[Dict]:
        """
        检索与当前问题相关的历史记忆。

        策略：语义相似度（如果可用）+ 关键词匹配 → 加权融合排序
        """
        if not self._memory_cache:
            return []

        results = []

        # --- 语义检索 ---
        semantic_scores: Dict[str, float] = {}
        if self._embeddings_available and self.vectorstore:
            try:
                raw = self.vectorstore.similarity_search_with_relevance_scores(query, k=k * 2)
                for doc, score in raw:
                    mid = doc.metadata.get("memory_id", "")
                    if mid:
                        semantic_scores[mid] = score
            except Exception as e:
                logger.warning(f"语义记忆检索失败: {e}")

        # --- 关键词匹配 ---
        qtokens = _tokenize_keywords(query)
        for mem in self._memory_cache:
            if not qtokens:
                continue
            kw_score = 0.0
            mem_text = f"{mem['query']} {' '.join(mem.get('topics', []))}"
            for token in qtokens:
                if token in mem_text:
                    kw_score += 1.0
            if kw_score > 0:
                kw_score = kw_score / len(qtokens)
                semantic_scores[mem["id"]] = (
                    semantic_scores.get(mem["id"], 0) * 0.6 + kw_score * 0.4
                )

        # 收集候选
        for mem in self._memory_cache:
            mid = mem["id"]
            score = semantic_scores.get(mid, 0)
            if score >= MEMORY_MIN_SCORE:
                results.append((mem, score))

        # 按得分降序
        results.sort(key=lambda x: x[1], reverse=True)
        top = results[:k]

        if top:
            logger.info(
                f"语义记忆检索: query='{query[:30]}...' → {len(top)}/{len(self._memory_cache)} 条"
                f" (top: {top[0][1]:.4f})"
            )

        return [mem for mem, _score in top]

    def format_for_context(self, memories: List[Dict]) -> str:
        """
        将检索到的历史记忆格式化为上下文文本，注入给 AI。
        """
        if not memories:
            return ""

        lines = ["[历史相关记忆] 以下是此前与此话题相关的对话片段："]
        for i, mem in enumerate(memories, 1):
            ts = time.strftime("%m-%d %H:%M", time.localtime(mem["timestamp"]))
            lines.append(
                f"\n  [{i}] ({ts}) Q: {mem['query'][:200]}\n"
                f"       A: {mem['response_summary'][:200]}"
            )
        return "\n".join(lines)

    def clear(self):
        """清空所有记忆。"""
        self._memory_cache = []
        if self._vectorstore:
            try:
                self._vectorstore._collection.delete(where={})
            except Exception:
                pass
        self._save_memories()
        logger.info("语义记忆: 已清空")


# 全局单例
_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory() -> SemanticMemory:
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory()
    return _semantic_memory
