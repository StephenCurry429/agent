# -*- coding: utf-8 -*-
"""
天气工具模块测试

测试天气工具模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase, mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.weather_tool import _search_weather_core, weather_search_tool


class TestWeatherTool(TestCase):
    """
    测试天气工具模块
    """

    def test_search_weather_valid_city(self):
        """
        测试使用有效城市名称调用天气查询函数
        """
        city = "北京"
        # Mock API 响应
        with mock.patch("tools.weather_tool.requests.get") as mock_get:
            # 模拟地理编码响应
            mock_geo_response = mock.Mock()
            mock_geo_response.json.return_value = {
                "status": "1",
                "geocodes": [{"adcode": "110000"}],
            }
            # 模拟天气响应
            mock_weather_response = mock.Mock()
            mock_weather_response.json.return_value = {
                "status": "1",
                "lives": [
                    {
                        "weather": "晴",
                        "temperature": "25",
                        "winddirection": "北",
                        "windpower": "3",
                        "humidity": "45",
                        "reporttime": "2024-01-01 12:00:00",
                    }
                ],
            }
            mock_get.side_effect = [mock_geo_response, mock_weather_response]

            with mock.patch("tools.weather_tool.settings") as mock_settings:
                mock_settings.AMAP_API_KEY = "test_key"
                result = _search_weather_core(city)

        self.assertIsInstance(result, str)
        self.assertIn(city, result)
        self.assertIn("天气", result)

    def test_search_weather_empty_city(self):
        """
        测试使用空城市名称调用天气查询函数
        """
        city = ""
        result = _search_weather_core(city)
        self.assertIsInstance(result, str)
        self.assertIn("错误", result)
        self.assertIn("城市名称不能为空", result)

    def test_search_weather_none_city(self):
        """
        测试使用 None 城市名称调用天气查询函数
        """
        city = None
        result = _search_weather_core(city)
        self.assertIsInstance(result, str)
        self.assertIn("错误", result)
        self.assertIn("城市名称不能为空", result)

    def test_search_weather_invalid_type(self):
        """
        测试使用无效类型调用天气查询函数
        """
        city = 123  # 使用整数而不是字符串
        result = _search_weather_core(city)
        self.assertIsInstance(result, str)
        self.assertIn("错误", result)
        self.assertIn("城市名称不能为空", result)

    def test_search_weather_no_api_key(self):
        """
        测试没有 API Key 的情况
        """
        city = "北京"
        with mock.patch("tools.weather_tool.settings") as mock_settings:
            mock_settings.AMAP_API_KEY = None
            result = _search_weather_core(city)

        self.assertIsInstance(result, str)
        self.assertIn("错误", result)
        self.assertIn("AMAP_API_KEY", result)

    def test_search_weather_api_error(self):
        """
        测试 API 返回错误的情况
        """
        city = "北京"
        with mock.patch("tools.weather_tool.requests.get") as mock_get:
            mock_response = mock.Mock()
            mock_response.json.return_value = {"status": "0", "info": "INVALID_KEY"}
            mock_get.return_value = mock_response

            with mock.patch("tools.weather_tool.settings") as mock_settings:
                mock_settings.AMAP_API_KEY = "test_key"
                result = _search_weather_core(city)

        self.assertIsInstance(result, str)
        self.assertIn("错误", result)

    def test_weather_search_tool_exists(self):
        """
        测试装饰后的天气工具函数存在
        """
        # 验证工具函数被正确装饰
        self.assertIsNotNone(weather_search_tool)


if __name__ == "__main__":
    import unittest

    unittest.main()
