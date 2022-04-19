"""
Settings and environment variable storage
"""

import logging
from pathlib import Path

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration settings"""
    app_name: str = 'FindTeam'
    repo_name: str = 'findteam-api'
    db_url: str = Field(
        'mysql+aiomysql://root:root@127.0.0.1:3306/findteam',
        env='DB_URL')
    create_tables: bool = Field(True, env='CREATE_TABLES')
    picture_storage: Path = Field(None, env='PICTURE_STORAGE')
    template_path: Path = Field('templates', env='TEMPLATE_PATH')
    logging_format: str = Field(
        f'%(asctime)s %(levelname)s {app_name} %(funcName)s %(message)s',
        env='LOGGING_FORMAT')
    logging_level: int = logging.DEBUG
    email_address: str = Field(
        'findteam.2labz.com@gmail.com',
        env='EMAIL_ADDRESS')
    email_password: str = Field(None, env='EMAIL_PASSWORD')

    def __str__(self):
        return '\n'.join(f'{k}: {v}' for k, v in self.dict().items())


settings = Settings()
