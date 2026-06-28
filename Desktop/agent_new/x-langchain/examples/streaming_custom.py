# -*- coding: utf-8 -*-
"""
LangChain 自定义更新示例

本示例展示了如何使用 LangChain 的自定义更新功能，发出用户定义的信号。

参考文档：https://langchain-doc.cn/v1/python/langchain/streaming.html#%E8%87%AA%E5%AE%9A%E4%B9%89%E6%9B%B4%E6%96%B0-custom-updates
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
from constants import STREAM_MODE_CUSTOM


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


def run_custom_updates_example():
    """运行自定义更新示例。"""
    # 4. 使用 stream 方法执行代理（展示自定义更新）
    user_input = "广州的天气怎么样？"

    # 使用 stream 方法获取自定义更新（设置 stream_mode="custom"）
    print(f"\n用户输入: {user_input}")
    print("\n=== 自定义更新示例 ===")
    print("正在生成响应...")

    # 迭代处理自定义更新
    for chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        config={"run_name": "Weather Assistant"},
        stream_mode=STREAM_MODE_CUSTOM
    ):
        print(chunk)

    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    run_custom_updates_example()
