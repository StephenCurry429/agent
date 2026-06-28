# -*- coding: utf-8 -*-
"""
动态模型选择中间件示例

本示例演示如何使用 `wrap_model_call` 中间件，根据对话轮数在「基础模型」
和「高级模型」之间动态切换，结合本项目 examples 下的统一风格和模型定义方式。
"""

import os
import sys

from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain_openai import ChatOpenAI

# 添加项目根目录到 Python 搜索路径（与其他示例保持一致）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings


def build_basic_model() -> ChatOpenAI:
    """基础模型：适合简单、短对话。"""
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )


def build_advanced_model() -> ChatOpenAI:
    """高级模型：用于更复杂、轮次更多的对话。

    这里为了示例简单，仍然复用同一组 DeepSeek 配置，
    在真实项目中你可以切换到更强的模型或不同提供商。
    """
    return ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )


# 预先构造两个模型实例，供中间件动态选择
basic_model = build_basic_model()
advanced_model = build_advanced_model()


# 1. 定义动态模型选择中间件
@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """根据对话消息数动态选择模型。"""
    # 获取当前对话消息数
    message_count = len(request.state["messages"])

    print(f"当前对话消息数: {message_count}")

    if message_count >= 3:
        # 对话消息数超过 2 条，切换至更强大的模型处理复杂对话
        model = advanced_model
        print(">>> 已切换到【高级模型】处理当前请求")
    else:
        model = basic_model
        print(">>> 使用【基础模型】处理当前请求")

    return handler(request.override(model=model))


# 2. 定义工具（与其他示例风格一致）
@tool
def get_current_location() -> str:
    """获取当前位置。"""
    return "当前位置为北京市。"


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息。"""
    return f"{city}的天气为晴朗，25°C。"


def run_dynamic_model_selection_example() -> None:
    """运行动态模型选择示例。"""
    print("正在创建 Agent（挂载动态模型选择中间件）...")

    agent = create_agent(
        model=basic_model,  # 设置一个默认模型，实际由中间件决定最终使用哪个
        tools=[get_current_location, get_weather],
        system_prompt="你是一个助手，可以帮助用户回答各种问题。",
        middleware=[dynamic_model_selection],
        debug=settings.DEBUG,
    )

    # 模拟一个对话的调用，包含获取当前位置和天气信息
    user_input = "获取当前位置，并告诉我天气情况"
    print(f"\n用户输入: {user_input}")

    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print("\n=== 最终回答 ===")
    print(result)


if __name__ == "__main__":
    run_dynamic_model_selection_example()