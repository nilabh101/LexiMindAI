from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    APP_NAME: str = "LexiMind AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "leximind-secret-key-change-in-production-32chars"
    DATABASE_URL: str = "sqlite+aiosqlite:///./leximind.db"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "txt,pdf,docx"
    RATE_LIMIT_PER_MINUTE: int = 60
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip() for e in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
