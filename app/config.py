from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    enable_sql: bool = False


@lru_cache()
def get_settings():
    """Return the Settings object"""
    return Settings()
