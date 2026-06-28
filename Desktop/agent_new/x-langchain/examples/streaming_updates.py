# -*- coding: utf-8 -*-
"""
LangChain 代理进度示例

本示例展示了如何使用 LangChain 的代理进度功能，在每个代理步骤后获取状态更新，
包括思考、工具调用和响应等步骤。

参考文档：https://langchain-doc.cn/v1/python/langchain/streaming.html#%E6%A6%82%E8%BF%B0-overview
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
from constants import STREAM_MODE_UPDATES


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


def run_agent_progress_example():
    """运行代理进度示例。"""
    # 4. 使用 stream 方法执行代理（展示代理进度）
    user_input = "漠河的天气怎么样？"
    print(f"\n用户输入: {user_input}")
    print("\n=== 代理执行过程（实时） ===")
    print("正在生成响应...")

    # 收集所有消息
    all_messages = []

    # 迭代处理每一个步骤
    for chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"run_name": "Weather Assistant"},
        stream_mode=STREAM_MODE_UPDATES
    ):
        for step, data in chunk.items():
            print(f"step: {step}")
            print(f"content: {data['messages'][-1].content_blocks}")
            print()
            # 收集消息
            all_messages.append(data['messages'][-1])

    # 5. 处理最终结果
    print("\n=== 最终结果 ===")
    print("收集到的消息数量:", len(all_messages))
    if all_messages:
        print("最后一条消息类型:", type(all_messages[-1]))
        last_message = all_messages[-1]
        if hasattr(last_message, "content"):
            print("最终回答:")
            print(last_message.content)
        else:
            print("最终回答 (无content属性):")
            print(last_message)

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    run_agent_progress_example()
