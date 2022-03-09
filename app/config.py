"""
Settings and environment variable storage
"""

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    create_tables: bool = Field(True, env='CREATE_TABLES')
    picture_storage: Path = Field('/pictures', env='PICTURE_STORAGE')
    logging_format: str = Field(
        f'%(asctime)s %(levelname)s {app_name} %(funcName)s %(message)s', env='LOGGING_FORMAT')
    logging_level: int = logging.DEBUG

    def __str__(self):
        return f'{self.repo_name} - create_tables={self.create_tables}, picture_storage={self.picture_storage}'


@lru_cache()
def get_settings() -> Settings:
    """Return the Settings object"""
    return Settings()
