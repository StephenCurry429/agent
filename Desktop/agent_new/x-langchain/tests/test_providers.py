# -*- coding: utf-8 -*-
"""LLM Provider 模块测试。"""

import os
import sys
from unittest import TestCase, mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.providers import (
    AliyunProvider,
    DeepSeekProvider,
    DoubaoProvider,
    LLMConfig,
    LocalMockChatModel,
    MockProvider,
    create_chat_model,
    get_llm_provider,
    list_providers,
)


class TestModelProviders(TestCase):
    def test_list_providers(self) -> None:
        self.assertIn("deepseek", list_providers())
        self.assertIn("doubao", list_providers())
        self.assertIn("tongyi", list_providers())
        self.assertIn("mock", list_providers())

    def test_get_llm_provider(self) -> None:
        self.assertIsInstance(get_llm_provider("deepseek"), DeepSeekProvider)
        self.assertIsInstance(get_llm_provider("doubao"), DoubaoProvider)
        self.assertIsInstance(get_llm_provider("tongyi"), AliyunProvider)
        self.assertIsInstance(get_llm_provider("mock"), MockProvider)

    def test_create_mock_model_is_offline(self) -> None:
        model = create_chat_model("mock")
        self.assertIsInstance(model, LocalMockChatModel)
        self.assertIs(model.bind_tools([]), model)
        response = model.invoke("hello")
        self.assertIn("Mock 响应", response.content)

    def test_create_chat_model_unsupported(self) -> None:
        with self.assertRaises(ValueError) as context:
            create_chat_model("unsupported")
        self.assertIn("LLM", str(context.exception))

    def test_create_deepseek_model(self) -> None:
        config = LLMConfig(
            api_key="test_key",
            api_base="https://test.api.com",
            model_name="test_model",
            temperature=0.5,
        )

        with mock.patch("models.providers.ChatOpenAI") as mock_chat:
            mock_model = mock.Mock()
            mock_chat.return_value = mock_model
            result = DeepSeekProvider(config).create_chat_model()

        mock_chat.assert_called_once_with(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test_model",
            temperature=0.5,
            max_tokens=None,
            timeout=60,
        )
        self.assertEqual(result, mock_model)

    def test_create_doubao_model(self) -> None:
        config = LLMConfig(
            api_key="test_key",
            api_base="https://test.api.com",
            model_name="test_model",
            temperature=0.5,
        )

        with mock.patch("models.providers.ChatOpenAI") as mock_chat:
            mock_model = mock.Mock()
            mock_chat.return_value = mock_model
            result = DoubaoProvider(config).create_chat_model()

        mock_chat.assert_called_once_with(
            api_key="test_key",
            base_url="https://test.api.com",
            model="test_model",
            temperature=0.5,
            max_tokens=None,
            timeout=60,
        )
        self.assertEqual(result, mock_model)

    def test_create_tongyi_model(self) -> None:
        config = LLMConfig(
            api_key="test_key",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model_name="test_model",
        )

        with mock.patch("langchain_community.chat_models.ChatTongyi") as mock_chat:
            mock_model = mock.Mock()
            mock_chat.return_value = mock_model
            result = AliyunProvider(config).create_chat_model()

        mock_chat.assert_called_once_with(
            model="test_model",
            dashscope_api_key="test_key",
        )
        self.assertEqual(result, mock_model)

    def test_create_chat_model_overrides_config(self) -> None:
        provider = DeepSeekProvider(
            LLMConfig(
                api_key="test_key",
                api_base="https://test.api.com",
                model_name="original_model",
                temperature=0.0,
            )
        )

        with mock.patch(
            "models.providers.get_llm_provider",
            return_value=provider,
        ), mock.patch.object(
            provider,
            "create_chat_model",
            return_value="mock_model",
        ) as mock_create:
            result = create_chat_model(
                "deepseek",
                model_name="override_model",
                temperature=0.3,
                timeout=10,
            )

        self.assertEqual(result, "mock_model")
        self.assertEqual(provider.config.model_name, "override_model")
        self.assertEqual(provider.config.temperature, 0.3)
        mock_create.assert_called_once_with(timeout=10)


if __name__ == "__main__":
    import unittest

    unittest.main()
