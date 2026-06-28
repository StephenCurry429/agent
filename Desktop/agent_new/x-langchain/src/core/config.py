# -*- coding: utf-8 -*-
"""项目统一配置入口。

所有配置都会从环境变量和项目 `.env` 文件中加载。请统一通过下面的方式导入：

    from core.config import settings
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


import os

outer_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '.env')
inner_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')

class Settings(BaseSettings):
    """模型 Provider、工具和示例运行时使用的配置。"""

    model_config = SettingsConfigDict(
        env_file=outer_env_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 模型选择
    MODEL_NAME: str = "deepseek"
    TEXT_TO_SQL_MODEL_NAME: str | None = None

    # OpenAI 兼容接口
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    MIMO_MODEL: str = ""

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL_NAME: str = "deepseek-chat"

    # Doubao
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_BASE: str = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL_NAME: str = ""

    # 阿里云通义
    ALIYUN_API_KEY: str = ""
    ALIYUN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    ALIYUN_MODEL_NAME: str = "qwen-plus"

    # 外部工具
    AMAP_API_KEY: str = ""
    MCP_ENABLED: bool = False

    # 数据库 / TextToSQL
    DB_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = ""
    TEXT_TO_SQL_MAX_ROWS: int = 100
    TEXT_TO_SQL_QUERY_TIMEOUT: int = 30

    # 通用行为
    TEMPERATURE: float = 0.0
    DEBUG: bool = True
    STRUCTURED: bool = False

    @field_validator("TEMPERATURE", mode="before")
    @classmethod
    def parse_temperature(cls, value: object) -> float:
        try:
            if value in (None, ""):
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @field_validator("DB_PORT", "TEXT_TO_SQL_MAX_ROWS", "TEXT_TO_SQL_QUERY_TIMEOUT", mode="before")
    @classmethod
    def parse_positive_int(cls, value: object, info) -> int:
        defaults = {
            "DB_PORT": 3306,
            "TEXT_TO_SQL_MAX_ROWS": 100,
            "TEXT_TO_SQL_QUERY_TIMEOUT": 30,
        }
        try:
            parsed = int(value)
            return parsed if parsed > 0 else defaults[info.field_name]
        except (TypeError, ValueError):
            return defaults[info.field_name]

    @property
    def text_to_sql_model_name(self) -> str:
        """TextToSQL 工具使用的模型 Provider。"""
        return self.TEXT_TO_SQL_MODEL_NAME or self.MODEL_NAME or "deepseek"

    def get_db_url(self) -> str:
        """返回当前配置的 SQLAlchemy 数据库连接地址。"""
        if self.DB_URL:
            return self.DB_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def validate_model_config(self, model_name: str) -> bool:
        """检查指定 Provider 是否具备足够的运行配置。"""
        provider = model_name.lower()
        if provider == "deepseek":
            return bool(self.DEEPSEEK_API_KEY and self.DEEPSEEK_MODEL_NAME)
        if provider == "doubao":
            return bool(self.DOUBAO_API_KEY and self.DOUBAO_MODEL_NAME)
        if provider in {"tongyi", "aliyun"}:
            return bool(self.ALIYUN_API_KEY and self.ALIYUN_MODEL_NAME)
        if provider in {"openai", "mimo"}:
            return bool(self.OPENAI_API_KEY and self.OPENAI_BASE_URL)
        if provider == "mock":
            return True
        return False


settings = Settings()

__all__ = ["Settings", "settings"]
