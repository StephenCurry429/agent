# -*- coding: utf-8 -*-
"""
日志模块测试

测试日志模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase, mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestLogger(TestCase):
    """
    测试日志模块
    """

    def test_logger_import(self):
        """
        测试日志模块导入
        """
        from core.logger import logger
        self.assertIsNotNone(logger)

    def test_logger_has_required_methods(self):
        """
        测试日志对象有必需的方法
        """
        from core.logger import logger
        required_methods = ['debug', 'info', 'warning', 'error', 'critical']
        for method in required_methods:
            self.assertTrue(hasattr(logger, method))
            self.assertTrue(callable(getattr(logger, method)))

    def test_log_directory_created(self):
        """
        测试日志目录被创建
        """
        # 日志目录应该在导入时就被创建
        self.assertTrue(os.path.exists('logs'))


if __name__ == '__main__':
    import unittest
    unittest.main()
