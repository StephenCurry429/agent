# -*- coding: utf-8 -*-
"""
秋池(QiuChi) MCP 工具包

此模块对接"秋池"的 MCP 服务器，基于 langchain-mcp-adapters 自动发现
MCP 服务器提供的工具并将其转换为 LangChain 工具。

使用方式：
    # 同步方式获取所有工具
    from tools.qiuchi_mcp import get_all_tools, list_tool_names
    tools = get_all_tools()
    print(list_tool_names())

    # 异步方式（推荐）
    from tools.qiuchi_mcp import get_all_tools_async
    tools = await get_all_tools_async()

    # 按名称获取工具
    from tools.qiuchi_mcp import get_tool_by_name
    tool = get_tool_by_name("some_tool")

环境变量：
    QIUCHI_MCP_BASE_URL: 秋池 MCP 服务器地址（默认: http://localhost:8000）
    QIUCHI_MCP_PATH: MCP 路径（默认: /mcp）
    QIUCHI_MCP_MODE: 连接模式 http/stdio（默认: http）

注意：需要安装 langchain-mcp-adapters
    pip install langchain-mcp-adapters
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from core.logger import logger

# MCP 服务器配置（可通过环境变量覆盖）
QIUCHI_MCP_BASE_URL = os.environ.get("QIUCHI_MCP_BASE_URL", "http://localhost:8000")
QIUCHI_MCP_PATH = os.environ.get("QIUCHI_MCP_PATH", "/mcp")
QIUCHI_MCP_MODE = os.environ.get("QIUCHI_MCP_MODE", "http")  # http 或 stdio

# 尝试导入 langchain-mcp-adapters
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    LANGCHAIN_MCP_ADAPTERS_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_MCP_ADAPTERS_AVAILABLE = False
    IMPORT_ERROR = str(e)


def _get_http_config() -> Dict[str, Any]:
    """获取 HTTP 模式的 MCP 客户端配置"""
    return {
        "transport": "http",
        "url": f"{QIUCHI_MCP_BASE_URL}{QIUCHI_MCP_PATH}",
    }


def _get_stdio_config() -> Dict[str, Any]:
    """获取 Stdio 模式的 MCP 客户端配置"""
    import sys
    from pathlib import Path

    # 获取 Python 解释器路径
    python_path = sys.executable

    # 秋池 MCP 服务器路径（用户可根据实际情况修改）
    # 假设秋池项目在同级目录或通过环境变量指定
    server_path = os.environ.get(
        "QIUCHI_MCP_SERVER_PATH",
        str(Path(__file__).parent.parent.parent.parent / "qiuchi" / "src" / "main.py")
    )

    return {
        "transport": "stdio",
        "command": python_path,
        "args": [server_path],
        "env": {
            "PYTHONPATH": str(Path(server_path).parent),
            "MCP_TRANSPORT": "stdio",
        }
    }


def _create_client_config() -> Dict[str, Any]:
    """根据配置创建 MCP 客户端配置"""
    if QIUCHI_MCP_MODE == "stdio":
        return _get_stdio_config()
    return _get_http_config()


class QiuChiMCPClient:
    """
    秋池 MCP 客户端封装类。

    提供同步和异步接口获取 MCP 工具。
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        path: Optional[str] = None,
        mode: Optional[str] = None,
        server_name: str = "qiuchi_mcp",
    ) -> None:
        """
        初始化客户端。

        Args:
            base_url: MCP 服务器地址（默认从环境变量读取）
            path: MCP 路径（默认从环境变量读取）
            mode: 连接模式 http/stdio（默认从环境变量读取）
            server_name: 服务器名称标识
        """
        self._base_url = base_url or QIUCHI_MCP_BASE_URL
        self._path = path or QIUCHI_MCP_PATH
        self._mode = mode or QIUCHI_MCP_MODE
        self._server_name = server_name
        self._cached_tools: Optional[List[Any]] = None
        self._cached_tool_names: Optional[List[str]] = None

    def _get_client_config(self) -> Dict[str, Dict[str, Any]]:
        """获取客户端配置"""
        if self._mode == "stdio":
            config = _get_stdio_config()
        else:
            config = {
                "transport": "http",
                "url": f"{self._base_url}{self._path}",
            }
        return {self._server_name: config}

    async def _fetch_tools_async(self) -> List[Any]:
        """异步获取工具"""
        if not LANGCHAIN_MCP_ADAPTERS_AVAILABLE:
            raise ImportError(
                f"langchain-mcp-adapters 不可用。请安装：pip install langchain-mcp-adapters\n"
                f"原始错误：{IMPORT_ERROR}"
            )

        config = self._get_client_config()
        client = MultiServerMCPClient(config)

        logger.info(f"连接到秋池 MCP 服务器: mode={self._mode}, server={self._server_name}")

        # 直接调用 get_tools，不使用 async with（MultiServerMCPClient 不支持上下文管理器）
        tools = await client.get_tools()

        logger.info(f"从秋池 MCP 服务器获取了 {len(tools)} 个工具")
        return tools

    def get_all_tools(self) -> List[Any]:
        """
        获取所有 MCP 工具（同步方式）。

        Returns:
            LangChain 工具列表
        """
        if self._cached_tools is not None:
            return self._cached_tools

        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self._cached_tools = loop.run_until_complete(self._fetch_tools_async())
        return self._cached_tools

    async def get_all_tools_async(self) -> List[Any]:
        """
        获取所有 MCP 工具（异步方式，推荐）。

        Returns:
            LangChain 工具列表
        """
        if self._cached_tools is not None:
            return self._cached_tools

        self._cached_tools = await self._fetch_tools_async()
        return self._cached_tools

    def list_tool_names(self) -> List[str]:
        """
        列出所有工具名称。

        Returns:
            工具名称列表
        """
        if self._cached_tool_names is not None:
            return self._cached_tool_names

        tools = self.get_all_tools()
        self._cached_tool_names = [t.name for t in tools if hasattr(t, 'name')]
        return self._cached_tool_names

    async def list_tool_names_async(self) -> List[str]:
        """
        异步列出所有工具名称。

        Returns:
            工具名称列表
        """
        if self._cached_tool_names is not None:
            return self._cached_tool_names

        tools = await self.get_all_tools_async()
        self._cached_tool_names = [t.name for t in tools if hasattr(t, 'name')]
        return self._cached_tool_names

    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """
        按名称获取工具。

        Args:
            name: 工具名称

        Returns:
            找到的工具，未找到返回 None
        """
        tools = self.get_all_tools()
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == name:
                return tool
        return None

    async def get_tool_by_name_async(self, name: str) -> Optional[Any]:
        """
        异步按名称获取工具。

        Args:
            name: 工具名称

        Returns:
            找到的工具，未找到返回 None
        """
        tools = await self.get_all_tools_async()
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == name:
                return tool
        return None

    def clear_cache(self) -> None:
        """清除缓存的工具"""
        self._cached_tools = None
        self._cached_tool_names = None


# 默认客户端实例
_default_client: Optional[QiuChiMCPClient] = None


def _get_default_client() -> QiuChiMCPClient:
    """获取默认客户端实例"""
    global _default_client
    if _default_client is None:
        _default_client = QiuChiMCPClient()
    return _default_client


# 便捷函数
def get_all_tools() -> List[Any]:
    """获取秋池 MCP 所有工具（同步）"""
    return _get_default_client().get_all_tools()


async def get_all_tools_async() -> List[Any]:
    """获取秋池 MCP 所有工具（异步，推荐）"""
    return await _get_default_client().get_all_tools_async()


def list_tool_names() -> List[str]:
    """列出秋池 MCP 所有工具名称"""
    return _get_default_client().list_tool_names()


async def list_tool_names_async() -> List[str]:
    """异步列出秋池 MCP 所有工具名称"""
    return await _get_default_client().list_tool_names_async()


def get_tool_by_name(name: str) -> Optional[Any]:
    """按名称获取秋池 MCP 工具"""
    return _get_default_client().get_tool_by_name(name)


async def get_tool_by_name_async(name: str) -> Optional[Any]:
    """异步按名称获取秋池 MCP 工具"""
    return await _get_default_client().get_tool_by_name_async(name)


def clear_cache() -> None:
    """清除工具缓存"""
    _get_default_client().clear_cache()


__all__ = [
    # 配置常量
    "QIUCHI_MCP_BASE_URL",
    "QIUCHI_MCP_PATH",
    "QIUCHI_MCP_MODE",
    # 客户端类
    "QiuChiMCPClient",
    # 便捷函数（同步）
    "get_all_tools",
    "list_tool_names",
    "get_tool_by_name",
    "clear_cache",
    # 便捷函数（异步）
    "get_all_tools_async",
    "list_tool_names_async",
    "get_tool_by_name_async",
]
