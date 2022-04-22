import pytest
from app import models
from app.db import engine, init_models, drop_models
from sqlalchemy import inspect


@pytest.fixture
def anyio_backend():
    """Use asyncio backend"""
    return 'asyncio'


@pytest.mark.anyio
async def test_init_models():
    """Test app.db.init_models()"""
    await drop_models()
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda x: inspect(x).get_table_names())
        assert len(tables) == 0
    await init_models()
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda x: inspect(x).get_table_names())
        assert len(tables) == 9
