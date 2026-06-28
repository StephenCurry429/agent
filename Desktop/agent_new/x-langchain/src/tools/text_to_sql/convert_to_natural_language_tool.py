# -*- coding: utf-8 -*-
"""将 SQL 查询结果转换为易读的自然语言回答。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.config import settings
from core.logger import logger


class ConvertToNaturalLanguageArgs(BaseModel):
    question: str = Field(..., description="用户原始问题")
    results: list[dict[str, Any]] = Field(..., description="查询结果行")
    schema_description: str = Field(default="", description="可选的表结构描述")
    rewritten_info: dict[str, Any] | None = Field(
        default=None,
        description="问题改写阶段得到的可选查询线索",
    )


class ConvertToNaturalLanguageTool(BaseTool):
    name: str = "convert_to_natural_language"
    description: str = "将 SQL 查询结果转换为简洁的自然语言回答"
    args_schema: type[ConvertToNaturalLanguageArgs] = ConvertToNaturalLanguageArgs

    def _run(
        self,
        question: str,
        results: list[dict[str, Any]],
        schema_description: str = "",
        rewritten_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            logger.info("Converting SQL rows to natural language")

            if not isinstance(results, list):
                return {
                    "original_question": question,
                    "results": results,
                    "natural_language": "",
                    "error": "results 必须是字典列表",
                    "success": False,
                }

            if not results:
                return {
                    "original_question": question,
                    "results": results,
                    "natural_language": "没有查询到匹配的数据。",
                    "success": True,
                }

            from models import create_chat_model

            model = create_chat_model(settings.text_to_sql_model_name)
            preview_rows = results[:20]
            truncated = len(results) > len(preview_rows)

            system_prompt = """你是一个数据分析助手。

请只根据提供的查询结果回答用户问题。
回答要简洁、准确；如果只展示了部分结果，请明确说明。
"""
            payload = {
                "question": question,
                "schema_description": schema_description,
                "rewritten_info": rewritten_info,
                "rows": preview_rows,
                "truncated": truncated,
                "total_rows": len(results),
            }
            user_message = json.dumps(payload, ensure_ascii=False)

            response = model.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )

            natural_language = getattr(response, "content", "") or str(response)
            if truncated:
                natural_language = f"{natural_language}\n\n当前仅展示前 {len(preview_rows)} 条，共 {len(results)} 条。"

            return {
                "original_question": question,
                "results": results,
                "schema_description": schema_description,
                "natural_language": natural_language,
                "success": True,
            }
        except Exception as exc:
            logger.error(f"Natural-language conversion failed: {exc}")
            preview = results[:5] if isinstance(results, list) else []
            return {
                "original_question": question,
                "results": results,
                "schema_description": schema_description,
                "natural_language": (
                    f"无法使用大模型转换查询结果：{exc}。"
                    f"结果预览：{json.dumps(preview, ensure_ascii=False)}"
                ),
                "error": str(exc),
                "success": False,
            }
