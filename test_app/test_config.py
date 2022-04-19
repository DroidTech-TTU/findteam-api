"""
Testing settings and environment variable storage
"""

from app.config import Settings

from . import settings


def test_settings():
    assert isinstance(settings, Settings)
