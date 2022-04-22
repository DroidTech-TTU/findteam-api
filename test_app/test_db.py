"""
Testing database creation and fetching
"""

import pytest
from app.db import engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def anyio_backend():
    """Use asyncio backend"""
    return 'asyncio'


@pytest.mark.anyio
async def test_get_db():
    """Test app.db.get_db()"""
    async_session = await anext(get_db())
    assert isinstance(async_session, AsyncSession)
    assert async_session.is_active
