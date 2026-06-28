# -*- coding: utf-8 -*-
"""
流式传输模式常量

本模块定义了 LangChain 流式传输的模式常量。

参考文档：https://langchain-doc.cn/v1/python/langchain/streaming.html
"""

from typing import Final, List

STREAM_MODE_UPDATES: Final[str] = "updates"
STREAM_MODE_CUSTOM: Final[str] = "custom"
STREAM_MODE_MESSAGES: Final[str] = "messages"

DEFAULT_STREAM_MODES: Final[List[str]] = [STREAM_MODE_UPDATES, STREAM_MODE_CUSTOM, STREAM_MODE_MESSAGES]
