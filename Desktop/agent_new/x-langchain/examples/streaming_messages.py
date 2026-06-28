# -*- coding: utf-8 -*-
"""
LLM 令牌流式传输示例

本示例展示了如何使用 LangChain 的流式传输功能，在语言模型生成令牌时进行流式传输。
以实现更流畅的用户体验。

参考文档：https://langchain-doc.cn/v1/python/langchain/streaming.html#llm-%E4%BB%A4%E7%89%8C-llm-tokens
"""

# 添加项目根目录到 Python 搜索路径（特殊处理）
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from tools.weather_tool import get_weather
from core.config import settings
from constants import STREAM_MODE_MESSAGES


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


def run_messages_streaming_example():
    """运行LLM令牌流式传输示例。"""
    # 4. 使用 stream 方法执行代理（展示代理进度）
    user_input = "漠河的天气怎么样？"

    # 使用 stream 方法获取代理执行过程（设置 stream_mode="messages"）
    print(f"\n用户输入: {user_input}")
    print("\n=== 代理执行过程（实时） ===")
    print("正在生成响应...")

    # 收集所有消息
    all_messages = []

    # 迭代处理每个步骤
    for chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"run_name": "Weather Assistant"},
        stream_mode=STREAM_MODE_MESSAGES
    ):
        for step, data in chunk.items():
            print(f"\nstep: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")

            # 收集消息
            all_messages.append(data['messages'][-1])

    # 5. 展示最终结果
    print("=== 最终结果 ===")
    if all_messages:
        final_message = all_messages[-1]
        if hasattr(final_message, "content_blocks"):
            print("最终回答:")
            for block in final_message.content_blocks:
                if block.get("type") == "text":
                    print(block.get("text"))

    print("\n=== 示例完成 ===")
    print("\n提示：在实际应用中，您可以使用这种令牌级别的流式传输来实现:")
    print("1. 实时显示AI生成的文本，提高用户体验")
    print("2. 在生成过程中添加动画效果")
    print("3. 实现打字机效果的输出")
    print("4. 允许用户在生成过程中中断或修改请求")


if __name__ == "__main__":
    run_messages_streaming_example()
