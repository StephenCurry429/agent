# -*- coding: utf-8 -*-
"""
天气助手代理快速开始示例

本脚本演示了如何构建一个功能完整的 LangChain 代理，包括：
1. 详细的系统提示
2. 工具创建与外部数据集成
3. 模型配置
4. 结构化输出
5. 对话记忆
6. 代理创建与运行

参考文档：https://langchain-doc.cn/v1/python/langchain/agents.html
"""

import os
import sys
import time
from dataclasses import dataclass

# 添加项目根目录到 Python 搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from core.config import settings
from tools.weather_tool import get_weather


# 定义详细的系统提示
SYSTEM_PROMPT = """你是一位擅长用双关语表达的专家天气预报员。

你的职责是：
1. 友好地回答用户关于天气的问题
2. 使用双关语让回答更加生动有趣
3. 确保在回答天气问题前知道具体位置
4. 使用 get_weather 工具获取指定位置的天气信息
5. 提供准确、有用的天气信息
6. 注意用户的特殊条件或需求

你可以使用以下工具：
- get_weather：用于获取特定地点的天气
"""


@dataclass
class Context:
    """自定义运行时上下文模式。"""
    user_id: str


# 结构化输出配置
@dataclass
class ResponseFormat:
    """代理的响应模式。"""
    # 带双关语的回应（始终必需）
    punny_response: str
    # 天气的任何有趣信息（如果有）
    weather_conditions: str | None = None
    # 用户的任何特殊条件或需求（如果有）
    user_conditions: str | None = None


# 1. 初始化语言模型
print("正在初始化语言模型...")
model = ChatOpenAI(
    model_name=settings.DEEPSEEK_MODEL_NAME,
    temperature=settings.TEMPERATURE,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE
)

# 2. 定义工具列表
print("正在定义工具列表...")
tools = [get_weather]

# 3. 对话记忆配置
print("正在配置对话记忆...")
checkpointer = InMemorySaver()

# 4. 创建代理
print("正在创建代理...")
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=tools,
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer,
    debug=settings.DEBUG
)


def run_conversation():
    """运行对话示例。"""
    # `thread_id` 是给定对话的唯一标识符
    config = {"configurable": {"thread_id": "1"}}
    
    # 第一次对话
    print("\n=== 第一次对话 ===")
    print("用户: 外面的天气怎么样？")
    response = agent.invoke(
        input={"messages": [{"role": "user", "content": "外面的天气怎么样？"}]},
        config=config,
        context=Context(user_id="1")
    )
    
    structured_response = response.get('structured_response')
    if structured_response:
        print(f"双关语回应: {structured_response.punny_response}")
        print(f"天气状况: {structured_response.weather_conditions}")
        print(f"用户条件: {structured_response.user_conditions}")
    
    # 第二次对话（使用相同的 thread_id）
    time.sleep(2)
    print("\n=== 第二次对话 ===")
    print("用户: 谢谢！明天的天气会怎么样？")
    response = agent.invoke(
        input={"messages": [{"role": "user", "content": "谢谢！明天的天气会怎么样？"}]},
        config=config,
        context=Context(user_id="1")
    )
    
    structured_response = response.get('structured_response')
    if structured_response:
        print(f"双关语回应: {structured_response.punny_response}")
        print(f"天气状况: {structured_response.weather_conditions}")
        print(f"用户条件: {structured_response.user_conditions}")


if __name__ == "__main__":
    print("\n=== LangChain 代理快速开始示例 ===\n")
    run_conversation()
    print("\n=== 示例完成 ===")
