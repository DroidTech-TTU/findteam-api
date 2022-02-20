"""
FindTeam FastAPI app
"""

import logging
from http import HTTPStatus

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import __version__, logger, models
from .config import Settings, get_settings
from .db import get_db, init_models
from .schemas import CredentialModel, StatusModel

app = FastAPI()


@app.on_event('startup')
async def startup():
    """Initialize logging and db models"""
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(message)s'))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_sh)
    if get_settings().enable_sql:
        logger.debug('Initializing models...')
        await init_models()
    else:
        logger.debug('Not initializing models')
    logger.info('Startup complete')


@app.get('/')
async def index(settings: Settings = Depends(get_settings)):
    """Return findteam-api version"""
    return {settings.repo_name: __version__}


@app.post('/login', response_model=StatusModel)
async def post_login(credentials: CredentialModel, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        user = await db.execute(select(models.User))
    return StatusModel(
        success=True,
        message=HTTPStatus.OK.phrase)

# @app.get('/user/projects', response_model=list[schemas.Project])
# async def get_user_projects(uid: int, db: AsyncSession = Depends(get_db)):
#    async with db.begin():
#        results = await db.execute(select(Project))
#        return [str(x) for x in results.scalars()]
