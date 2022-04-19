"""
Testing database creation and fetching
"""

import pytest
from app.db import get_db, init_models
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.anyio
async def test_get_db():
    async_session = await anext(get_db())
    assert isinstance(async_session, AsyncSession)

@pytest.mark.anyio
async def test_init_models():
    await init_models()