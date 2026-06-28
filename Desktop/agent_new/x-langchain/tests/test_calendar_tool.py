# -*- coding: utf-8 -*-
"""
日历工具模块测试

测试日历工具模块的功能是否正常。
"""

import os
import sys
from unittest import TestCase
from datetime import date, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.calendar_tool import CalendarTool, CalendarArgs


class TestCalendarTool(TestCase):
    """
    测试日历工具模块
    """

    def test_calendar_tool_initialization(self):
        """
        测试日历工具类初始化
        """
        tool = CalendarTool()
        self.assertEqual(tool.name, "search_calendar")
        self.assertEqual(tool.description, "查询指定日期的事件或信息")
        self.assertEqual(tool.args_schema, CalendarArgs)

    def test_search_calendar_core_with_date_string(self):
        """
        测试使用日期字符串查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("2024-01-01")
        self.assertIsInstance(result, str)
        self.assertIn("2024年01月01日", result)
        self.assertIn("星期一", result)
        self.assertIn("元旦", result)

    def test_search_calendar_core_with_today(self):
        """
        测试使用"今天"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("今天")
        self.assertIsInstance(result, str)
        self.assertIn("就是今天", result)

    def test_search_calendar_core_with_tomorrow(self):
        """
        测试使用"明天"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("明天")
        self.assertIsInstance(result, str)
        self.assertIn("距今还有 1 天", result)

    def test_search_calendar_core_with_yesterday(self):
        """
        测试使用"昨天"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("昨天")
        self.assertIsInstance(result, str)
        self.assertIn("已经过去 1 天", result)

    def test_search_calendar_core_with_english_today(self):
        """
        测试使用英文"today"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("today")
        self.assertIsInstance(result, str)
        self.assertIn("就是今天", result)

    def test_search_calendar_core_with_english_tomorrow(self):
        """
        测试使用英文"tomorrow"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("tomorrow")
        self.assertIsInstance(result, str)
        self.assertIn("距今还有 1 天", result)

    def test_search_calendar_core_with_english_yesterday(self):
        """
        测试使用英文"yesterday"查询
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("yesterday")
        self.assertIsInstance(result, str)
        self.assertIn("已经过去 1 天", result)

    def test_search_calendar_core_weekend(self):
        """
        测试周末日期
        """
        tool = CalendarTool()
        # 2024-01-06 是星期六
        result = tool._search_calendar_core("2024-01-06")
        self.assertIsInstance(result, str)
        self.assertIn("星期六", result)
        self.assertIn("周末", result)

    def test_search_calendar_core_workday(self):
        """
        测试工作日日期
        """
        tool = CalendarTool()
        # 2024-01-01 是星期一
        result = tool._search_calendar_core("2024-01-01")
        self.assertIsInstance(result, str)
        self.assertIn("星期一", result)
        self.assertIn("工作日", result)

    def test_search_calendar_core_holiday(self):
        """
        测试节假日显示
        """
        tool = CalendarTool()
        # 国庆节
        result = tool._search_calendar_core("2024-10-01")
        self.assertIsInstance(result, str)
        self.assertIn("国庆节", result)

    def test_search_calendar_core_no_holiday(self):
        """
        测试非节假日不显示节日信息
        """
        tool = CalendarTool()
        # 2024-01-02 不是节假日
        result = tool._search_calendar_core("2024-01-02")
        self.assertIsInstance(result, str)
        self.assertNotIn("节日", result)

    def test_search_calendar_core_invalid_date_format(self):
        """
        测试无效日期格式
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("invalid-date")
        self.assertIsInstance(result, str)
        self.assertIn("日期格式错误", result)

    def test_search_calendar_core_empty_string(self):
        """
        测试空字符串
        """
        tool = CalendarTool()
        result = tool._search_calendar_core("")
        self.assertIsInstance(result, str)
        self.assertIn("日期格式错误", result)

    def test_calendar_tool_run_method(self):
        """
        测试日历工具的 _run 方法
        """
        tool = CalendarTool()
        result = tool._run("2024-01-01")
        self.assertIsInstance(result, str)
        self.assertIn("2024年01月01日", result)

    def test_calendar_args_schema(self):
        """
        测试日历参数模式
        """
        args = CalendarArgs(datetime="2024-01-01")
        self.assertEqual(args.datetime, "2024-01-01")


if __name__ == '__main__':
    import unittest
    unittest.main()
