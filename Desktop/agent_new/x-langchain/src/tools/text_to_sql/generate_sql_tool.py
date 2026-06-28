# -*- coding: utf-8 -*-
"""
生成SQL工具模块

根据用户问题和数据库结构生成SQL查询语句
"""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from core.logger import logger


class GenerateSQLArgs(BaseModel):
    """生成SQL参数"""

    question: str = Field(..., description="用户原始问题或重写后的问题")
    schema_info: dict[str, Any] = Field(
        ...,
        description="数据库结构信息，包含表名和字段信息",
    )
    rewritten_info: dict[str, Any] | None = Field(
        default=None,
        description="问题重写后提取的信息（可选）",
    )


class GenerateSQLTool(BaseTool):
    """生成SQL工具"""

    name: str = "generate_sql"
    description: str = "根据用户问题和数据库结构生成SQL查询语句"
    args_schema: type[GenerateSQLArgs] = GenerateSQLArgs

    def _run(
        self,
        question: str,
        schema_info: dict[str, Any],
        rewritten_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        生成SQL查询语句

        Args:
            question: 用户问题
            schema_info: 数据库结构信息
            rewritten_info: 问题重写后提取的信息

        Returns:
            生成的SQL语句和相关信息
        """
        try:
            logger.info(f"生成SQL: {question}")

            # 验证 schema_info
            if not schema_info:
                return {
                    "sql": "",
                    "error": "数据库结构信息为空，无法生成SQL",
                    "success": False,
                }

            from models import create_chat_model

            # 获取 LLM 实例
            model = create_chat_model("deepseek")

            # 构建数据库结构描述
            schema_description = self._build_schema_description(schema_info)

            # 构建提示词
            system_prompt = f"""你是一个专业的SQL生成专家。根据用户的自然语言问题和数据库结构，生成准确的SQL查询语句。

## 数据库结构

{schema_description}

## 生成规则

1. 只生成SELECT查询语句，不要生成INSERT、UPDATE、DELETE等修改语句
2. 使用标准的SQL语法
3. 表名和字段名必须与给定的数据库结构完全一致
4. 合理使用JOIN连接相关表
5. 使用适当的WHERE条件过滤数据
6. 如果涉及聚合，使用GROUP BY和HAVING
7. 如果用户指定了排序，使用ORDER BY
8. 如果用户指定了数量限制，使用LIMIT
9. 对于字符串匹配，使用LIKE时注意转义特殊字符
10. 不要编造不存在的表或字段

## 输出格式

请直接输出SQL语句，不要包含任何解释或markdown代码块标记。"""

            user_message = f"请根据以下问题生成SQL查询语句：\n\n{question}"

            # 如果有重写后的信息，添加到提示中
            if rewritten_info:
                extra_info = []
                if rewritten_info.get("query_intent"):
                    extra_info.append(f"查询意图: {rewritten_info['query_intent']}")
                if rewritten_info.get("entities"):
                    extra_info.append(f"可能涉及的实体: {', '.join(rewritten_info['entities'])}")
                if rewritten_info.get("conditions"):
                    extra_info.append(f"查询条件: {', '.join(rewritten_info['conditions'])}")
                if rewritten_info.get("aggregation"):
                    extra_info.append(f"聚合方式: {rewritten_info['aggregation']}")
                if rewritten_info.get("sort"):
                    extra_info.append(f"排序方式: {rewritten_info['sort']}")
                if rewritten_info.get("limit"):
                    extra_info.append(f"限制条数: {rewritten_info['limit']}")

                if extra_info:
                    user_message += "\n\n" + "\n".join(extra_info)

            # 调用 LLM
            response = model.invoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                    ]
            )

            # 提取 SQL
            sql = response.content.strip()

            # 清理可能的 markdown 代码块标记
            if sql.startswith("```"):
                lines = sql.split("\n")
                # 移除第一行的 ```sql 或 ```
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 移除最后一行的 ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                sql = "\n".join(lines).strip()

            # 基本验证
            sql = self._sanitize_sql(sql)

            logger.info(f"SQL生成成功: {sql}")
            return {
                "sql": sql,
                "question": question,
                "tables_used": self._extract_tables(sql, schema_info),
                "success": True,
            }

        except Exception as e:
            logger.error(f"SQL生成失败: {str(e)}")
            return {
                "sql": "",
                "error": str(e),
                "success": False,
            }

    def _build_schema_description(self, schema_info: dict[str, Any]) -> str:
        """
        构建数据库结构描述

        Args:
            schema_info: 数据库结构信息

        Returns:
            结构描述文本
        """
        descriptions: list[str] = []

        for table_name, table_info in schema_info.items():
            columns = table_info.get("columns", [])
            primary_keys = table_info.get("primary_keys", [])
            foreign_keys = table_info.get("foreign_keys", [])

            col_descriptions = []
            for col in columns:
                col_name = col.get("name", "")
                col_type = col.get("type", "")
                is_pk = col_name in primary_keys
                pk_marker = " [PRIMARY KEY]" if is_pk else ""
                col_descriptions.append(f"  - {col_name} ({col_type}){pk_marker}")

            table_desc = f"### 表: {table_name}\n" + "\n".join(col_descriptions)

            # 添加外键信息
            if foreign_keys:
                fk_descriptions = []
                for fk in foreign_keys:
                    fk_descriptions.append(
                        f"  - {fk.get('column')} -> {fk.get('foreign_table')}.{fk.get('foreign_column')}"
                    )
                table_desc += "\n外键关系:\n" + "\n".join(fk_descriptions)

            descriptions.append(table_desc)

        return "\n\n".join(descriptions)

    def _sanitize_sql(self, sql: str) -> str:
        """
        清理和验证SQL语句

        Args:
            sql: 原始SQL语句

        Returns:
            清理后的SQL语句
        """
        # 移除多余空白
        sql = sql.strip()

        # 清理可能的 markdown 代码块标记
        if sql.startswith("```"):
            lines = sql.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sql = "\n".join(lines).strip()

        sql = " ".join(sql.split())

        # 确保以分号结尾（可选）
        if not sql.endswith(";"):
            sql = sql + ";"

        return sql

    def _extract_tables(
        self, sql: str, schema_info: dict[str, Any]
    ) -> list[str]:
        """
        从SQL中提取使用的表名

        Args:
            sql: SQL语句
            schema_info: 数据库结构信息

        Returns:
            使用的表名列表
        """
        sql_lower = sql.lower()
        tables_used = []

        for table_name in schema_info.keys():
            if table_name.lower() in sql_lower:
                tables_used.append(table_name)

        return tables_used
