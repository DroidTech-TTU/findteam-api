import logging
from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    enable_sql: bool = Field(True, env='ENABLE_SQL')
    picture_storage: Path = Field('/pictures', env='PICTURE_STORAGE')
    logging_format: str = Field(
        f'%(asctime)s %(levelname)s {app_name} %(message)s', env='LOGGING_FORMAT')
    logging_level: int = logging.DEBUG


@lru_cache()
def get_settings() -> Settings:
    """Return the Settings object"""
    return Settings()
