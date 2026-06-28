from datetime import datetime, date, timedelta
from typing import List

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

WEEKDAYS: List[str] = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

HOLIDAYS: dict[str, str] = {
    "01-01": "元旦",
    "02-14": "情人节",
    "03-08": "妇女节",
    "03-12": "植树节",
    "04-01": "愚人节",
    "05-01": "劳动节",
    "05-04": "青年节",
    "06-01": "儿童节",
    "07-01": "建党节",
    "08-01": "建军节",
    "09-10": "教师节",
    "10-01": "国庆节",
    "10-31": "万圣节",
    "11-11": "双十一购物节",
    "12-24": "平安夜",
    "12-25": "圣诞节",
}


class CalendarArgs(BaseModel):
    datetime: str = Field(..., description="要查询的日期，格式为YYYY-MM-DD")


class CalendarTool(BaseTool):
    name: str = "search_calendar"
    description: str = "查询指定日期的事件或信息"
    args_schema: type[CalendarArgs] = CalendarArgs

    def _search_calendar_core(self, date_str: str) -> str:
        """查询日历信息的核心逻辑"""
        try:
            target_date: date
            if date_str.lower() in ["今天", "today"]:
                target_date = date.today()
            elif date_str.lower() in ["明天", "tomorrow"]:
                target_date = date.today() + timedelta(days=1)
            elif date_str.lower() in ["昨天", "yesterday"]:
                target_date = date.today() - timedelta(days=1)
            else:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            weekday: str = WEEKDAYS[target_date.weekday()]
            is_weekend: bool = target_date.weekday() >= 5
            today: date = date.today()
            days_diff: int = (target_date - today).days

            if days_diff > 0:
                days_info: str = f"距今还有 {days_diff} 天"
            elif days_diff < 0:
                days_info = f"已经过去 {abs(days_diff)} 天"
            else:
                days_info = "就是今天"

            month_day: str = target_date.strftime("%m-%d")
            holiday_name: str = HOLIDAYS.get(month_day, "")

            result_parts: List[str] = [
                f"📅 日期：{target_date.strftime('%Y年%m月%d日')}",
                f"📆 星期：{weekday}",
                f"📍 状态：{'周末' if is_weekend else '工作日'}",
                f"⏰ {days_info}",
            ]

            if holiday_name:
                result_parts.append(f"🎉 节日：{holiday_name}")

            return "\n".join(result_parts)

        except ValueError as e:
            return f"日期格式错误，请使用 YYYY-MM-DD 格式，例如：2024-01-01。错误信息：{str(e)}"
        except Exception as e:
            return f"查询日期信息失败：{str(e)}"

    def _run(self, datetime: str) -> str:
        """执行查询日历事件的操作"""
        return self._search_calendar_core(datetime)


if __name__ == "__main__":
    tool: CalendarTool = CalendarTool()
    print(tool._run("2024-01-01"))
    print("\n" + "=" * 50 + "\n")
    print(tool._run("今天"))
    print("\n" + "=" * 50 + "\n")
    print(tool._run("明天"))
