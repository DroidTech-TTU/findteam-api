"""
Testing database creation and fetching
"""

import pytest
from app.db import engine, get_db, init_models
from pytest import fixture
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession


@fixture
def anyio_backend():
    """Use asyncio backend"""
    return 'asyncio'


@pytest.mark.anyio
async def test_get_db():
    """Test app.db.get_db()"""
    async_session = await anext(get_db())
    assert isinstance(async_session, AsyncSession)
    assert async_session.is_active


@pytest.mark.anyio
async def test_init_models():
    """Test app.db.init_models()"""
    async with engine.connect() as conn:
        inspector = inspect(engine.sync_engine)
    assert len(inspector.get_table_names()) == 0
    await init_models()
    assert len(inspector.get_table_names()) == 9
