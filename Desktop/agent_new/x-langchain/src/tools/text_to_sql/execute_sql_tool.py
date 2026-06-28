# -*- coding: utf-8 -*-
"""
执行SQL工具

执行生成的SQL查询语句，返回查询结果。
"""

from typing import Dict, Any, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from core.logger import logger


class ExecuteSQLArgs(BaseModel):
    """
    执行SQL参数
    """

    sql: str = Field(..., description="要执行的SQL查询语句")


class ExecuteSQLTool(BaseTool):
    """
    执行SQL查询工具
    """

    name: str = "execute_sql"
    description: str = "执行SQL查询语句并返回结果"
    args_schema: type[ExecuteSQLArgs] = ExecuteSQLArgs

    def _run(self, sql: str) -> Dict[str, Any]:
        """
        执行SQL查询

        Args:
            sql: SQL查询语句

        Returns:
            查询结果
        """
        try:
            logger.info(f"执行SQL查询: {sql}")

            # 延迟导入，避免循环依赖
            from clients.db import DBOperations

            db_ops: DBOperations = DBOperations()
            results: List[Dict[str, Any]] = db_ops.execute_sql(sql)

            logger.info(f"SQL查询执行成功，返回 {len(results)} 条记录")

            return {"sql": sql, "results": results, "success": True}
        except Exception as e:
            logger.error(f"执行SQL失败: {str(e)}")
            return {"sql": sql, "error": str(e), "success": False}
