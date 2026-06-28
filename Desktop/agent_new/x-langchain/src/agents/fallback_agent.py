# -*- coding: utf-8 -*-
"""
链路回退 Agent

当主模型调用失败时，自动按链路依次回退到备用模型。
支持每个模型重试，最终兜底返回友好的错误提示。
"""

import asyncio
import time
from typing import Any, List, Optional

from core import logger
from core.config import settings
from models import create_chat_model
from tools import get_all_tools


# ── 链路回退顺序，按优先级从高到低 ──
# 主模型由配置 MODLE_NAME 决定，这里定义回退链路
DEFAULT_FALLBACK_CHAIN = ["deepseek", "doubao", "mock"]

# 每个模型最多重试次数
MAX_RETRIES_PER_MODEL = 2

# 重试间隔基数（秒）
RETRY_BASE_DELAY = 2


def _build_agent_for_model(model_name: str):
    """为指定模型创建一个 Agent 实例。"""
    from langchain.agents import create_agent

    model = create_chat_model(model_name)
    tools_list = get_all_tools()
    return create_agent(
        model=model,
        tools=tools_list,
        system_prompt="""你是一个友好、专业的智能助手。

## 角色设定

每条回复开头先说"你好主人"，然后再回答问题。

## 输出格式（必须遵守）

1. 用 Markdown 结构回复：## 标题 / **粗体** / `代码` / - 列表 / > 引用
2. 代码必须用 ``` 代码块包裹，标注语言
3. 多条信息用列表，不要用逗号堆砌
4. 重要结论放最前面，先说结论再解释

## 工具使用

当用户需要实时信息或外部数据时，优先调用工具。使用工具后，请清晰总结工具结果，
不要编造事实。

## 搜索回答格式（强制）

1. 仅基于检索到的权威公开信息作答，信息不明确就如实说明，绝对禁止编造
2. 关键数据须对应具体官方来源，标注发布机构与时间
3. 检索匹配度不足时，直接告知"未查询到相关公开信息"，不得引申或拼接无关内容
4. 正文仅展示整理后的结论，自然流畅，不提及检索过程
5. 禁止列出编号搜索列表、完整URL或逐条复述原始摘要
6. 禁止出现"搜索结果显示""根据搜索结果"等过程描述
7. 链接自动在搜索资源区展示，正文无需重复

遇到数据库问题时，请遵循 TextToSQL 流程：改写问题、查看表结构、
生成 SQL、校验 SQL、执行 SQL，然后用自然语言解释结果。
""",
        debug=False,
    )


class FallbackAgent:
    """
    带链路回退的 Agent 包装器。

    调用链:
      主模型 (2次重试) → deepseek (2次重试) → doubao (2次重试) → mock (兜底)

    每次模型切换时记录日志并增加回退延迟。
    """

    def __init__(self, primary_model: str, fallback_chain: Optional[List[str]] = None):
        self.primary_model = primary_model
        self.fallback_chain = fallback_chain or DEFAULT_FALLBACK_CHAIN

        # 过滤掉与主模型重名的备选
        self.candidates = [primary_model] + [
            m for m in self.fallback_chain if m != primary_model
        ]
        logger.info(
            f"FallbackAgent 链路: {' → '.join(self.candidates)}"
        )

    async def _try_invoke(self, model_name: str, all_messages: list, config: dict) -> tuple[str, str]:
        """
        尝试用指定模型调用并返回 (response, model_used)。

        Raises:
            Exception: 调用失败时抛出
        """
        agent = _build_agent_for_model(model_name)
        result = await agent.ainvoke(
            {"messages": all_messages},
            config=config,
        )

        response = ""
        if isinstance(result, dict) and 'messages' in result:
            messages = result.get('messages', [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
                elif isinstance(last_message, dict):
                    response = last_message.get('content', '')
        elif hasattr(result, 'content'):
            response = result.content
        else:
            response = str(result)

        return response, model_name

    async def invoke(self, all_messages: list, config: Optional[dict] = None) -> tuple[str, str]:
        """
        带链路回退的调用。

        Returns:
            (response_text, model_used)
        """
        if config is None:
            config = {"run_name": "Fallback Chat"}

        last_error = None
        for i, model_name in enumerate(self.candidates):
            for attempt in range(MAX_RETRIES_PER_MODEL):
                try:
                    logger.info(
                        f"[Fallback] 尝试模型 {model_name} (第 {attempt + 1} 次)"
                    )
                    response, used_model = await self._try_invoke(
                        model_name, all_messages, config
                    )
                    if i > 0:
                        logger.warning(
                            f"[Fallback] 主模型失败，已回退到 {used_model}"
                        )
                    return response, used_model
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[Fallback] 模型 {model_name} 第 {attempt + 1} 次调用失败: {e}"
                    )
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        delay = RETRY_BASE_DELAY * (attempt + 1)
                        logger.info(f"[Fallback] {delay}s 后重试...")
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(
                            f"[Fallback] 模型 {model_name} 已耗尽重试，切换到下一个"
                        )

            # 切换到下一个模型前等待
            if i < len(self.candidates) - 1:
                await asyncio.sleep(1)

        # 所有模型都失败，兜底返回
        error_msg = (
            f"抱歉，所有模型均调用失败。最后错误: {last_error}"
        )
        logger.error(f"[Fallback] 全部模型失败: {error_msg}")
        return error_msg, "fallback_error"

    async def astream(self, all_messages: list, config: Optional[dict] = None, stream_mode: str = "messages"):
        """
        带链路回退的流式调用。

        Yields:
            (token_or_tool_name, enriched_metadata, model_name) 或最终 done 信号

        元数据包含:
          - _msg_type: 消息类型 (AIMessageChunk / ToolMessage)
          - _tool_calls: [tool_name, ...] 本轮调用的工具名列表
          - _tool_result: True 表示这是工具返回值
          - _tool_name: 工具名 (仅 ToolMessage)
        """
        if config is None:
            config = {"run_name": "Fallback Stream"}

        last_error = None
        for i, model_name in enumerate(self.candidates):
            for attempt in range(MAX_RETRIES_PER_MODEL):
                try:
                    logger.info(
                        f"[Fallback] 流式尝试模型 {model_name} (第 {attempt + 1} 次)"
                    )
                    agent = _build_agent_for_model(model_name)
                    full = ""
                    async for chunk in agent.astream(
                        {"messages": all_messages},
                        config=config,
                        stream_mode=stream_mode,
                    ):
                        if isinstance(chunk, tuple) and len(chunk) == 2:
                            message_chunk, raw_meta = chunk

                            # ── 构建增强元数据 ──
                            if isinstance(raw_meta, dict):
                                meta = dict(raw_meta)
                            else:
                                meta = {}
                            msg_type = type(message_chunk).__name__
                            meta["_msg_type"] = msg_type

                            # 检测 tool_calls（AIMessageChunk 带 tool_calls 时 content 可能为空）
                            tc_list = getattr(message_chunk, "tool_calls", None)
                            if tc_list:
                                tc_names = []
                                for tc in tc_list:
                                    name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                                    tc_names.append(name)
                                meta["_tool_calls"] = tc_names

                            # 检测 ToolMessage（工具返回结果）
                            if msg_type == "ToolMessage":
                                meta["_tool_result"] = True
                                meta["_tool_name"] = getattr(message_chunk, "name", "")

                            content = getattr(message_chunk, "content", "") or ""
                            if content:
                                full += content
                            elif not tc_list:
                                # 既无内容也无 tool_calls，跳过无意义 chunk
                                continue

                            yield (content, meta, model_name)

                    if i > 0:
                        logger.warning(
                            f"[Fallback] 主模型失败，已回退到 {model_name}"
                        )
                    yield ("", None, model_name)
                    return
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"[Fallback] 模型 {model_name} 第 {attempt + 1} 次流式调用失败: {e}"
                    )
                    if attempt < MAX_RETRIES_PER_MODEL - 1:
                        delay = RETRY_BASE_DELAY * (attempt + 1)
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(
                            f"[Fallback] 模型 {model_name} 已耗尽重试，切换到下一个"
                        )

            if i < len(self.candidates) - 1:
                await asyncio.sleep(1)

        # 兜底
        error_msg = f"抱歉，所有模型均调用失败。最后错误: {last_error}"
        logger.error(f"[Fallback] 全部模型失败: {error_msg}")
        yield (error_msg, None, "fallback_error")
