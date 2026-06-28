# -*- coding: utf-8 -*-
"""
网络搜索工具模块测试

测试网络搜索工具模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase, mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.web_tool import WebSearchTool


class TestWebTool(TestCase):
    """
    测试网络搜索工具模块
    """

    def test_web_search_tool_exists(self):
        """
        测试网络搜索工具类存在
        """
        tool = WebSearchTool()
        self.assertIsNotNone(tool)

    def test_web_search_tool_with_mock_results(self):
        """
        测试网络搜索工具（有搜索结果）
        """
        tool = WebSearchTool()
        query = "Python"

        # Mock DDGS
        mock_result = {
            "title": "Python Programming",
            "href": "https://python.org",
            "body": "Python is a programming language"
        }

        with mock.patch('ddgs.DDGS') as mock_ddgs_class:
            mock_ddgs = mock.Mock()
            mock_ddgs.__enter__ = mock.Mock(return_value=mock_ddgs)
            mock_ddgs.__exit__ = mock.Mock(return_value=False)
            mock_ddgs.text.return_value = [mock_result]
            mock_ddgs_class.return_value = mock_ddgs

            result = tool._run(query)

        self.assertIsInstance(result, str)
        self.assertIn(query, result)
        self.assertIn("Python Programming", result)

    def test_web_search_tool_no_results(self):
        """
        测试网络搜索工具（无搜索结果）
        """
        tool = WebSearchTool()
        query = "xyzabc123nonexistent"

        with mock.patch('ddgs.DDGS') as mock_ddgs_class:
            mock_ddgs = mock.Mock()
            mock_ddgs.__enter__ = mock.Mock(return_value=mock_ddgs)
            mock_ddgs.__exit__ = mock.Mock(return_value=False)
            mock_ddgs.text.return_value = []
            mock_ddgs_class.return_value = mock_ddgs

            result = tool._run(query)

        self.assertIsInstance(result, str)
        self.assertIn("未找到", result)

    def test_web_search_tool_error(self):
        """
        测试网络搜索工具（错误情况）
        """
        tool = WebSearchTool()
        query = "test"

        with mock.patch('ddgs.DDGS') as mock_ddgs_class:
            mock_ddgs = mock.Mock()
            mock_ddgs.__enter__ = mock.Mock(return_value=mock_ddgs)
            mock_ddgs.__exit__ = mock.Mock(return_value=False)
            mock_ddgs.text.side_effect = Exception("Network error")
            mock_ddgs_class.return_value = mock_ddgs

            result = tool._run(query)

        self.assertIsInstance(result, str)
        self.assertIn("错误", result)


if __name__ == '__main__':
    import unittest
    unittest.main()
