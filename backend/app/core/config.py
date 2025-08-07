from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "CHANGE_ME"
    jwt_alg: str = "HS256"
    openai_api_key: str
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # cached for the process