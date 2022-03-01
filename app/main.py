"""
FindTeam FastAPI app
"""

from logging import Formatter, StreamHandler

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict
from sqlalchemy.exc import SQLAlchemyError
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
oauth2 = OAuth2PasswordBearer(tokenUrl='login')


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
    response_model=schemas.OAuth2AccessTokenModel,
    responses={
        status.HTTP_403_FORBIDDEN: {
            'description': 'Email not found or password not correct'}
    },
    tags=['users'])
async def post_login(
        credentials: OAuth2PasswordRequestFormStrict = Depends(),
        db: AsyncSession = Depends(get_db)):
    """Process LoginRequestModel to return LoginTokenModel"""
    user = await models.User.from_email(credentials.username, db)
    if not user or not user.check_password(credentials.password):
        raise HTTPException(status_code=403)
    return schemas.OAuth2AccessTokenModel(access_token=user.access_token)


@app.post(
    '/register',
    response_model=schemas.OAuth2AccessTokenModel,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'description': 'Error adding User to database'}
    },
    tags=['users'])
async def post_register(
        credentials: schemas.RegisterRequestModel,
        db: AsyncSession = Depends(get_db)):
    """Process RegisterRequestModel to return LoginTokenModel"""
    user = models.User(
        first_name=credentials.first_name,
        middle_name=credentials.middle_name,
        last_name=credentials.last_name,
        email=credentials.email,
        password=credentials.password)
    try:
        db.add(user)
        await db.commit()
    except SQLAlchemyError as e:
        logger.exception()
        raise HTTPException(status_code=500) from e
    return schemas.OAuth2AccessTokenModel(access_token=user.b64_access_token)


@app.get(
    '/me',
    response_model=schemas.UserResultModel,
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['users'])
async def get_me(
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Get currently logged in UserResultModel"""
    logger.info(f'test = {access_token}')
    logger.info(f'test = {access_token.parse()}')
    user = await models.User.from_b64_access_token(access_token, db)
    if not user or not user.check_b64_access_token(access_token.login_token):
        raise HTTPException(status_code=403)
    return schemas.UserResultModel().from_orm(user)


@app.post(
    '/me',
    responses={
        status.HTTP_200_OK: {'description': 'User info updated successfully'},
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['users'])
async def post_me(
        login_token: schemas.OAuth2AccessTokenModel,
        new_info: schemas.UserRequestModel,
        db: AsyncSession = Depends(get_db)):
    """Process UserRequestModel"""
    user = await models.User.from_uid(login_token.uid, db)
    if not user or not user.check_b64_access_token(login_token.login_token):
        raise HTTPException(status_code=403)
    for attr, val in new_info.dict().items():
        setattr(user, attr, val)
    return Response(status_code=200)


@app.get(
    '/picture/{filename}',
    response_class=FileResponse,
    tags=['pictures'])
async def get_picture(
        filename: str,
        settings: Settings = Depends(get_settings)):
    """Return picture file"""
    return FileResponse(settings.picture_storage / filename)
