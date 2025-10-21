from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    debug: Optional[bool] = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings():
    return Settings()
