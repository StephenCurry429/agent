# -*- coding: utf-8 -*-
"""
汇率工具模块测试

测试汇率工具模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase, mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.exchange_rate_tool import _fetch_exchange_rate, exchange_rate_tool


class TestExchangeRateTool(TestCase):
    """
    测试汇率工具模块
    """

    def test_exchange_rate_tool_exists(self) -> None:
        """
        测试装饰后的汇率工具函数存在
        """
        self.assertIsNotNone(exchange_rate_tool)

    def test_fetch_exchange_rate_valid(self) -> None:
        """
        测试使用有效货币代码调用汇率查询函数
        """
        with mock.patch("tools.exchange_rate_tool.requests.get") as mock_get:
            mock_response = mock.Mock()
            mock_response.json.return_value = {
                "success": True,
                "result": 7.2,
                "date": "2024-01-01",
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = _fetch_exchange_rate("USD", "CNY")

        self.assertIsInstance(result, str)
        self.assertIn("USD", result)
        self.assertIn("CNY", result)
        self.assertIn("7.2", result)

    def test_fetch_exchange_rate_empty_codes(self) -> None:
        """
        测试空货币代码
        """
        result = _fetch_exchange_rate("", "")
        self.assertIsInstance(result, str)
        self.assertIn("错误", result)

    def test_fetch_exchange_rate_invalid_type(self) -> None:
        """
        测试无效类型作为货币代码
        """
        result = _fetch_exchange_rate(123, "CNY")  # type: ignore[arg-type]
        self.assertIsInstance(result, str)
        self.assertIn("错误", result)

    def test_fetch_exchange_rate_api_error(self) -> None:
        """
        测试接口返回失败的情况
        """
        with mock.patch("tools.exchange_rate_tool.requests.get") as mock_get:
            mock_response = mock.Mock()
            mock_response.json.return_value = {"success": False, "error": "invalid"}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = _fetch_exchange_rate("USD", "CNY")

        self.assertIsInstance(result, str)
        self.assertIn("错误", result)

    def test_fetch_exchange_rate_network_error(self) -> None:
        """
        测试网络异常情况
        """
        with mock.patch("tools.exchange_rate_tool.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = _fetch_exchange_rate("USD", "CNY")

        self.assertIsInstance(result, str)
        self.assertIn("失败", result)


if __name__ == "__main__":
    import unittest

    unittest.main()

