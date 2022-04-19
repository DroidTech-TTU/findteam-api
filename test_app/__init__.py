"""
FindTeam FastAPI test package
"""

__author__ = 'DroidTech'

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
