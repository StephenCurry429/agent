# -*- coding: utf-8 -*-
"""Agent 工厂测试。"""

import os
from unittest import TestCase, mock


class TestAgentFactory(TestCase):
    def test_agent_factory_initialization(self) -> None:
        from agents.agent_factory import AgentFactory, agent_factory

        self.assertIsInstance(agent_factory, AgentFactory)

    def test_get_default_tools(self) -> None:
        from agents.agent_factory import AgentFactory

        self.assertIsInstance(AgentFactory.get_default_tools(), list)

    def test_create_agent_mock(self) -> None:
        from agents.agent_factory import AgentFactory

        with mock.patch("langchain.agents.create_agent") as mock_create_agent:
            mock_agent = mock.Mock()
            mock_create_agent.return_value = mock_agent

            with mock.patch("agents.agent_factory.create_chat_model") as mock_create_model:
                mock_create_model.return_value = "mock_model"
                agent = AgentFactory.create_agent("mock")

        mock_create_agent.assert_called_once()
        self.assertEqual(agent, mock_agent)

    def test_create_agent_with_custom_tools(self) -> None:
        from agents.agent_factory import AgentFactory

        custom_tools = [mock.Mock()]
        with mock.patch("langchain.agents.create_agent") as mock_create_agent:
            mock_agent = mock.Mock()
            mock_create_agent.return_value = mock_agent

            with mock.patch("agents.agent_factory.create_chat_model") as mock_create_model:
                mock_create_model.return_value = "mock_model"
                agent = AgentFactory.create_agent("mock", tools=custom_tools)

        self.assertEqual(agent, mock_agent)
        self.assertEqual(mock_create_agent.call_args.kwargs["tools"], custom_tools)

    def test_create_agent_unsupported_model(self) -> None:
        from agents.agent_factory import AgentFactory

        with self.assertRaises(ValueError):
            AgentFactory.create_agent("unsupported_model")  # type: ignore[arg-type]

    def test_create_agent_instance(self) -> None:
        from agents.agent_factory import AgentFactory

        with mock.patch("langchain.agents.create_agent") as mock_create_agent:
            mock_agent = mock.Mock()
            mock_create_agent.return_value = mock_agent
            agent = AgentFactory._create_agent_instance(model="mock_model", tools=[])

        self.assertEqual(agent, mock_agent)
        mock_create_agent.assert_called_once()

    def test_system_prompt_content(self) -> None:
        from agents.agent_factory import AgentFactory

        with mock.patch("langchain.agents.create_agent") as mock_create_agent:
            mock_create_agent.return_value = mock.Mock()

            with mock.patch("agents.agent_factory.create_chat_model", return_value="mock_model"):
                with mock.patch.dict(os.environ, {"STRUCTURED": "False"}):
                    AgentFactory.create_agent("mock")
                    self.assertIn(
                        "智能助手",
                        mock_create_agent.call_args.kwargs["system_prompt"],
                    )
                    self.assertNotIn(
                        "只返回合法 JSON",
                        mock_create_agent.call_args.kwargs["system_prompt"],
                    )

                with mock.patch.dict(os.environ, {"STRUCTURED": "True"}):
                    AgentFactory.create_agent("mock")
                    self.assertIn(
                        "只返回合法 JSON",
                        mock_create_agent.call_args.kwargs["system_prompt"],
                    )
                    self.assertIn(
                        "TextToSQL",
                        mock_create_agent.call_args.kwargs["system_prompt"],
                    )
