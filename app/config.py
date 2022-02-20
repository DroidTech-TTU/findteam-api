from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    enable_sql: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Return the Settings object"""
    return Settings()
