"""
FindTeam FastAPI test package
"""

__author__ = 'DroidTech'

from logging import DEBUG

from app.config import settings


settings.db_url = 'mysql+aiomysql://root:root@127.0.0.1/findteam'
settings.logging_level = DEBUG
