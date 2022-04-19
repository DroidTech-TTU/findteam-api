"""
FindTeam FastAPI test package
"""

__author__ = 'DroidTech'

from logging import DEBUG
from pathlib import Path
from tempfile import gettempdir

from app.config import settings

settings.db_url = 'mysql+aiomysql://root:root@127.0.0.1/findteam'
#settings.email_password = '123'
settings.logging_level = DEBUG
settings.picture_storage = Path(gettempdir())
