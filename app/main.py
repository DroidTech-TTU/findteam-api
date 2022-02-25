"""
FindTeam FastAPI app
"""

from logging import Formatter, StreamHandler

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
    settings = get_settings()
    _sh = StreamHandler()
    _sh.setFormatter(Formatter(settings.logging_format))
    logger.setLevel(settings.logging_level)
    logger.addHandler(_sh)
    if settings.enable_sql:
        logger.debug('Initializing models...')
        await init_models()
    else:
        logger.debug('Not initializing models')
    if settings.picture_storage:
        settings.picture_storage.mkdir(
            parents=True,
            exist_ok=True)
    logger.info('Startup complete')


@app.get('/')
async def index(settings: Settings = Depends(get_settings)):
    """Return findteam-api version"""
    return {settings.repo_name: __version__}


@app.post(
    '/login',
    response_model=schemas.LoginResultModel,
    responses={
        403: {'description': 'Email not found or password not correct'}
    },
    tags=['users'])
async def post_login(credentials: schemas.LoginRequestModel, db: AsyncSession = Depends(get_db)):
    """Process LoginRequestModel to return LoginResultModel"""
    user = await models.User.from_email(credentials.email, db)
    if not user or not user.check_password(credentials.password):
        raise HTTPException(status_code=403)
    return schemas.LoginResultModel(
        uid=user.uid,
        login_token=user.b64_login_token)


@app.post(
    '/register',
    response_model=schemas.LoginResultModel,
    response={
        500: {'description': 'Error adding User to database'}
    },
    tags=['users'])
async def post_register(credentials: schemas.RegisterRequestModel, db: AsyncSession = Depends(get_db)):
    """Process RegisterRequestModel to return LoginResultModel"""
    user = models.User(
        first_name=credentials.first_name,
        middle_name=credentials.middle_name,
        last_name=credentials.last_name,
        email=credentials.email,
        password=credentials.password)
    try:
        db.add(user)
        await db.commit()
    except:
        logger.exception()
        raise HTTPException(status_code=500)
    return schemas.LoginResultModel(
        uid=user.uid,
        login_token=user.b64_login_token)


@app.get('/user', response_model=schemas.UserModel, tags=['users'])
async def get_me(login_token: schemas.LoginTokenModel, db: AsyncSession = Depends(get_db)):
    """Get currently logged in UserModel"""
    user = await models.User.from_uid(login_token.uid)
    if not user:
        raise HTTPException(status_code=403)
    if not user.check_b64_login_token(login_token.login_token):
        raise HTTPException(status_code=403)
    return schemas.UserModel().from_orm(user)


@app.get('/picture/{filename}', response_class=FileResponse, tags=['pictures'])
async def get_picture(filename: str, settings: Settings = Depends(get_settings)):
    """Return picture file"""
    return FileResponse(settings.picture_storage / filename)
