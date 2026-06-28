# -*- coding: utf-8 -*-
"""兼容 LangGraph 的 Agent 定义。"""

from langchain.agents import create_agent

from core.config import settings
from tools import get_all_tools


def get_default_model():
    """创建默认模型；配置不完整时自动回退到 mock。"""
    from models import create_chat_model

    provider = settings.MODEL_NAME
    if not settings.validate_model_config(provider):
        provider = "mock"
    return create_chat_model(provider)


SYSTEM_PROMPT = """你是一个友好、专业的智能助手。

## 工具使用

当用户需要实时信息或外部数据时，优先调用工具。使用工具后，请清晰总结工具结果，
不要编造事实。

## 搜索回答格式（强制）

1. 仅基于检索到的权威公开信息作答，信息不明确就如实说明，绝对禁止编造
2. 关键数据须对应具体官方来源，标注发布机构与时间
3. 检索匹配度不足时，直接告知"未查询到相关公开信息"，不得引申或拼接无关内容
4. 正文仅展示整理后的结论，自然流畅，不提及检索过程
5. 禁止列出编号搜索列表、完整URL或逐条复述原始摘要
6. 禁止出现"搜索结果显示""根据搜索结果"等过程描述
7. 链接自动在搜索资源区展示，正文无需重复

遇到数据库问题时，请遵循 TextToSQL 流程：改写问题、查看表结构、
生成 SQL、校验 SQL、执行 SQL，然后用自然语言解释结果。
"""

TOOLS = get_all_tools()

agent = create_agent(
    model=get_default_model(),
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    debug=False,
)


if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "你能做什么？"}]}
    )
    print(result)
