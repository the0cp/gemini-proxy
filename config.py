from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    MAX_REQUESTS_PER_MIN: int = 12
    REQUEST_DELAY_MIN: float = 1.0
    REQUEST_DELAY_MAX: float = 4.0
    HEADLESS: bool = False
    LOG_LEVEL: str = "info" 
    AUTH_DIR: Path = Path("auth")
    LOG_DIR: Path = Path("logs")
    USER_AGENT: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()