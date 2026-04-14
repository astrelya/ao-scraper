from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./ao_scraper.db"
    BOAMP_API_URL: str = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1"
    FETCH_INTERVAL_MINUTES: int = 60

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
