"""
FindTeam FastAPI app
"""

import logging
from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import logger, schemas
from .config import Settings, get_settings
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
async def index(settings: Settings = Depends(get_settings)):
    """Return findteam-api version"""
    return {settings.repo_name: __version__}


@app.post('/user/login')
async def post_login(db: AsyncSession = Depends(get_db)):
    pass

@app.get('/user/projects', response_model=List[schemas.Project])
async def get_user_projects(uid: int, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        results = await db.execute(select(Project))
        return [str(x) for x in results.scalars()]
