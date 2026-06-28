# -*- coding: utf-8 -*-
"""
工具错误处理中间件示例

本示例演示如何使用 `wrap_tool_call` 在工具执行发生异常时，
向模型返回一条自定义的错误消息，而不是让异常直接抛出。
"""

import os
import sys

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# 添加项目根目录到 Python 搜索路径（与其他示例保持一致）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings
from tools import web_search_tool, weather_search_tool


@wrap_tool_call
def handle_tool_errors(request, handler):
    """使用自定义消息处理工具执行错误。"""
    try:
        return handler(request)
    except Exception as e:
        # 向模型返回自定义错误消息，提示检查输入参数
        return ToolMessage(
            content=f"调用工具出错，请检查输入参数并重试。（错误信息: {str(e)}）",
            tool_call_id=request.tool_call["id"],
        )


@tool
def error_demo_tool(city: str) -> str:
    """演示用：总是抛出异常的工具，用于测试错误处理中间件。"""
    raise ValueError(f"这是一个演示用异常，city 参数值为: {city}")


def run_handle_tool_errors_example() -> None:
    """运行工具错误处理中间件示例。"""
    print("正在初始化语言模型...")
    llm = ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )

    print("正在初始化工具...")

    # 包含一个专门用于演示的“必然报错”工具，确保中间件能够捕获到异常
    tools = [web_search_tool, weather_search_tool, error_demo_tool]

    print("正在创建 Agent（挂载工具错误处理中间件）...")
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=(
            "你是一个助手，能够使用联网搜索和天气查询工具。"
            "此外，还有一个名为 error_demo_tool 的工具，它总是会抛出异常，"
            "用于测试工具错误处理中间件。当你想演示错误处理效果时，可以调用它。"
        ),
        middleware=[handle_tool_errors],
        debug=settings.DEBUG,
    )

    # 为了方便手动测试，这里给出一个示例输入
    user_input = "帮我查一下北京今天的天气，并顺便在网上搜一下最近的新闻。"
    print(f"\n用户输入: {user_input}")

    result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    print("\n=== 最终回答 ===")
    print(result)


if __name__ == "__main__":
    run_handle_tool_errors_example()