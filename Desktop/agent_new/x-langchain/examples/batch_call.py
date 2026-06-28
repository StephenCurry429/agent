#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量调用模型示例（使用 `batch` 函数）

本示例演示如何一次性向大模型发送多条请求，适合「多条独立小问答」这类场景，
相比循环逐条调用，可以更好地利用并发能力、减少网络开销。
"""

from __future__ import annotations

import os
import sys
from typing import List

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# 确保能从项目根目录导入 config 等模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings


def build_llm() -> ChatOpenAI:
    """构造一个通用的 LLM，对应 DeepSeek / OpenAI 风格聊天接口。"""
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )


def run_batch_with_strings() -> None:
    """
    使用纯字符串作为输入，演示最简单的 batch 调用方式。

    等价逻辑如果用循环实现，大致是：

    ```python
    for prompt in prompts:
        llm.invoke(prompt)
    ```

    这里改为一次性调用 `llm.batch(prompts)`。
    """
    llm = build_llm()

    cities = ["北京", "上海", "广州", "深圳"]
    prompts: List[str] = [
        f"用一句话介绍一下{city}，不超过 30 个字。" for city in cities
    ]

    print("===== 示例 1：字符串输入的 batch 调用 =====")
    print(f"共 {len(prompts)} 条请求，一次性调用 llm.batch(prompts)\n")

    # 批量调用：返回值是一个「响应列表」，顺序与输入 prompts 一一对应
    responses = llm.batch(prompts)

    for city, resp in zip(cities, responses):
        print(f"{city} -> {resp.content}")


def run_batch_with_messages() -> None:
    """
    使用消息对象（HumanMessage 列表）作为输入，演示更通用的 batch 调用方式。
    """
    llm = build_llm()

    inputs: List[list[HumanMessage]] = [
        [HumanMessage(content="把这句话翻译成英文：你好，世界。")],
        [HumanMessage(content="把这句话翻译成英文：今天天气很好，我们去公园散步。")],
        [HumanMessage(content="把这句话翻译成英文：请尽量简洁。")],
    ]

    print("\n===== 示例 2：消息列表输入的 batch 调用 =====")
    print(f"共 {len(inputs)} 条请求，一次性调用 llm.batch(message_lists)\n")

    responses = llm.batch(inputs)

    for idx, resp in enumerate(responses, start=1):
        print(f"[{idx}] {resp.content}")


if __name__ == "__main__":
    # 直接运行本文件即可看到两个 batch 示例的输出
    run_batch_with_strings()
    run_batch_with_messages()

