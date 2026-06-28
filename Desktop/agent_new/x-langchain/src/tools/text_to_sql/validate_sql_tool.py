# -*- coding: utf-8 -*-
"""
验证SQL工具

验证生成的SQL语句是否符合语法规则。
"""

from typing import Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from core.logger import logger


class ValidateSQLArgs(BaseModel):
    """
    验证SQL参数
    """

    sql: str = Field(..., description="要验证的SQL查询语句")


class ValidateSQLTool(BaseTool):
    """
    验证SQL语法工具
    """

    name: str = "validate_sql"
    description: str = "验证SQL语句的语法是否正确"
    args_schema: type[ValidateSQLArgs] = ValidateSQLArgs

    def _run(self, sql: str) -> Dict[str, Any]:
        """
        验证SQL语法

        Args:
            sql: SQL查询语句

        Returns:
            验证结果
        """
        try:
            logger.info(f"验证SQL语法: {sql}")

            # 延迟导入，避免循环依赖
            from clients.db import DBOperations

            db_ops: DBOperations = DBOperations()
            is_valid: bool = db_ops.validate_sql(sql)

            if is_valid:
                logger.info("SQL语法验证通过")
                return {"sql": sql, "is_valid": True, "message": "SQL语法验证通过"}
            else:
                logger.warning("SQL语法验证失败")
                return {"sql": sql, "is_valid": False, "message": "SQL语法验证失败"}
        except Exception as e:
            logger.error(f"验证SQL失败: {str(e)}")
            return {"sql": sql, "is_valid": False, "message": f"验证失败: {str(e)}"}
