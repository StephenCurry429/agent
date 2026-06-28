# -*- coding: utf-8 -*-
"""
工具模块包

使用插件化系统管理所有工具：
- 所有工具在模块加载时自动注册到 ToolRegistry
- 使用 @register_tool 装饰器注册新工具
- 使用 discover_tools() 自动发现工具目录中的工具
"""

import warnings
import os
from typing import Any, List

# =============================================================================
# 导入注册表和装饰器
# =============================================================================
from .registry import ToolRegistry, register_tool, discover_tools, print_registry_info

# =============================================================================
# 系统日期时间工具（手动注册，确保 AI 能获取准确时间）
# =============================================================================
try:
    from langchain_core.tools import StructuredTool
    from .current_time_tool import get_current_datetime as _get_current_datetime

    _datetime_tool = StructuredTool.from_function(
        func=_get_current_datetime,
        name="get_current_datetime",
        description="获取当前真实的系统日期和时间。当用户询问今天几号、现在几点、今天星期几时使用此工具。",
    )
    ToolRegistry.register(
        _datetime_tool,
        name="get_current_datetime",
        category="function_calling",
        subcategory="utility",
        description="获取当前真实的系统日期和时间",
    )
except ImportError:
    pass

# =============================================================================
# RAG 检索工具（手动注册，因为 rag 模块不在 tools 目录下）
# =============================================================================
try:
    from rag.rag_tool import rag_search_tool as _rag_search_tool
    ToolRegistry.register(
        _rag_search_tool,
        name="rag_search_tool",
        category="function_calling",
        subcategory="rag",
        description="从已上传的知识库文档中语义检索相关内容",
    )
except ImportError:
    pass

# =============================================================================
# MCP 工具（从 MCP 服务器动态获取）
# =============================================================================
from .qiuchi_mcp import (
    get_all_tools as get_qiuchi_tools,
    get_all_tools_async as get_qiuchi_tools_async,
)

# MCP may be temporarily unavailable in some deployments.
# When disabled, we skip registering MCP tools to avoid startup failures/timeouts.
MCP_ENABLED: bool = os.getenv("MCP_ENABLED", "false").lower() == "true"

# =============================================================================
# 工具获取接口
# =============================================================================
def get_function_calling_tools() -> List[Any]:
    """获取所有 Function Calling 工具"""
    return ToolRegistry.get_all(category="function_calling")


def get_function_calling_tools_by_subcategory(subcategory: str) -> List[Any]:
    """获取指定子类的 Function Calling 工具

    Args:
        subcategory: 子类名称，如 "text_to_sql"

    Returns:
        工具列表
    """
    return ToolRegistry.get_all(category="function_calling", subcategory=subcategory)


def register_mcp_tools() -> int:
    """注册所有 MCP 工具（秋池 + 天气）到 ToolRegistry

    Returns:
        成功注册的工具数量
    """
    if not MCP_ENABLED:
        return 0

    count = 0

    try:
        qiuchi_tools = get_qiuchi_tools()
        for tool in qiuchi_tools:
            tool_name = getattr(tool, "name", str(tool))
            if not ToolRegistry.contains(tool_name):
                ToolRegistry.register(tool, name=tool_name, category="mcp", subcategory="qiuchi_mcp")
                count += 1
    except Exception as e:
        warnings.warn(f"获取秋池 MCP 工具失败: {e}")

    return count


async def register_mcp_tools_async() -> int:
    """异步注册所有 MCP 工具（秋池 + 天气）到 ToolRegistry

    Returns:
        成功注册的工具数量
    """
    if not MCP_ENABLED:
        return 0

    count = 0

    try:
        qiuchi_tools = await get_qiuchi_tools_async()
        for tool in qiuchi_tools:
            tool_name = getattr(tool, "name", str(tool))
            if not ToolRegistry.contains(tool_name):
                ToolRegistry.register(tool, name=tool_name, category="mcp", subcategory="qiuchi_mcp")
                count += 1
    except Exception as e:
        warnings.warn(f"获取秋池 MCP 工具失败: {e}")

    return count


def get_mcp_tools() -> List[Any]:
    """获取所有已注册的 MCP 工具（秋池 + 天气）"""
    return ToolRegistry.get_all(category="mcp")


def get_mcp_tools_by_subcategory(subcategory: str) -> List[Any]:
    """获取指定子类的 MCP 工具

    Args:
        subcategory: 子类名称，如 "weather_mcp", "qiuchi_mcp"

    Returns:
        工具列表
    """
    return ToolRegistry.get_all(category="mcp", subcategory=subcategory)


async def get_mcp_tools_async() -> List[Any]:
    """异步获取所有已注册的 MCP 工具（秋池 + 天气）"""
    return ToolRegistry.get_all(category="mcp")


def get_all_tools() -> List[Any]:
    """获取所有工具"""
    # 确保 Function Calling 工具已通过插件系统注册
    discover_function_calling_tools()
    # 确保 MCP 工具已注册
    register_mcp_tools()
    
    return [
        *get_function_calling_tools(),
        *get_mcp_tools(),
    ]


async def get_all_tools_async() -> List[Any]:
    """异步获取所有工具"""
    # 确保 Function Calling 工具已通过插件系统注册
    discover_function_calling_tools()
    #  注册所有的 MCP 工具
    await register_mcp_tools_async()
    
    fc_tools = get_function_calling_tools()
    mcp_tools = await get_mcp_tools_async()
    return fc_tools + mcp_tools


# =============================================================================
# 插件系统：自动发现工具
# =============================================================================
def discover_function_calling_tools() -> int:
    """
    自动发现并加载 Function Calling 工具

    这是插件系统的核心函数，它会：
    1. 扫描 tools 目录
    2. 识别所有 BaseTool 子类
    3. 自动推断 category 为 "function_calling"
    4. 注册到 ToolRegistry

    Returns:
        成功注册的工具数量
    """
    return discover_tools()


# =============================================================================
# 可导出
# =============================================================================
__all__ = [
    # 核心功能
    "ToolRegistry",
    "register_tool",
    "discover_tools",
    "discover_function_calling_tools",
    "print_registry_info",
    # 工具注册接口
    "register_mcp_tools",
    "register_mcp_tools_async",
    # 工具获取接口
    "get_function_calling_tools",
    "get_function_calling_tools_by_subcategory",
    "get_mcp_tools",
    "get_mcp_tools_by_subcategory",
    "get_mcp_tools_async",
    "get_all_tools",
    "get_all_tools_async",
]
