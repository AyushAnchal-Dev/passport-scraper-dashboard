import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./dev_scraper.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    MOCK_SCRAPER_MODE: bool = True
    SCRAPE_INTERVAL_MINUTES: int = 5

    # CORS — comma-separated list of allowed origins
    # Set to "*" for development, or "https://yourdomain.com" for production
    CORS_ORIGINS: str = "*"

    # Supported languages for translation
    SUPPORTED_LANGUAGES: str = "en,hi,pa,es,fr,de,ar,zh,ru,ja"

    @property
    def languages_list(self) -> List[str]:
        return [lang.strip() for lang in self.SUPPORTED_LANGUAGES.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        origins = self.CORS_ORIGINS.strip()
        if origins == "*":
            return ["*"]
        return [o.strip() for o in origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
