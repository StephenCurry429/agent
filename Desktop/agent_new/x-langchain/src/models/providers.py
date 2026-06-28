# -*- coding: utf-8 -*-
"""
LLM 提供者模块

提供统一的 LLM 接口，支持多种模型提供者：
- DeepSeek
- 豆包 (Doubao)
- 阿里云百炼 (Alibaba Cloud)
- Mock (用于测试)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from core.logger import logger


class LLMConfig(BaseModel):
    """LLM 配置模型"""

    api_key: str = Field(..., description="API 密钥")
    api_base: str = Field(..., description="API 基础地址")
    model_name: str = Field(..., description="模型名称")
    temperature: float = Field(default=0.0, description="温度参数")
    max_tokens: Optional[int] = Field(default=None, description="最大令牌数")
    timeout: int = Field(default=60, description="请求超时时间（秒）")


class BaseLLMProvider(ABC):
    """
    LLM 提供者基类

    所有 LLM 提供者都需要继承此类并实现 create_chat_model 方法。
    """

    name: str = ""
    description: str = ""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化 LLM 提供者

        Args:
            config: LLM 配置（可选，默认从 settings 读取）
        """
        self.config = config or self._get_default_config()
        self._chat_model: Optional[BaseChatModel] = None

    @abstractmethod
    def _get_default_config(self) -> LLMConfig:
        """
        获取默认配置

        Returns:
            LLMConfig 配置对象
        """
        pass

    @abstractmethod
    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """
        创建聊天模型实例

        Args:
            **kwargs: 额外的模型参数

        Returns:
            BaseChatModel 实例
        """
        pass

    @property
    def chat_model(self) -> BaseChatModel:
        """获取聊天模型（懒加载）"""
        if self._chat_model is None:
            self._chat_model = self.create_chat_model()
        return self._chat_model

    def invoke(self, messages: list, **kwargs) -> Any:
        """
        调用聊天模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            模型响应
        """
        logger.info(f"[{self.name}] 调用 LLM: {len(messages)} 条消息")
        return self.chat_model.invoke(messages, **kwargs)

    def stream(self, messages: list, **kwargs):
        """
        流式调用聊天模型

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            流式响应块
        """
        logger.info(f"[{self.name}] 流式调用 LLM: {len(messages)} 条消息")
        yield from self.chat_model.stream(messages, **kwargs)

    def bind_tools(self, tools: list, **kwargs) -> BaseChatModel:
        """
        绑定工具到聊天模型

        Args:
            tools: 工具列表
            **kwargs: 额外参数

        Returns:
            绑定工具后的聊天模型
        """
        logger.info(f"[{self.name}] 绑定 {len(tools)} 个工具")
        return self.chat_model.bind_tools(tools, **kwargs)

    def with_structured_output(self, schema: Any, **kwargs) -> Any:
        """
        配置结构化输出

        Args:
            schema: 输出模式（Pydantic 模型或 JSON Schema）
            **kwargs: 额外参数

        Returns:
            配置结构化输出的可运行对象
        """
        logger.info(f"[{self.name}] 配置结构化输出")
        return self.chat_model.with_structured_output(schema, **kwargs)


class DeepSeekProvider(BaseLLMProvider):
    """
    DeepSeek LLM 提供者

    支持的模型：
    - deepseek-chat
    - deepseek-reasoner
    """

    name = "deepseek"
    description = "DeepSeek 模型提供者"

    def _get_default_config(self) -> LLMConfig:
        """获取 DeepSeek 默认配置"""
        return LLMConfig(
            api_key=settings.DEEPSEEK_API_KEY,
            api_base=settings.DEEPSEEK_API_BASE,
            model_name=settings.DEEPSEEK_MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )

    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """创建 DeepSeek 聊天模型"""
        logger.info(f"创建 DeepSeek 聊天模型: {self.config.model_name}")

        return ChatOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            model=self.config.model_name,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            timeout=kwargs.get("timeout", self.config.timeout),
        )


class DoubaoProvider(BaseLLMProvider):
    """
    豆包 (Doubao) LLM 提供者

    支持的模型：
    - doubao-pro-32k
    - doubao-pro-128k
    - doubao-lite-32k
    """

    name = "doubao"
    description = "豆包模型提供者（字节跳动）"

    def _get_default_config(self) -> LLMConfig:
        """获取豆包默认配置"""
        return LLMConfig(
            api_key=settings.DOUBAO_API_KEY,
            api_base=settings.DOUBAO_API_BASE,
            model_name=settings.DOUBAO_MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )

    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """创建豆包聊天模型"""
        logger.info(f"创建豆包聊天模型: {self.config.model_name}")

        return ChatOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            model=self.config.model_name,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            timeout=kwargs.get("timeout", self.config.timeout),
        )


class AliyunProvider(BaseLLMProvider):
    """
    阿里云百炼 (Alibaba Cloud) LLM 提供者

    支持的模型：
    - qwen-turbo
    - qwen-plus
    - qwen-max
    - qwen-max-longcontext
    """

    name = "aliyun"
    description = "阿里云百炼模型提供者（通义千问）"

    def _get_default_config(self) -> LLMConfig:
        """获取阿里云默认配置"""
        return LLMConfig(
            api_key=settings.ALIYUN_API_KEY,
            api_base=settings.ALIYUN_API_BASE,
            model_name=settings.ALIYUN_MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )

    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """创建阿里云聊天模型"""
        logger.info(f"创建阿里云聊天模型: {self.config.model_name}")

        # 阿里云使用 langchain_community 的 ChatTongyi
        from langchain_community.chat_models import ChatTongyi

        return ChatTongyi(
            model=self.config.model_name,
            dashscope_api_key=self.config.api_key,
        )


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI 兼容接口 LLM 提供者

    支持所有 OpenAI 兼容的 API 接口，包括：
    - 原生 OpenAI
    - MIMO
    - 其他兼容 OpenAI API 的服务
    """

    name = "openai"
    description = "OpenAI 兼容接口提供者"

    def _get_default_config(self) -> LLMConfig:
        """获取 OpenAI 默认配置"""
        return LLMConfig(
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_BASE_URL,
            model_name=settings.MIMO_MODEL or "gpt-3.5-turbo",
            temperature=settings.TEMPERATURE,
        )

    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """创建 OpenAI 兼容聊天模型"""
        logger.info(f"创建 OpenAI 兼容聊天模型: {self.config.model_name}")

        return ChatOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            model=self.config.model_name,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            timeout=kwargs.get("timeout", self.config.timeout),
        )


class MIMOProvider(OpenAIProvider):
    """
    MIMO LLM 提供者

    基于 OpenAI 兼容接口的 MIMO 模型
    """

    name = "mimo"
    description = "MIMO 模型提供者"


class MockProvider(BaseLLMProvider):
    """
    模拟 LLM 提供者（用于测试）

    不调用真实的 LLM，返回模拟响应
    """

    name = "mock"
    description = "模拟模型提供者（用于测试）"

    def _get_default_config(self) -> LLMConfig:
        """获取模拟配置"""
        return LLMConfig(
            api_key="mock-api-key",
            api_base="http://localhost:8000",
            model_name="gpt-3.5-turbo",
            temperature=0.0,
        )

    def create_chat_model(self, **kwargs) -> BaseChatModel:
        """创建模拟聊天模型"""
        logger.info("创建模拟聊天模型（用于测试）")
        
        # 创建自定义模拟模型类
        from langchain_core.messages import AIMessage
        
        class MockChatModel(BaseChatModel):
            """模拟聊天模型"""
            
            @property
            def _llm_type(self) -> str:
                return "mock"
            
            def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                last_message = messages[-1] if messages else {}
                content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                
                if "天气" in content:
                    response = "抱歉，我是模拟模型，无法查询实时天气。请配置真实的 API Key。"
                elif "计算" in content or "+" in content or "-" in content or "*" in content or "/" in content:
                    response = "模拟计算结果：这是一个测试响应。如果需要真实计算，请配置真实的 API Key。"
                elif "代码" in content or "python" in content.lower() or "javascript" in content.lower():
                    response = "# 这是一段模拟代码\nprint('Hello, World!')\n\n// 模拟代码结束\n\n注意：这是模拟响应，实际代码生成需要配置真实的 API Key。"
                else:
                    response = f"模拟响应：收到您的消息 - {content[:50]}...\n\n（这是模拟模型的响应，如需真实 AI 回复，请配置真实的 API Key）"
                
                from langchain_core.outputs import ChatGeneration, ChatResult
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response))])
            
            def bind_tools(self, tools, **kwargs):
                """绑定工具（模拟实现）"""
                return self
        
        return MockChatModel()

    def invoke(self, messages: list, **kwargs) -> Any:
        """返回模拟响应"""
        from langchain_core.messages import AIMessage

        logger.info(f"[Mock] 返回模拟响应")
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "") if isinstance(last_message, dict) else str(last_message)

        # 根据消息内容返回不同的模拟响应
        if "天气" in content:
            response = "抱歉，我是模拟模型，无法查询实时天气。请配置真实的 API Key。"
        elif "计算" in content or "+" in content or "-" in content:
            response = "模拟计算结果：这是一个测试响应。"
        else:
            response = f"模拟响应：收到您的消息 - {content[:50]}..."

        return AIMessage(content=response)


# 提供者类型别名
ProviderName = str  # "deepseek" | "doubao" | "aliyun" | "mock"

# 提供者注册表
_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "deepseek": DeepSeekProvider,
    "doubao": DoubaoProvider,
    "aliyun": AliyunProvider,
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "mimo": MIMOProvider,
    # 兼容旧名称
    "tongyi": AliyunProvider,
}


def get_llm_provider(provider_name: str, config: Optional[LLMConfig] = None) -> BaseLLMProvider:
    """
    获取 LLM 提供者实例

    Args:
        provider_name: 提供者名称（deepseek, doubao, aliyun, tongyi, mock）
        config: 自定义配置（可选）

    Returns:
        BaseLLMProvider 实例

    Raises:
        ValueError: 不支持的提供者
    """
    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(f"不支持的 LLM 提供者: {provider_name}。支持的提供者: {available}")

    logger.info(f"获取 LLM 提供者: {provider_name}")
    return _PROVIDERS[provider_name](config)


def create_chat_model(
    provider_name: str = "deepseek",
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs,
) -> BaseChatModel:
    """
    创建聊天模型的便捷函数

    Args:
        provider_name: 提供者名称
        model_name: 模型名称（可选，覆盖默认配置）
        temperature: 温度参数（可选，覆盖默认配置）
        **kwargs: 其他参数

    Returns:
        BaseChatModel 实例
    """
    provider = get_llm_provider(provider_name)

    # 覆盖配置
    if model_name:
        provider.config.model_name = model_name
    if temperature is not None:
        provider.config.temperature = temperature

    return provider.create_chat_model(**kwargs)


def list_providers() -> list[str]:
    """列出所有可用的 LLM 提供者"""
    return list(_PROVIDERS.keys())