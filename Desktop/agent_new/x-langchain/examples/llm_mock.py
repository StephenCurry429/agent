# pip install -qU "langchain[anthropic]" 调用模型

import os
import sys

# 添加项目根目录到 Python 搜索路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.agents import create_agent

# 从统一的工具模块中导入天气工具
from tools.weather_tool import weather_search_tool

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[weather_search_tool],
    system_prompt="你是一个乐于助人的助手",
)

# 执行代理
if __name__ == "__main__":
    agent.invoke({"messages": [{"role": "user", "content": "旧金山天气如何？"}]})
