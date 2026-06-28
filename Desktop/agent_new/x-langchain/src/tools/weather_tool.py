# -*- coding: utf-8 -*-
"""
天气工具模块

提供获取天气信息的工具函数，供各个模型文件共同使用。
"""

from typing import Any, Dict

import requests
from langchain.tools import tool
from core.config import settings


def _search_weather_by_web(city: str) -> str:
    """通过 Bing 搜索获取天气信息"""
    try:
        import requests
        import re

        query = f"{city} 今天天气 气温"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "count": 3},
            headers=headers,
            timeout=5,
        )
        resp.raise_for_status()
        html = resp.text

        results = []
        # 优先从 <h2> 内提取标题链接（避免面包屑误匹配）
        h2_blocks = re.findall(
            r'<h2[^>]*>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>\s*</h2>',
            html, re.DOTALL,
        )
        for url, raw_title in h2_blocks:
            title = re.sub(r'<[^>]+>', '', raw_title).strip()
            if not title or len(title) < 2:
                continue
            results.append({"title": title, "href": url, "body": ""})
            if len(results) >= 3:
                break

        # 补充摘要
        for i, r in enumerate(results):
            pos = html.find(r["href"])
            if pos < 0:
                continue
            nearby = html[pos:pos + 2000]
            snippet_m = re.search(
                r'<(?:p|div)[^>]*class="[^"]*(?:b_caption|b_snippet|b_lineclamp)[^"]*"[^>]*>(.*?)</(?:p|div)>',
                nearby, re.DOTALL,
            )
            if snippet_m:
                body = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()
                body = re.sub(r'\s+', ' ', body)
                results[i]["body"] = body[:300]

        if not results:
            return f"暂未获取到 {city} 的天气信息，请稍后重试"

        lines = [f"关于 **{city}天气** 的搜索结果:"]
        for r in results:
            body = r.get("body", "")
            href = r.get("href", "")
            if body:
                lines.append(f"  - {body}")
                if href:
                    lines.append(f"    来源: {href}")
        lines.append("---")
        lines.append("请基于以上天气信息，总结出清晰、准确的天气预报，包含温度、天气状况和出行建议。")
        return "\n".join(lines) if len(lines) > 1 else f"暂未获取到 {city} 的天气信息"

    except Exception as e:
        return f"天气查询失败: {str(e)}"


def _search_weather_core(city: str) -> str:
    """
    查询指定城市的天气信息的核心逻辑

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    try:
        # 验证参数
        if not city or not isinstance(city, str):
            return "错误：城市名称不能为空"

        # 集成高德地图天气 API
        api_key: str = settings.AMAP_API_KEY
        if not api_key:
            return _search_weather_by_web(city)

        # 1. 先通过地理编码 API 获取城市的 adcode
        geo_url: str = "https://restapi.amap.com/v3/geocode/geo"
        geo_params: Dict[str, str] = {"key": api_key, "address": city, "output": "json"}

        geo_response: requests.Response = requests.get(geo_url, params=geo_params)
        geo_data: Dict[str, Any] = geo_response.json()

        if geo_data.get("status") != "1" or not geo_data.get("geocodes"):
            return f"错误：无法获取 {city} 的地理位置信息"

        adcode: str = geo_data["geocodes"][0]["adcode"]

        # 2. 使用 adcode 获取天气信息
        weather_url: str = "https://restapi.amap.com/v3/weather/weatherInfo"
        weather_params: Dict[str, str] = {
            "key": api_key,
            "city": adcode,
            "extensions": "base",  # base: 基础天气信息, all: 详细天气信息
            "output": "json",
        }

        weather_response: requests.Response = requests.get(weather_url, params=weather_params)
        weather_data: Dict[str, Any] = weather_response.json()

        if weather_data.get("status") != "1" or not weather_data.get("lives"):
            return f"错误：无法获取 {city} 的天气信息"

        # 3. 处理天气数据
        live_weather: Dict[str, str] = weather_data["lives"][0]
        weather: str = live_weather["weather"]
        temperature: str = live_weather["temperature"]
        winddirection: str = live_weather["winddirection"]
        windpower: str = live_weather["windpower"]
        humidity: str = live_weather["humidity"]
        reporttime: str = live_weather["reporttime"]

        # 4. 构建返回字符串
        return f"{city}的天气：{weather}，气温 {temperature}°C，{winddirection}{windpower}级，湿度 {humidity}%，数据更新时间：{reporttime}"

    except Exception as e:
        # 捕获所有异常，确保工具不会因为错误而崩溃
        return f"获取天气信息失败: {str(e)}"


@tool
def weather_search_tool(city: str) -> str:
    """查询指定城市的天气信息

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    return _search_weather_core(city)


get_weather = weather_search_tool
