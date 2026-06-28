# -*- coding: utf-8 -*-
"""
Agent 工厂模块

用于创建和配置 LangChain Agent 实例。
"""

import os
from typing import Any, List, Literal

from core.config import settings
from models import create_chat_model
from tools import get_all_tools, get_all_tools_async

ProviderName = Literal["deepseek", "doubao", "aliyun", "tongyi", "mock"]


class AgentFactory:
    """
    Agent 工厂类，用于创建不同的 Agent 实例
    """

    @staticmethod
    def get_default_tools() -> List[Any]:
        """
        获取默认工具列表（从 ToolRegistry 动态加载）

        Returns:
            工具列表
        """
        return get_all_tools()

    @staticmethod
    async def get_default_tools_async() -> List[Any]:
        """
        异步获取默认工具列表

        Returns:
            工具列表
        """
        return await get_all_tools_async()

    @staticmethod
    def create_agent(
        model_name: ProviderName,
        tools: list[Any] | None = None,
    ) -> Any:
        """
        根据提供者名称创建对应的 Agent 实例

        Args:
            model_name: 提供者名称，支持 'deepseek', 'doubao', 'aliyun', 'tongyi', 'mock'
            tools: 工具列表（如果为 None，则使用 ToolRegistry 中的所有工具）

        Returns:
            创建的 Agent 实例
        """

        # 创建模型
        model: Any = create_chat_model(model_name)

        # 创建 Agent
        return AgentFactory._create_agent_instance(model, tools)

    @staticmethod
    def _create_agent_instance(
        model: Any,
        tools: list[Any] | None = None,
    ) -> Any:
        """
        创建 Agent 实例

        Args:
            model: 模型实例
            tools: 工具列表（如果为 None，则使用 ToolRegistry 中的所有工具）

        Returns:
            Agent 实例
        """
        from langchain.agents import create_agent

        # 使用传入的工具列表或从 ToolRegistry 获取所有工具
        tools_list: list[Any] = tools if tools is not None else AgentFactory.get_default_tools()

        # 根据配置中的结构化输出设置，决定是否使用结构化输出
        structured: bool = os.getenv("STRUCTURED", str(settings.STRUCTURED)).lower() == "true"

        # 根据是否结构化输出，设置不同的系统提示
        system_prompt: str
        base_prompt = """你是一个友好、专业的智能助手。

## 角色设定

每条回复开头先说"你好主人"，然后再回答问题。

## 输出格式（必须遵守）

1. 用 Markdown 结构回复：## 标题 / **粗体** / `代码` / - 列表 / > 引用
2. 代码必须用 ``` 代码块包裹，标注语言
3. 多条信息用列表，不要用逗号堆砌
4. 重要结论放最前面，先说结论再解释

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
        if structured:
            system_prompt = base_prompt
        else:
            system_prompt = base_prompt

        # LangChain 官方推荐：直接传入 LLM / ChatModel 实例和工具列表创建 Agent
        return create_agent(
            model=model,
            tools=tools_list,
            system_prompt=system_prompt,
            debug=False,  # 禁用详细输出
        )


# 创建全局 Agent 工厂实例
agent_factory: AgentFactory = AgentFactory()