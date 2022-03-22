"""
Database creation and fetching
"""

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

engine = create_async_engine(
    get_settings().db_url,
    echo=True)
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False)

_Base = declarative_base()


class Base(_Base):
    """Subclass of declarative_base to add dict conversion"""
    __abstract__ = True

    def __iter__(self):
        """Allow iterating over key/value tuples"""
        return iter((c.key, getattr(self, c.key)) for c in inspect(self).mapper.column_attrs)


async def init_models() -> None:
    """Create all models in Base metadata"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Yields an AsyncSession"""
    async with async_session() as session:
        yield session
