# -*- coding: utf-8 -*-
"""
LangChain 流式传输多种模式示例

本示例展示了如何同时使用多种流式传输模式，可选择 updates（代理进度）、messages（LLM 令牌 + 元数据）或 custom（任意用户数据）。

参考文档：https://langchain-doc.cn/v1/python/langchain/streaming.html#%E6%B5%81%E5%BC%8F%E4%BC%A0%E8%BE%93%E5%A4%9A%E7%A7%8D%E6%A8%A1%E5%BC%8F-stream-multiple-modes
"""

# 添加项目根目录到 Python 搜索路径（特殊处理）
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from core.config import settings
from constants import STREAM_MODE_UPDATES, STREAM_MODE_CUSTOM, STREAM_MODE_MESSAGES


# 定义带自定义更新的天气工具
def get_weather(city: str) -> str:
    """获取给定城市的天气。"""
    writer = get_stream_writer()  # 获取流写入器
    # 流式传输自定义更新
    writer(f"正在查询城市: {city}")
    writer(f"正在获取天气数据: {city}")
    
    # 模拟天气数据获取延迟
    import time
    time.sleep(1)
    
    writer(f"已获取天气数据: {city}")
    
    # 返回天气信息
    return f"{city}的天气晴朗，气温适宜。"


# 1. 初始化语言模型
print("正在初始化语言模型...")
llm = ChatOpenAI(
    model_name=settings.DEEPSEEK_MODEL_NAME,
    temperature=settings.TEMPERATURE,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE
)

# 2. 定义工具列表
print("正在定义工具列表...")
tools = [get_weather]

# 3. 创建代理
print("正在创建代理...")
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个天气助手，负责回答用户的天气查询问题。",
    debug=settings.DEBUG
)


def run_multi_modes_streaming_example():
    """运行多种流式传输模式示例。"""
    # 4. 使用 stream 方法执行代理（展示多种流式传输模式）
    user_input = "深圳的天气怎么样？"

    # 使用 stream 方法同时获取代理进度、自定义更新和LLM令牌（设置 stream_mode=[STREAM_MODE_UPDATES, STREAM_MODE_CUSTOM, STREAM_MODE_MESSAGES]）
    print(f"\n用户输入: {user_input}")
    print("\n=== 流式传输多种模式示例 ===")
    print("正在生成响应...")

    # 执行流式传输
    for stream_mode, chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"run_name": "Weather Assistant"},
        stream_mode=[STREAM_MODE_UPDATES, STREAM_MODE_CUSTOM, STREAM_MODE_MESSAGES]
    ):
        print(f"stream_mode: {stream_mode}")
        print(f"content: {chunk}")
        print()

    print("\n=== 示例完成 ===")
    print("\n提示：通过将流模式作为列表传递，您可以同时获取:")
    print("1. updates - 代理执行的步骤更新")
    print("2. custom - 工具执行过程中的自定义更新")
    print("3. messages - LLM生成的令牌")
    print("这样可以同时监控代理的执行过程和工具的内部状态变化。")


if __name__ == "__main__":
    run_multi_modes_streaming_example()
