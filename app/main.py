"""
FindTeam FastAPI app
"""

from logging import Formatter, StreamHandler

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.security import (OAuth2PasswordBearer,
                              OAuth2PasswordRequestFormStrict)
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
    logger.debug(str(settings))
    if settings.create_tables:
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
async def index():
    """Redirect to /docs"""
    return RedirectResponse(
        url='/docs',
        status_code=status.HTTP_303_SEE_OTHER)


@app.post(
    '/register',
    response_model=schemas.OAuth2AccessTokenModel,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'description': 'Error during User registration commit'}
    },
    tags=['users'])
async def register(
        credentials: schemas.RegisterRequestModel,
        db: AsyncSession = Depends(get_db)):
    """Process RegisterRequestModel to return LoginTokenModel"""
    user = models.User(
        first_name=credentials.first_name,
        middle_name=credentials.middle_name,
        last_name=credentials.last_name,
        email=credentials.email,
        password=models.User.hash_password(credentials.password))
    db.add(user)
    try:
        await db.commit()
    except SQLAlchemyError as e:
        logger.exception('Error during User registration commit')
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
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=403)
    return schemas.UserResultModel(
        urls=[schemas.UrlModel.from_orm(url) for url in await models.UserUrl.get_user_urls(user.uid, db)],
        tags=[schemas.TagModel.from_orm(tag) for tag in await models.Tag.get_user_tags(user.uid, db)],
        **dict(user))


@app.post(
    '/me',
    responses={
        status.HTTP_200_OK: {'description': 'User info updated successfully'},
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['users'])
async def post_me(
        new_info: schemas.UserRequestModel,
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Process UserRequestModel"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=403)
    uid = user.uid
    try:
        for key in dict(user):  # Remaining UserRequestModel attributes
            try:
                setattr(user, key, getattr(new_info, key))
            except AttributeError:  # Ignore extras
                pass
        await db.commit()
        await models.Tag.set_user_tags(
            uid,
            [dict(tag_dict) for tag_dict in new_info.tags],
            db)
        await models.UserUrl.set_user_urls(
            uid,
            [dict(url_model) for url_model in new_info.urls],
            db)
    except SQLAlchemyError as e:
        logger.exception('Error during User update commit')
        raise HTTPException(status_code=500) from e
    return Response(status_code=200)


@app.post(
    '/login',
    response_model=schemas.OAuth2AccessTokenModel,
    responses={
        status.HTTP_403_FORBIDDEN: {
            'description': 'Email not found or password not correct'}
    },
    tags=['users'])
async def post_login(
        request: Request,
        credentials: OAuth2PasswordRequestFormStrict = Depends(),
        db: AsyncSession = Depends(get_db)):
    """Process LoginRequestModel to return LoginTokenModel"""
    user = await models.User.from_email(credentials.username, db)
    if not user or not models.User.check_password(user, credentials.password):
        logger.warning(f'Incorrect password for {user} ({request.client})')
        raise HTTPException(status_code=403)
    return schemas.OAuth2AccessTokenModel(access_token=user.b64_access_token)


@app.post('/me/reset')
async def reset_password():
    raise NotImplemented


@app.get(
    '/picture/{filename}',
    response_class=FileResponse,
    tags=['pictures'])
async def get_picture(
        filename: str,
        settings: Settings = Depends(get_settings)):
    """Return picture file"""
    return FileResponse(settings.picture_storage / filename)
