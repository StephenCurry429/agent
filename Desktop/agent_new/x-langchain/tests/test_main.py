# -*- coding: utf-8 -*-
"""
主模块测试

测试主模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


class TestMain(TestCase):
    """
    测试主模块
    """

    def test_main_import(self):
        """
        测试主模块导入
        """
        try:
            import main
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"导入 main 模块失败: {e}")

    def test_main_module_exists(self):
        """
        测试主模块存在
        """
        main_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py')
        self.assertTrue(os.path.exists(main_file))


if __name__ == '__main__':
    import unittest
    unittest.main()
