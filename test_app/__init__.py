"""
FindTeam FastAPI test package
"""

__author__ = 'DroidTech'

from logging import DEBUG
from pathlib import Path
from tempfile import gettempdir
from app.config import settings

settings.db_url = 'sqlite+aiosqlite:///:memory:'
settings.logging_level = DEBUG
settings.picture_storage = Path(gettempdir())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
