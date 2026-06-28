# -*- coding: utf-8 -*-
"""
LangChain 天气助手示例（接入 DeepSeek 平台）

本示例展示了如何使用 LangChain 创建一个简单的天气查询助手，
包括工具定义、Agent 创建和调用过程，使用 DeepSeek 平台作为模型后端。
"""

import os
import sys

# 添加项目根目录到 Python 搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入必要的模块
# create_agent: 创建 LangChain Agent 的核心函数
# ChatOpenAI: OpenAI 兼容的聊天模型接口
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# 从统一的工具模块中导入天气工具
from tools.weather_tool import weather_search_tool


# 1. 初始化 DeepSeek 平台模型
# 从配置管理模块中读取配置
from core.config import settings

llm = ChatOpenAI(
    model_name=settings.DEEPSEEK_MODEL_NAME,
    temperature=settings.TEMPERATURE,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_API_BASE
)

# 2. 定义工具列表
# 工具是 Agent 可以调用的函数，用于执行特定任务
tools = [weather_search_tool]

# 3. 创建 Agent
# model: 语言模型实例
# tools: Agent 可以使用的工具列表
# system_prompt: 系统提示，定义 Agent 的角色和行为
# debug: 是否开启调试模式，True 会显示详细的思考过程
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个天气助手",
    debug=settings.DEBUG
)

# 4. 调用 Agent
# invoke 方法用于执行 Agent
# 输入格式为字典，包含 messages 键
# messages 是一个列表，每个元素是一个消息对象
# 消息对象包含 role（角色）和 content（内容）
if __name__ == "__main__":
    result = agent.invoke({"messages": [{"role": "user", "content": "北京的天气"}]})

    # 5. 打印结果
    # Agent 的返回结果是一个字典，包含生成的响应
    print(result)
