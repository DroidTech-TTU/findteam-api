"""
FindTeam FastAPI app
"""

import logging
from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import logger, schemas
from .db import get_db, init_models
from .models import User

app = FastAPI()


@app.on_event('startup')
async def startup():
    """Initialize logging and db models"""
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(message)s'))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_sh)
    logger.debug('Initializing models...')
    await init_models()
    logger.debug('Startup complete')


@app.get('/')
async def index():
    """Return findteam-api version"""
    return {'findteam-api': __version__}


# response_model=List[schemas.User]
@app.get('/users', response_model=List[str])
async def get_users(db: AsyncSession = Depends(get_db)):
    async with db.begin():
        results = await db.execute(select(User))
        return [str(x) for x in results.scalars()]
