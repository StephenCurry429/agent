# -*- coding: utf-8 -*-
"""
上下文压缩模块

实现对话上下文的智能压缩，防止上下文窗口溢出：

1. 令牌计数 — 基于字符数/词数的轻量估算
2. 摘要式压缩 — 超阈值时将旧消息压缩成摘要
3. 滑动窗口 — 保留最近 N 轮完整对话，更早的合并为摘要
4. 增量压缩 — 每次只增量更新摘要，避免重复调用 LLM
"""

import tiktoken
from typing import List, Tuple, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .logger import logger

# 压缩触发阈值（按消息条数，每条 ≈ 大模型一轮对话）
COMPRESS_THRESHOLD = 40  # 超过 40 条消息开始压缩（约 20 轮对话）

# 滑动窗口：保留最近 N 条完整消息不压缩
SLIDING_WINDOW = 20  # 最近 20 条（约 10 轮对话）保持完整

# 首次压缩时保留多少条旧消息给 LLM 做摘要
SUMMARY_INPUT_SIZE = 40  # 用前 40 条消息生成摘要


def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量（中文按 2 字/token，英文按 4 字/token）。"""
    chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other = len(text) - chinese
    return chinese // 2 + other // 4 + 1


def estimate_messages_tokens(messages: List[BaseMessage]) -> int:
    """估算消息列表的总 token 数。"""
    total = 0
    for msg in messages:
        if isinstance(msg, SystemMessage):
            # 系统消息有额外开销
            total += estimate_tokens(msg.content) + 4
        elif isinstance(msg, HumanMessage):
            total += estimate_tokens(msg.content) + 4
        elif isinstance(msg, AIMessage):
            total += estimate_tokens(msg.content) + 4
        else:
            total += estimate_tokens(str(msg)) + 4
    return total


def _summarize_messages(
    messages: List[BaseMessage],
    chat_model,
) -> str:
    """
    用 LLM 将一段历史消息压缩为简洁摘要。

    返回一段自然语言摘要，保留关键信息：
    - 用户问过什么
    - AI 回答了什么
    - 关键决策、数据、结论
    """
    # 构建摘要提示
    lines = ["请将以下对话历史压缩为一段简洁的摘要，保留所有关键信息：\n"]
    for msg in messages:
        role = "用户" if isinstance(msg, HumanMessage) else ("助手" if isinstance(msg, AIMessage) else "系统")
        content = msg.content[:800]  # 每条截断以控制输入长度
        lines.append(f"[{role}]: {content}")
    lines.append("\n摘要（保留时间线、关键数据、决策和结论）：")

    summary_prompt = "\n".join(lines)

    try:
        from langchain_core.messages import HumanMessage as LC_HumanMessage
        response = chat_model.invoke([LC_HumanMessage(content=summary_prompt)])
        summary = response.content.strip()
        logger.info(f"上下文压缩完成: {len(messages)} 条消息 → {len(summary)} 字符摘要")
        return summary
    except Exception as e:
        logger.warning(f"上下文摘要生成失败，使用简单拼接: {e}")
        # 降级：简单拼接前 500 字
        fallback = " ".join(m.content[:200] for m in messages[:5])
        return f"[历史对话摘要] {fallback}..."


class ContextCompressor:
    """
    上下文压缩管理器。

    按会话隔离，每个 session 维护：
    - full_history: 完整消息列表（不压缩时即为此）
    - summary: 压缩后的摘要文本
    - recent_messages: 滑动窗口内的最近消息

    对外透明：调用 get_compressed_context() 即可获得压缩后的上下文。
    """

    def __init__(self):
        self._summaries: dict = {}       # session_id → 摘要字符串
        self._full_histories: dict = {}  # session_id → 完整历史
        self._chat_model = None

    @property
    def chat_model(self):
        """延迟加载摘要用的 LLM（轻量模型即可）。"""
        if self._chat_model is None:
            from langchain_openai import ChatOpenAI
            import os
            from .config import settings

            # 摘要用模型：优先用小模型降低成本
            model = os.getenv("SUMMARY_MODEL", settings.OPENAI_MODEL_NAME or "gpt-3.5-turbo")
            self._chat_model = ChatOpenAI(
                model=model,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                temperature=0.3,
                max_tokens=512,
            )
        return self._chat_model

    def should_compress(self, session_id: str) -> bool:
        """判断是否需要执行压缩。"""
        history = self._full_histories.get(session_id, [])
        return len(history) > COMPRESS_THRESHOLD

    def compress(self, session_id: str, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        执行上下文压缩。

        返回压缩后的消息列表 = [SystemMessage(摘要)] + 滑动窗口内的最近消息。

        Args:
            session_id: 会话 ID
            messages: 完整的消息历史

        Returns:
            压缩后的消息列表
        """
        n = len(messages)
        if n <= COMPRESS_THRESHOLD:
            return messages  # 不需要压缩

        # 增量压缩：如果之前已有摘要，只对新消息做增量
        existing_summary = self._summaries.get(session_id, "")

        if existing_summary:
            # 增量模式：将超出滑动窗口的新消息追加到摘要中
            old_count = len(self._full_histories.get(session_id, []))
            new_old_msgs = messages[old_count:-SLIDING_WINDOW] if old_count < n - SLIDING_WINDOW else []
            if new_old_msgs:
                delta_summary = _summarize_messages(new_old_msgs, self.chat_model)
                existing_summary = f"{existing_summary}\n{delta_summary}"
                logger.info(f"增量压缩: +{len(new_old_msgs)} 条新消息追加到摘要")
        else:
            # 首次压缩：取前 SUMMARY_INPUT_SIZE 条做摘要
            old_messages = messages[:min(SUMMARY_INPUT_SIZE, n - SLIDING_WINDOW)]
            if old_messages:
                existing_summary = _summarize_messages(old_messages, self.chat_model)

        # 更新存储
        self._summaries[session_id] = existing_summary
        self._full_histories[session_id] = list(messages)

        # 构建压缩后的上下文：摘要 + 滑动窗口最近消息
        recent = messages[-SLIDING_WINDOW:]
        compressed = []

        if existing_summary:
            compressed.append(SystemMessage(
                content=f"[历史对话摘要 - 以下为此前对话的关键信息]\n{existing_summary}"
            ))

        compressed.extend(recent)

        orig_tokens = estimate_messages_tokens(messages)
        comp_tokens = estimate_messages_tokens(compressed)
        logger.info(
            f"上下文压缩: {n} 条消息 ({orig_tokens}tok) → "
            f"{len(compressed)} 条 ({comp_tokens}tok), "
            f"压缩比 {comp_tokens/max(orig_tokens,1):.1%}"
        )

        return compressed

    def get_compressed_context(
        self,
        session_id: str,
        messages: List[BaseMessage],
    ) -> List[BaseMessage]:
        """获取压缩后的上下文（对外统一接口）。"""
        if self.should_compress(session_id):
            return self.compress(session_id, messages)
        return messages

    def clear(self, session_id: str):
        """清理指定会话的压缩缓存。"""
        self._summaries.pop(session_id, None)
        self._full_histories.pop(session_id, None)


# 全局单例
_compressor: Optional[ContextCompressor] = None


def get_compressor() -> ContextCompressor:
    """获取全局压缩器单例。"""
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor
