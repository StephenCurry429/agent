# 插件开发指南

x-langchain 提供了插件化的工具系统，开发者可以轻松添加新工具，无需修改核心代码。

---

## 📚 目录

- [工具注册](#工具注册)
- [创建新工具](#创建新工具)
- [工具类别](#工具类别)
- [高级用法](#高级用法)
- [示例](#示例)

---

## 工具注册

### 方式一：使用装饰器（推荐）

使用 `@register_tool` 装饰器自动注册工具：

```python
from tools.registry import register_tool

@register_tool(
    name="my_tool",
    category="custom",
    description="我的自定义工具"
)
class MyTool:
    def __init__(self):
        self.name = "my_tool"
        self.description = "我的自定义工具"

    def run(self, param: str) -> str:
        return f"Hello, {param}!"
```

### 方式二：手动注册

使用 `ToolRegistry.register()` 手动注册工具：

```python
from tools.registry import ToolRegistry

class MyTool:
    pass

# 手动注册
ToolRegistry.register(
    MyTool(),
    name="my_tool",
    category="custom",
    description="我的自定义工具"
)
```

### 方式三：自动发现

将工具文件放入 `tools/` 目录，系统会自动发现：

```python
# tools/my_new_tool.py
from tools.registry import register_tool

@register_tool(name="my_new_tool")
def my_new_tool_function(query: str) -> str:
    """我的新工具函数"""
    return f"处理查询: {query}"
```

---

## 创建新工具

### 1. 创建工具文件

在 `tools/` 目录下创建新的 Python 文件，例如 `tools/my_calculator.py`：

```python
# -*- coding: utf-8 -*-
"""
计算器工具
"""

from tools.registry import register_tool
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


class CalculatorInput(BaseModel):
    """计算器输入参数"""
    operation: str = Field(description="运算符: add, subtract, multiply, divide")
    a: float = Field(description="第一个数字")
    b: float = Field(description="第二个数字")


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "执行基本的数学运算"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, operation: str, a: float, b: float) -> str:
        """执行计算"""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else "不能除以零",
        }

        if operation not in operations:
            return f"不支持的运算符: {operation}"

        result = operations[operation](a, b)
        return f"{a} {operation} {b} = {result}"

# 使用装饰器注册
register_tool(name="calculator", category="math", description="数学计算工具")(CalculatorTool)
```

### 2. 工具自动加载

工具会在模块导入时自动注册到 `ToolRegistry`，无需手动修改其他文件。

---

## 工具类别

工具按类别组织，便于管理和过滤：

### 内置类别

- `function_calling`: Function Calling 工具
- `mcp`: MCP 工具
- `text_to_sql`: TextToSQL 工具

### 自定义类别

你可以创建自己的类别：

```python
@register_tool(
    name="my_tool",
    category="my_custom_category",  # 自定义类别
    description="我的工具"
)
class MyTool:
    pass
```

### 按类别获取工具

```python
from tools import ToolRegistry

# 获取所有数学工具
math_tools = ToolRegistry.get_all(category="math")

# 获取所有自定义工具
custom_tools = ToolRegistry.get_all(category="my_custom_category")
```

---

## 高级用法

### 查询注册表

```python
from tools import ToolRegistry

# 检查工具是否存在
if ToolRegistry.contains("calculator"):
    print("计算器工具已注册")

# 获取工具
calc_tool = ToolRegistry.get("calculator")

# 获取工具元数据
metadata = ToolRegistry.get_metadata("calculator")
print(f"工具描述: {metadata['description']}")
print(f"工具类别: {metadata['category']}")

# 获取统计信息
stats = ToolRegistry.get_stats()
print(f"总工具数: {stats['total_tools']}")
print(f"类别数: {stats['categories']}")
```

### 动态管理工具

```python
from tools import ToolRegistry

# 移除工具
ToolRegistry.remove("calculator")

# 清空所有工具
ToolRegistry.clear()

# 重新发现工具
from tools import discover_tools
count = discover_tools()
print(f"发现了 {count} 个新工具")
```

### 调试注册表

```python
from tools import print_registry_info

# 打印所有已注册工具
print_registry_info()
```

---

## 示例

### 示例 1：天气查询工具

```python
# tools/weather_tool.py
from tools.registry import register_tool

@register_tool(name="weather_search", category="weather", description="查询天气信息")
def weather_search_tool(city: str) -> str:
    """
    查询指定城市的天气信息

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    # 这里调用实际的天气 API
    return f"{city} 今天晴天，温度 25°C"
```

### 示例 2：翻译工具

```python
# tools/translation_tool.py
from tools.registry import register_tool

@register_tool(name="translate", category="language", description="翻译文本")
class TranslationTool:
    def __init__(self):
        self.name = "translate"
        self.description = "将文本从一种语言翻译到另一种语言"

    def run(self, text: str, from_lang: str, to_lang: str) -> str:
        """
        执行翻译

        Args:
            text: 要翻译的文本
            from_lang: 源语言
            to_lang: 目标语言

        Returns:
            翻译后的文本
        """
        # 这里调用实际的翻译 API
        return f"[{to_lang}] {text}"
```

### 示例 3：文件操作工具

```python
# tools/file_tool.py
from tools.registry import register_tool
import os

@register_tool(name="file_reader", category="filesystem", description="读取文件内容")
class FileReaderTool:
    def __init__(self):
        self.name = "file_reader"
        self.description = "读取指定文件的内容"

    def run(self, file_path: str) -> str:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            文件内容
        """
        if not os.path.exists(file_path):
            return f"文件不存在: {file_path}"

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

---

## 最佳实践

### 1. 命名规范

- 工具名称使用小写字母和下划线
- 类名使用驼峰命名法
- 文件名使用小写字母和下划线

### 2. 错误处理

```python
@register_tool(name="my_tool")
class MyTool:
    def run(self, param: str) -> str:
        try:
            # 处理逻辑
            result = self._process(param)
            return result
        except Exception as e:
            return f"工具执行失败: {e}"
```

### 3. 参数验证

```python
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="参数描述")

@register_tool(name="my_tool")
class MyTool:
    def run(self, param: str) -> str:
        # 验证参数
        if not param:
            return "参数不能为空"

        # 处理逻辑
        return f"处理: {param}"
```

### 4. 文档字符串

为工具添加详细的文档字符串：

```python
@register_tool(name="my_tool", description="我的工具描述")
def my_tool(param: str) -> str:
    """
    工具的详细描述

    这个工具可以做什么，如何使用，注意事项等。

    Args:
        param: 参数说明

    Returns:
        返回值说明

    Raises:
        ValueError: 当参数无效时抛出

    Examples:
        >>> my_tool("hello")
        "Hello, hello!"
    """
    return f"Hello, {param}!"
```

---

## 故障排查

### 问题：工具没有自动注册

**原因**：工具文件没有正确导入或装饰器使用错误

**解决**：
1. 确保工具文件在 `tools/` 目录下
2. 检查 `@register_tool` 装饰器使用是否正确
3. 使用 `print_registry_info()` 查看已注册工具

### 问题：工具找不到

**原因**：工具名称不匹配

**解决**：
```python
# 检查工具是否存在
from tools import ToolRegistry
print(ToolRegistry.contains("my_tool"))  # True or False
print(ToolRegistry.get_names())  # 打印所有工具名称
```

### 问题：导入工具时出错

**原因**：依赖缺失或代码错误

**解决**：
1. 检查错误日志
2. 确保所有依赖已安装
3. 检查工具代码是否有语法错误

---

## 相关文档

- [工具 API 参考](./工具_API_参考.md)
- [LangChain 工具文档](https://python.langchain.com/docs/modules/tools)
- [项目主文档](../README.md)
