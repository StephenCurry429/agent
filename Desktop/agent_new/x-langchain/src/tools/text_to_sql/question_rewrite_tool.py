# -*- coding: utf-8 -*-
"""为 TextToSQL 改写自然语言问题。"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.config import settings
from core.logger import logger


class QuestionRewriteArgs(BaseModel):
    question: str = Field(..., description="用户原始问题")
    context: str = Field(default="", description="可选的对话上下文")


class QuestionRewriteTool(BaseTool):
    name: str = "question_rewrite"
    description: str = "改写用户问题，并提取 TextToSQL 查询线索"
    args_schema: type[QuestionRewriteArgs] = QuestionRewriteArgs

    def _run(self, question: str, context: str = "") -> dict[str, Any]:
        try:
            logger.info(f"Rewriting question: {question}")

            from models import create_chat_model

            model = create_chat_model(settings.text_to_sql_model_name)
            system_prompt = """你负责为 TextToSQL 流程整理用户问题。

请只返回合法 JSON，字段如下：
{
  "rewritten_question": "在保留用户原意基础上改写后的清晰问题",
  "query_intent": "查询意图，如明细查询、聚合统计、排序、过滤、分组等",
  "entities": ["可能涉及的数据表或业务实体"],
  "conditions": ["过滤条件或时间范围"],
  "aggregation": "count/sum/avg/min/max/null",
  "sort": "排序规则或 null",
  "limit": "返回数量或 null"
}

不要编造用户问题或上下文中没有出现的信息。
"""
            user_message = f"用户问题：{question}"
            if context:
                user_message += f"\n\n上下文：{context}"

            response = model.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ]
            )

            parsed = self._parse_json(getattr(response, "content", ""))
            return {
                "original_question": question,
                "rewritten_question": parsed.get("rewritten_question", question),
                "query_intent": parsed.get("query_intent", "明细查询"),
                "entities": parsed.get("entities", []),
                "conditions": parsed.get("conditions", []),
                "aggregation": parsed.get("aggregation"),
                "sort": parsed.get("sort"),
                "limit": parsed.get("limit"),
                "success": True,
            }
        except Exception as exc:
            logger.error(f"Question rewrite failed: {exc}")
            return {
                "original_question": question,
                "rewritten_question": question,
                "error": str(exc),
                "success": False,
            }

    def _parse_json(self, content: str) -> dict[str, Any]:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(content[start:end])
        return {}
