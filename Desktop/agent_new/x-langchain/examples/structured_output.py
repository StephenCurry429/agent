"""
结构化输出综合示例

本文件融合了两个示例的精华，演示两种常见的「格式化输出」方式：

1. 仅通过提示词约束模型输出 JSON，然后用 `json + Pydantic` 手动解析（天气示例）
2. 使用 `JsonOutputParser + PromptTemplate` 构建标准化链，自动完成 JSON 解析（笑话示例）

这两种方式可以帮助你把 LLM 的自然语言输出，稳定地转成结构化数据（字典 / Pydantic 模型）。
"""

from __future__ import annotations

import json
import os
import sys

# 确保能从项目根目录导入 config 等模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings




class WeatherInfo(BaseModel):
    """天气信息结构化输出（手动 JSON 解析示例）"""

    city: str = Field(description="城市名称")
    weather: str = Field(description="天气状况，如晴、阴、雨等")
    temperature: int = Field(description="气温，单位：摄氏度")
    humidity: Optional[int] = Field(default=None, description="湿度，单位：百分比")
    wind_direction: Optional[str] = Field(default=None, description="风向")
    wind_power: Optional[str] = Field(default=None, description="风力等级")


class Joke(BaseModel):
    """笑话（搞笑段子）的结构化输出示例"""

    setup: str = Field(description="笑话的开头部分")
    punchline: str = Field(description="笑话的包袱 / 笑点")
    rating: Optional[int] = Field(
        default=None,
        description="笑话的有趣程度评分，范围 1 到 10",
    )


def run_weather_json_demo(llm: ChatOpenAI) -> None:
    """示例 1：仅用提示词 + 手动 JSON 解析的结构化输出。"""

    prompt = """请以 JSON 格式输出天气信息，包含以下字段：
- city: 城市名称
- weather: 天气状况，如晴、阴、雨等
- temperature: 气温，单位：摄氏度
- humidity: 湿度，单位：百分比（可选）
- wind_direction: 风向（可选）
- wind_power: 风力等级（可选）

请确保输出是【有效的 JSON】，不要包含解释性文字或代码块标记。"""

    city = "北京"
    user_input = f"{prompt}\n\n用户问题：{city}的天气怎么样？"

    print("===== 示例 1：提示词约束 + 手动 JSON 解析 =====")
    print(f"用户输入: {city}的天气怎么样？\n")
    print("正在调用模型...\n")

    result = llm.invoke(user_input)
    response_text = result.content

    try:
        # 尝试从响应中提取 JSON
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start == -1 or json_end <= json_start:
            raise ValueError("未找到有效的 JSON 片段")

        json_str = response_text[json_start:json_end]
        data = json.loads(json_str)

        weather_info = WeatherInfo(**data)

        print("结构化输出结果（Pydantic 模型）：")
        print(f"- 城市: {weather_info.city}")
        print(f"- 天气: {weather_info.weather}")
        print(f"- 气温: {weather_info.temperature}°C")
        if weather_info.humidity is not None:
            print(f"- 湿度: {weather_info.humidity}%")
        if weather_info.wind_direction:
            print(f"- 风向: {weather_info.wind_direction}")
        if weather_info.wind_power:
            print(f"- 风力: {weather_info.wind_power}")

        print("\n字典格式：")
        print(weather_info.model_dump())
        print()
    except Exception as exc:  # 包含 JSONDecodeError 等
        print("无法解析为有效 JSON，原始响应如下：")
        print(response_text)
        print(f"\n解析错误：{exc}")


def run_joke_json_demo(llm: ChatOpenAI, topic: str = "猫") -> None:
    """运行 JsonOutputParser 版本的结构化输出示例。"""
    parser = JsonOutputParser(pydantic_object=Joke)

    prompt_template = PromptTemplate(
        template=(
            "你是一个中文幽默笑话生成器。\n"
            "围绕下面的主题生成一个简短有趣的笑话。\n"
            "严格按照 JSON 格式输出，字段说明如下：\n"
            "{format_instructions}\n\n"
            "主题：{topic}"
        ),
        input_variables=["topic"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # prompt -> llm -> JSON 文本 -> 解析为结构化对象（dict）
    chain = prompt_template | llm | parser

    print("===== 示例 2：JsonOutputParser + PromptTemplate 链式结构化输出 =====")
    print(f"主题: {topic}\n")

    resp = chain.invoke({"topic": topic})

    # 当前 parser 返回的是 dict，这里统一按 dict 处理并格式化打印
    print("结构化字典：")
    print(resp)

    json_str = json.dumps(resp, ensure_ascii=False, indent=2)
    print("\n格式化 JSON：")
    print(json_str)
    print()


if __name__ == "__main__":
    # 统一初始化一次 LLM，供两个示例复用
    llm = ChatOpenAI(
        model=settings.DEEPSEEK_MODEL_NAME,
        temperature=settings.TEMPERATURE,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE,
    )

    # 依次运行两个结构化输出示例
    run_weather_json_demo(llm)
    run_joke_json_demo(llm)
