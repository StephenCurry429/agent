# -*- coding: utf-8 -*-
"""
工具注册表

提供插件化的工具管理机制，支持：
- 工具自动注册
- 工具发现和加载
- 工具类别管理
"""

import importlib
import inspect
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# 工具注册表
# =============================================================================

class ToolRegistry:
    """
    工具注册表，管理所有已注册的工具

    支持多级别类别：
    - category: 大类（如 "function_calling", "mcp"）
    - subcategory: 小类（如 "weather_mcp", "qiuchi_mcp" 等，对应文件夹名称）
    """

    # 类级别的工具存储
    _tools: Dict[str, Any] = {}
    # 多级别类别存储: {category: {subcategory: [tool_names]}}
    _tools_by_category: Dict[str, Dict[str, List[str]]] = {}
    _tool_metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        tool: Any,
        name: Optional[str] = None,
        category: str = "default",
        subcategory: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """
        注册工具到注册表

        Args:
            tool: 工具实例或类
            name: 工具名称（如果为 None，则使用工具的 __name__）
            category: 大类，如 "function_calling", "mcp"
            subcategory: 小类，如 "weather_mcp", "qiuchi_mcp" 等（对应文件夹名称）
            description: 工具描述
        """
        # 获取工具名称
        tool_name = name or getattr(tool, "__name__", str(tool))

        # 检查是否已注册
        if tool_name in cls._tools:
            warnings.warn(f"工具 '{tool_name}' 已存在，将被覆盖")

        # 注册工具
        cls._tools[tool_name] = tool

        # 注册到多级别类别
        if category not in cls._tools_by_category:
            cls._tools_by_category[category] = {}
        if subcategory not in cls._tools_by_category[category]:
            cls._tools_by_category[category][subcategory] = []
        cls._tools_by_category[category][subcategory].append(tool_name)

        # 存储元数据
        cls._tool_metadata[tool_name] = {
            "name": tool_name,
            "category": category,
            "subcategory": subcategory,
            "description": description or "",
            "instance": tool,
        }

    @classmethod
    def get(cls, name: str, default: Any = None) -> Any:
        """
        获取工具

        Args:
            name: 工具名称
            default: 默认值（如果工具不存在）

        Returns:
            工具实例
        """
        return cls._tools.get(name, default)

    @classmethod
    def get_all(
        cls,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> List[Any]:
        """
        获取所有工具

        Args:
            category: 大类（如 "function_calling", "mcp"）
            subcategory: 小类（如 "weather_mcp", "qiuchi_mcp" 等）

        Returns:
            工具列表
        """
        if category:
            if category not in cls._tools_by_category:
                return []
            if subcategory:
                tool_names = cls._tools_by_category[category].get(subcategory, [])
            else:
                # 获取该大类下的所有工具
                tool_names = []
                for sub_cat_tools in cls._tools_by_category[category].values():
                    tool_names.extend(sub_cat_tools)
            return [cls._tools[name] for name in tool_names]
        return list(cls._tools.values())

    @classmethod
    def get_names(
        cls,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> List[str]:
        """
        获取所有工具名称

        Args:
            category: 大类（如 "function_calling", "mcp"）
            subcategory: 小类（如 "weather_mcp", "qiuchi_mcp" 等）

        Returns:
            工具名称列表
        """
        if category:
            if category not in cls._tools_by_category:
                return []
            if subcategory:
                return cls._tools_by_category[category].get(subcategory, []).copy()
            # 获取该大类下的所有工具名称
            tool_names = []
            for sub_cat_tools in cls._tools_by_category[category].values():
                tool_names.extend(sub_cat_tools)
            return tool_names
        return list(cls._tools.keys())

    @classmethod
    def get_categories(cls) -> List[str]:
        """
        获取所有大类

        Returns:
            大类列表
        """
        return list(cls._tools_by_category.keys())

    @classmethod
    def get_subcategories(cls, category: str) -> List[str]:
        """
        获取指定大类下的所有小类

        Args:
            category: 大类名称

        Returns:
            小类列表
        """
        if category not in cls._tools_by_category:
            return []
        return list(cls._tools_by_category[category].keys())

    @classmethod
    def get_metadata(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具元数据

        Args:
            name: 工具名称

        Returns:
            工具元数据
        """
        return cls._tool_metadata.get(name)

    @classmethod
    def contains(cls, name: str) -> bool:
        """
        检查工具是否已注册

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in cls._tools

    @classmethod
    def clear(cls) -> None:
        """清空注册表"""
        cls._tools.clear()
        for category in cls._tools_by_category:
            cls._tools_by_category[category].clear()
        cls._tools_by_category.clear()
        cls._tool_metadata.clear()

    @classmethod
    def remove(cls, name: str) -> bool:
        """
        移除工具

        Args:
            name: 工具名称

        Returns:
            是否成功移除
        """
        if name not in cls._tools:
            return False

        # 从主存储中移除
        del cls._tools[name]

        # 从多级别类别中移除
        metadata = cls._tool_metadata.get(name, {})
        category = metadata.get("category", "default")
        subcategory = metadata.get("subcategory")
        if category in cls._tools_by_category:
            if subcategory:
                if subcategory in cls._tools_by_category[category]:
                    if name in cls._tools_by_category[category][subcategory]:
                        cls._tools_by_category[category][subcategory].remove(name)
                    # 如果小类为空，则删除该小类
                    if not cls._tools_by_category[category][subcategory]:
                        del cls._tools_by_category[category][subcategory]
            # 如果大类为空，则删除该大类
            if not cls._tools_by_category[category]:
                del cls._tools_by_category[category]

        # 移除元数据
        del cls._tool_metadata[name]

        return True

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        获取注册表统计信息

        Returns:
            统计信息字典
        """
        tools_by_category: Dict[str, Any] = {}
        for category, subcategories in cls._tools_by_category.items():
            tools_by_category[category] = {
                "total": sum(len(tools) for tools in subcategories.values()),
                "subcategories": {
                    subcat: len(tools)
                    for subcat, tools in subcategories.items()
                },
            }
        return {
            "total_tools": len(cls._tools),
            "categories": len(cls._tools_by_category),
            "tools_by_category": tools_by_category,
        }


# =============================================================================
# 工具注册装饰器
# =============================================================================

def register_tool(
    name: Optional[str] = None,
    category: str = "default",
    subcategory: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    工具注册装饰器

    使用方式：
        ```python
        @register_tool(name="my_tool", category="mcp", subcategory="my_folder", description="我的工具")
        class MyTool:
            def __init__(self):
                self.name = "my_tool"

            def run(self):
                return "Hello from my tool"
        ```

    Args:
        name: 工具名称（如果为 None，则使用类/函数的 __name__）
        category: 大类（如 "function_calling", "mcp"）
        subcategory: 小类（如 "weather_mcp", "qiuchi_mcp" 等，对应文件夹名称）
        description: 工具描述

    Returns:
        装饰器函数
    """

    def decorator(item: Any) -> Any:
        # 如果是类，则实例化后注册
        if inspect.isclass(item):
            # 延迟实例化，在首次使用时创建实例
            # 但为了兼容现有代码，我们直接实例化
            instance = item()
            ToolRegistry.register(
                instance, name=name, category=category, subcategory=subcategory, description=description
            )
            return item
        else:
            # 如果是函数或实例，直接注册
            ToolRegistry.register(
                item, name=name, category=category, subcategory=subcategory, description=description
            )
            return item

    return decorator


# =============================================================================
# 工具发现和加载
# =============================================================================

def _infer_category_from_path(module_path: Path) -> tuple[str, Optional[str]]:
    """
    从模块路径推断 category 和 subcategory

    Args:
        module_path: 模块文件或目录路径

    Returns:
        (category, subcategory) 元组
    """
    parent_name = module_path.parent.name

    # 判断大类
    if parent_name == "tools":
        # 直接在 tools 目录下的单文件工具，使用 function_calling
        return "function_calling", None
    else:
        # 在子目录下的工具，子目录名作为 subcategory
        # 根据 subcategory 名称判断大类
        subcategory = parent_name

        # MCP 工具
        if subcategory.endswith("_mcp"):
            return "mcp", subcategory
        # TextToSQL 工具
        elif subcategory == "text_to_sql":
            return "function_calling", subcategory
        # 其他工具
        else:
            return "function_calling", subcategory


def _extract_tools_from_module(module: Any, category: str, subcategory: Optional[str] = None) -> int:
    """
    从模块中提取工具并自动注册

    支持两种工具类型：
    1. 继承 BaseTool 的类
    2. 使用 @tool 装饰器的函数

    Args:
        module: 模块对象
        category: 大类
        subcategory: 小类

    Returns:
        注册的工具数量
    """
    # 延迟导入避免循环依赖
    from langchain_core.tools import BaseTool

    count = 0

    # 查找所有可调用的对象
    for name, obj in inspect.getmembers(module):
        # 跳过私有属性和特殊属性
        if name.startswith("_"):
            continue

        # 跳过已导入的模块
        if inspect.ismodule(obj):
            continue

        # 类型1：BaseTool 子类
        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj != BaseTool:
            # 检查是否已经注册过
            instance = obj()
            tool_name = getattr(instance, "name", name)
            if not ToolRegistry.contains(tool_name):
                # 自动注册工具
                ToolRegistry.register(
                    instance,
                    name=tool_name,
                    category=category,
                    subcategory=subcategory,
                    description=getattr(instance, "description", None),
                )
                count += 1

        # 类型2：使用 @tool 装饰器的函数
        elif isinstance(obj, BaseTool):
            tool_name = getattr(obj, "name", name)
            if not ToolRegistry.contains(tool_name):
                ToolRegistry.register(
                    obj,
                    name=tool_name,
                    category=category,
                    subcategory=subcategory,
                    description=getattr(obj, "description", None),
                )
                count += 1

        elif inspect.isfunction(obj) and hasattr(obj, "name"):
            # 检查是否已经注册过
            tool_name = getattr(obj, "name", name)
            if not ToolRegistry.contains(tool_name):
                # 自动注册工具
                ToolRegistry.register(
                    obj,
                    name=tool_name,
                    category=category,
                    subcategory=subcategory,
                    description=getattr(obj, "description", None),
                )
                count += 1

    return count


def discover_tools(
    tools_dir: Optional[Path] = None,
    package_name: str = "tools",
) -> int:
    """
    发现并加载工具目录中的所有工具（插件系统）

    自动扫描 tools 目录，识别所有工具类并注册到 ToolRegistry。
    工具可以是：
    - 单文件模块（如 calendar_tool.py）
    - 子包（如 weather_mcp/）

    Args:
        tools_dir: 工具目录路径（如果为 None，则使用当前目录）
        package_name: 包名称

    Returns:
        成功注册的工具数量
    """
    if tools_dir is None:
        # 获取当前文件所在目录的父目录
        current_file = Path(__file__)
        tools_dir = current_file.parent

    # 需要跳过的文件和目录
    skip_files = {"__init__.py", "__pycache__", "registry.py"}

    count = 0

    # 遍历工具目录
    for item in tools_dir.iterdir():
        # 跳过跳过的文件和目录
        if item.name in skip_files:
            continue

        # 处理 Python 文件（单文件工具模块）
        if item.is_file() and item.suffix == ".py":
            module_name = item.stem
            try:
                # 导入模块
                full_module_name = f"{package_name}.{module_name}"
                module = importlib.import_module(full_module_name)

                # 从路径推断 category 和 subcategory
                category, subcategory = _infer_category_from_path(item)

                # 提取并注册工具
                count += _extract_tools_from_module(module, category, subcategory)

            except Exception as e:
                warnings.warn(f"导入工具模块 {module_name} 失败: {e}")

        # 处理子包目录（如 text_to_sql/, weather_mcp/）
        elif item.is_dir() and (item / "__init__.py").exists():
            module_name = item.name
            try:
                # 导入子包
                full_module_name = f"{package_name}.{module_name}"
                module = importlib.import_module(full_module_name)

                # 从路径推断 category 和 subcategory
                category, subcategory = _infer_category_from_path(item)

                # 提取并注册工具
                count += _extract_tools_from_module(module, category, subcategory)

            except Exception as e:
                warnings.warn(f"导入工具包 {module_name} 失败: {e}")

    return count


def load_tools_from_module(module_name: str) -> int:
    """
    从指定模块加载工具

    Args:
        module_name: 模块名称

    Returns:
        加载的工具数量
    """
    try:
        module = importlib.import_module(module_name)

        # 查找所有可调用的对象
        count = 0
        for name, obj in inspect.getmembers(module):
            # 跳过私有属性和特殊属性
            if name.startswith("_"):
                continue

            # 查找工具（通常有 name 或 description 属性）
            if hasattr(obj, "name") or hasattr(obj, "description"):
                # 自动注册
                tool_name = getattr(obj, "name", name)
                ToolRegistry.register(
                    obj,
                    name=tool_name,
                    category=module_name.split(".")[-1],
                    description=getattr(obj, "description", None),
                )
                count += 1

        return count

    except Exception as e:
        warnings.warn(f"加载模块 {module_name} 失败: {e}")
        return 0


# =============================================================================
# 辅助函数
# =============================================================================

def print_registry_info() -> None:
    """打印注册表信息（用于调试）"""
    stats = ToolRegistry.get_stats()
    print("=" * 50)
    print("工具注册表信息")
    print("=" * 50)
    print(f"总工具数: {stats['total_tools']}")
    print(f"大类数: {stats['categories']}")
    print("\n按多级别类别分类:")
    for category, cat_info in stats['tools_by_category'].items():
        print(f"  {category} (共 {cat_info['total']} 个工具):")
        for subcategory, count in cat_info.get('subcategories', {}).items():
            sub_str = f" - {subcategory}: {count} 个工具" if subcategory else f" - (默认): {count} 个工具"
            print(f"    {sub_str}")
    print("\n所有工具:")
    for tool_name in ToolRegistry.get_names():
        metadata = ToolRegistry.get_metadata(tool_name)
        subcat_str = f" [{metadata.get('subcategory')}]" if metadata.get('subcategory') else ""
        print(f"  - {tool_name}{subcat_str}: {metadata.get('description', '无描述')}")
    print("=" * 50)


# =============================================================================
# 可导出
# =============================================================================

__all__ = [
    "ToolRegistry",
    "register_tool",
    "discover_tools",
    "load_tools_from_module",
    "print_registry_info",
]
