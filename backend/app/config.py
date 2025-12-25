"""
Application configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""
    
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "B24 Analytics Hub")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./b24_analytics.db")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # MCP Bitrix24
    MCP_BITRIX24_URL: str = os.getenv("MCP_BITRIX24_URL", "http://0.0.0.0:8000/mcp")
    MCP_BITRIX24_NAME: str = os.getenv("MCP_BITRIX24_NAME", "bitrix24-main")
    MCP_BITRIX24_TRANSPORT: str = os.getenv("MCP_BITRIX24_TRANSPORT", "streamable_http")
    MCP_BITRIX24_AUTH_TOKEN: str = os.getenv("MCP_BITRIX24_AUTH_TOKEN", "")
    
    # Python Executor
    PYTHON_EXECUTOR_URL: str = os.getenv("PYTHON_EXECUTOR_URL", "http://python-executor:8002")
    PYTHON_EXECUTOR_TIMEOUT: int = int(os.getenv("PYTHON_EXECUTOR_TIMEOUT", "30"))
    
    def validate(self):
        """Validate required settings"""
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is required")
        if not self.JWT_REFRESH_SECRET_KEY:
            raise ValueError("JWT_REFRESH_SECRET_KEY is required")
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")


settings = Settings()

