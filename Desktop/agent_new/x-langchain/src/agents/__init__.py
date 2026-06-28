# -*- coding: utf-8 -*-
"""
Agent 管理模块

集中管理和创建不同的 Agent 实例，提高代码的模块化和可扩展性。
"""

from .agent_factory import agent_factory
from .fallback_agent import FallbackAgent

__all__ = ['agent_factory', 'FallbackAgent']
