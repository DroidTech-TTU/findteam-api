"""
FindTeam FastAPI app
"""

import logging
from http import HTTPStatus

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from . import __version__, logger, models, schemas
from .config import Settings, get_settings
from .db import get_db, init_models

app = FastAPI(
    title=get_settings().app_name,
    description=__doc__,
    version=__version__,
    openapi_tags=[
        {
            'name': 'users',
            'description': 'User database operation'
        },
        {
            'name': 'pictures',
            'description': 'Picture storage and retrieval'
        }
    ])


@app.on_event('startup')
async def startup():
    """Initialize logging and db models"""
    _sh = logging.StreamHandler()
    _sh.setFormatter(logging.Formatter(
        '[%(levelname)s] %(asctime)s - %(message)s'))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_sh)
    settings = get_settings()
    if settings.enable_sql:
        logger.debug('Initializing models...')
        await init_models()
    else:
        logger.debug('Not initializing models')
    settings.picture_storage.mkdir(
        parents=True,
        exist_ok=True)
    logger.info('Startup complete')


@app.get('/')
async def index(settings: Settings = Depends(get_settings)):
    """Return findteam-api version"""
    return {settings.repo_name: __version__}


@app.post('/login', response_model=schemas.StatusModel, tags=['users'])
async def post_login(credentials: schemas.CredentialModel, db: AsyncSession = Depends(get_db)):
    """Accept credentials and return auth token"""
    user = await models.User.from_email(credentials.email, db)
    if not user:
        raise HTTPException(status_code=404)
    if not user.check_password(credentials.password):
        raise HTTPException(status_code=403)
    # Todo: return auth token
    return schemas.StatusModel(
        success=True,
        message=HTTPStatus.OK.phrase)


@app.get('/picture/{filename}', response_class=FileResponse)
async def get_picture(filename: str, settings: Settings = Depends(get_settings)):
    """Return picture file"""
    return FileResponse(settings.picture_storage / filename)
