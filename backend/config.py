"""
AiMaster 后端配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础
    APP_NAME: str = "AiMaster Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/aimaster"
    )

    # JWT 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MiniMax API 配置
    MINIMAX_API_KEY: str = os.getenv("MINIMAX_API_KEY", "")
    MINIMAX_BASE_URL: str = "https://api.minimaxi.com/anthropic"
    MINIMAX_MODEL: str = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
    # 是否使用模拟模式（不消耗 API 配额）
    AI_MOCK_MODE: bool = os.getenv("AI_MOCK_MODE", "true").lower() == "true"

    # 默认管理员账号
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # CORS 配置
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
