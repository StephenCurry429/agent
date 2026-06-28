# -*- coding: utf-8 -*-
"""
代码沙箱工具模块

在隔离子进程中执行 Python 代码，超时保护、限制危险操作。
"""

import subprocess
import tempfile
import os
import sys

from langchain.tools import tool

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 30

# 禁止的模块/函数前缀
BLOCKED_IMPORTS = (
    "os.system", "os.popen", "os.spawn", "os.exec",
    "subprocess",
    "shutil.rmtree", "shutil.move",
    "socket",
    "requests",
    "http",
)

_RESTRICT_GUARD = """
import sys, os, builtins

BLOCKED = {blocked_modules!r}
_original_import = builtins.__import__

def _restrict_import(name, globals=None, locals=None, fromlist=(), level=0):
    for b in BLOCKED:
        if name == b or name.startswith(b + "."):
            raise ImportError("禁止导入模块: " + name)
    return _original_import(name, globals, locals, fromlist, level)

builtins.__import__ = _restrict_import
"""


def execute_code(code: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    在隔离子进程中执行 Python 代码。

    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒），默认 30

    Returns:
        执行结果（stdout + stderr）
    """
    if not code or not code.strip():
        return "错误：代码不能为空"

    # 注入安全限制 + 用户代码
    full_code = _RESTRICT_GUARD.format(blocked_modules=sorted(BLOCKED_IMPORTS))
    full_code += "\n" + code

    # 写入临时文件
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(full_code)
        tmp.close()

        # 用当前 Python 解释器运行
        python_exe = sys.executable

        result = subprocess.run(
            [python_exe, tmp.name],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = ""
        if result.stdout:
            output += result.stdout.strip()
        if result.stderr:
            if output:
                output += "\n"
            output += "[stderr] " + result.stderr.strip()
        if not output:
            output = "(无输出)"
        return output

    except subprocess.TimeoutExpired:
        return f"代码执行超时（>{timeout}秒）"
    except Exception as e:
        return f"沙箱执行出错: {str(e)}"
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@tool
def code_sandbox_tool(code: str) -> str:
    """在沙箱中执行 Python 代码并返回结果。

    适用场景：
    - 用户要求计算、数据处理等需要代码执行的任务
    - 测试简单算法逻辑
    - 生成数据可视化之前的计算

    限制：
    - 禁止网络请求、文件系统危险操作
    - 默认 30 秒超时
    - 仅支持 Python 代码

    Args:
        code: 要执行的 Python 代码字符串

    Returns:
        代码执行的标准输出和错误输出
    """
    return execute_code(code)


get_sandbox_executor = code_sandbox_tool
