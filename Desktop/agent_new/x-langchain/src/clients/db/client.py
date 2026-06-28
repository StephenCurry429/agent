"""TextToSQL 工具使用的数据库辅助能力。"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import Engine, MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings
from core.logger import logger

_MUTATING_SQL_RE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|replace|merge|grant|revoke)\b",
    re.IGNORECASE,
)
_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)


def get_db_url() -> str:
    """返回当前配置的 SQLAlchemy 数据库连接地址。"""
    return settings.get_db_url()


def is_safe_select_sql(sql: str) -> bool:
    """仅当 SQL 是单条只读 SELECT 语句时返回 True。"""
    normalized = sql.strip()
    if not normalized:
        return False

    body = normalized[:-1].strip() if normalized.endswith(";") else normalized
    if ";" in body:
        return False
    if not body.lower().startswith("select"):
        return False
    if _MUTATING_SQL_RE.search(body):
        return False
    return True


def apply_default_limit(sql: str, max_rows: int | None = None) -> str:
    """当安全 SELECT 查询没有 LIMIT 时，自动追加默认 LIMIT。"""
    if not is_safe_select_sql(sql):
        raise ValueError("只允许执行单条只读 SELECT 语句")

    limit = max_rows or settings.TEXT_TO_SQL_MAX_ROWS
    body = sql.strip()
    trailing_semicolon = body.endswith(";")
    body = body[:-1].strip() if trailing_semicolon else body

    if not _LIMIT_RE.search(body):
        body = f"{body} LIMIT {limit}"

    return f"{body};"


class DBOperations:
    """TextToSQL 工具使用的数据库操作封装。"""

    def __init__(self, db_url: str | None = None) -> None:
        self.db_url: str = db_url or get_db_url()
        self.engine: Engine | None = None
        self.Session: sessionmaker[Session] | None = None
        self.metadata: MetaData | None = None
        self._init_db()

    def _init_db(self) -> None:
        try:
            connect_args: dict[str, Any] = {}
            if self.db_url.startswith("mysql"):
                connect_args["connect_timeout"] = settings.TEXT_TO_SQL_QUERY_TIMEOUT

            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
            self.Session = sessionmaker(bind=self.engine)
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)
            logger.info("Connected to database")
        except SQLAlchemyError as exc:
            logger.error("Database connection failed: %s", exc)
            raise

    def get_schema_info(self) -> dict[str, Any]:
        """返回表、字段、主键、外键等元数据信息。"""
        schema_info: dict[str, Any] = {}

        if not self.metadata:
            logger.error("Metadata is not initialized")
            return schema_info

        try:
            for table_name, table in self.metadata.tables.items():
                columns = [
                    {
                        "name": column.name,
                        "type": str(column.type),
                        "primary_key": column.primary_key,
                    }
                    for column in table.columns
                ]
                schema_info[table_name] = {
                    "columns": columns,
                    "primary_keys": [col.name for col in table.primary_key],
                    "foreign_keys": [
                        {
                            "column": fk.parent.name,
                            "references": fk.target_fullname,
                        }
                        for fk in table.foreign_keys
                    ],
                }
            logger.info("Loaded database schema for %s tables", len(schema_info))
        except SQLAlchemyError as exc:
            logger.error("Failed to load database schema: %s", exc)
        return schema_info

    def execute_sql(self, sql: str) -> list[dict[str, Any]]:
        """执行安全 SELECT 查询，并以字典列表返回结果。"""
        if not self.engine:
            raise RuntimeError("Database engine is not initialized")

        safe_sql = apply_default_limit(sql)
        results: list[dict[str, Any]] = []

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(safe_sql))
                columns = list(result.keys())
                for row in result.fetchmany(settings.TEXT_TO_SQL_MAX_ROWS):
                    results.append(dict(zip(columns, row)))
            logger.info("SQL executed successfully: %s", safe_sql)
        except SQLAlchemyError as exc:
            logger.error("SQL execution failed: %s", exc)
            raise
        return results

    def validate_sql(self, sql: str) -> bool:
        """在不真正执行查询的前提下校验 SQL 语法。"""
        if not self.engine:
            logger.error("Database engine is not initialized")
            return False
        if not is_safe_select_sql(sql):
            return False

        try:
            safe_sql = apply_default_limit(sql)
            with self.engine.connect() as conn:
                conn.execute(text(f"EXPLAIN {safe_sql}"))
            return True
        except SQLAlchemyError as exc:
            logger.error("SQL validation failed: %s", exc)
            return False


__all__ = ["DBOperations", "apply_default_limit", "get_db_url", "is_safe_select_sql"]
