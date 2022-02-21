from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    enable_sql: bool = True
    picture_storage: Path = Path.cwd() / 'pictures'


@lru_cache()
def get_settings() -> Settings:
    """Return the Settings object"""
    return Settings()
