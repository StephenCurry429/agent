# -*- coding: utf-8 -*-
"""
获取数据库结构工具

获取数据库的表结构信息，包括表名、字段、主键、外键等。
"""

from typing import Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from core.logger import logger


class GetSchemaArgs(BaseModel):
    """
    获取数据库结构参数
    """

    # 暂时不需要参数


class GetSchemaTool(BaseTool):
    """
    获取数据库结构工具
    """

    name: str = "get_schema"
    description: str = "获取数据库的表结构信息，包括表名、字段、主键、外键等"
    args_schema: type[GetSchemaArgs] = GetSchemaArgs

    def _run(self) -> Dict[str, Any]:
        """
        获取数据库结构

        Returns:
            数据库结构信息
        """
        try:
            logger.info("获取数据库结构")

            # 延迟导入，避免循环依赖
            from clients.db import DBOperations

            db_ops: DBOperations = DBOperations()
            schema_info: Dict[str, Any] = db_ops.get_schema_info()

            logger.info(f"成功获取数据库结构，包含 {len(schema_info)} 个表")

            return {"schema_info": schema_info, "success": True}
        except Exception as e:
            logger.error(f"获取数据库结构失败: {str(e)}")
            return {"error": str(e), "success": False}
