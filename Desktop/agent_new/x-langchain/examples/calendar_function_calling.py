# -*- coding: utf-8 -*-
"""
Calendar Tool Function Calling 示例

目标：跑起来就是「用户一句话 → 模型自动调用日历工具 → 返回结果」。

运行：
  python examples/calendar_function_calling.py

前置：
  - 在项目根目录配置好 .env（至少 DeepSeek 的 API 配置，见 core/config.py）
"""

import os
import sys

# Windows 终端默认编码可能导致中文乱码，这里尽量统一输出编码
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 添加项目根目录到 Python 搜索路径（与其他示例保持一致）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from core.config import settings
from constants import STREAM_MODE_UPDATES
from tools import calendar_tool


SYSTEM_PROMPT = """你是一个日程/日期助手。

当用户询问某一天（如“今天/明天/2024-10-01”）对应的星期、是否周末、节日等信息时，
你必须调用日历工具 `search_calendar` 获取结果，然后基于工具返回内容答复用户。

工具参数说明：
- `datetime` 字段除了支持 `YYYY-MM-DD`，也支持自然语言：今天 / 明天 / 昨天（直接原样传入即可）。

注意：如果用户没有明确日期，请先向用户追问日期再调用工具。
"""


def run() -> None:
    llm = ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )

    agent = create_agent(
        model=llm,
        tools=[calendar_tool],
        system_prompt=SYSTEM_PROMPT,
        debug=settings.DEBUG,
    )

    user_input = "帮我查一下明天是星期几？如果有节日也告诉我。"
    print(f"用户: {user_input}")

    print("\n=== 执行过程（会出现工具调用步骤） ===\n")
    last_message = None
    for chunk in agent.stream(
        input={"messages": [{"role": "user", "content": user_input}]},
        stream_mode=STREAM_MODE_UPDATES,
        config={"run_name": "Calendar Function Calling"},
    ):
        for step, data in chunk.items():
            msg = data["messages"][-1]
            last_message = msg
            content = getattr(msg, "content_blocks", None) or getattr(msg, "content", None)
            print(f"[{step}] {type(msg).__name__}")
            if content:
                print(content)
            print()

    print("\n=== 最终回答 ===\n")
    if last_message is not None and hasattr(last_message, "content"):
        print(last_message.content)
    else:
        # 兜底：不同版本的返回结构可能略有差异
        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        print(result)


if __name__ == "__main__":
    run()

