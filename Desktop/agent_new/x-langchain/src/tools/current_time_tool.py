# -*- coding: utf-8 -*-
"""
系统日期时间工具

直接从操作系统获取当前日期和时间，确保准确性。
"""

from datetime import datetime


def get_current_datetime() -> str:
    """获取当前系统日期和时间（精确到秒）。

    适用场景：
    - 用户询问"今天几号"、"现在几点"、"今天星期几"等
    - 任何需要获取真实当前时间的场景

    无需参数，直接返回系统真实日期时间。
    """
    now = datetime.now()
    weekday_names = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    lines = [
        f"📅 日期：{now:%Y年%m月%d日}",
        f"📆 星期：{weekday_names[now.weekday()]}",
        f"🕐 时间：{now:%H:%M:%S}",
        f"📍 {now:%Y-%m-%d} (ISO 格式)",
    ]

    if now.weekday() >= 5:
        lines.append("💤 状态：周末")
    else:
        lines.append("💼 状态：工作日")

    return "\n".join(lines)


get_date = get_current_datetime
