# -*- coding: utf-8 -*-
"""Smoke tests for importable runtime entry points."""


def test_agent_factory_can_create_mock_agent() -> None:
    from agents import agent_factory

    agent = agent_factory.create_agent("mock", tools=[])
    assert agent is not None


def test_langgraph_agent_module_imports() -> None:
    import agents.agent as agent_module

    assert agent_module.agent is not None


def test_default_tools_include_expected_tools() -> None:
    from tools import ToolRegistry, get_all_tools

    ToolRegistry.clear()
    tool_names = {getattr(tool, "name", str(tool)) for tool in get_all_tools()}
    assert "weather_search_tool" in tool_names
    assert "exchange_rate_tool" in tool_names
    assert "web_search" in tool_names
