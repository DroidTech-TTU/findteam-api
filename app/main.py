"""
FindTeam FastAPI app
"""

from hashlib import sha256
from logging import Formatter, StreamHandler

from fastapi import (Depends, FastAPI, HTTPException, Request, UploadFile,
                     status)
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.security import (OAuth2PasswordBearer,
                              OAuth2PasswordRequestFormStrict)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from . import __version__, logger, mail, models, schemas
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e
    return schemas.OAuth2AccessTokenModel(access_token=user.b64_access_token)


@app.get(
    '/user',
    response_model=schemas.UserResultModel,
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'},
        status.HTTP_404_NOT_FOUND: {
            'description': 'User not found (must be authorized for this to occur)'}
    },
    tags=['users'])
async def view_user(
        uid: int = None,
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Return the specified UserResultModel by uid, otherwise return currently logged in user"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if uid:
        user = await models.User.from_uid(uid, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await schemas.UserResultModel.from_orm(user, db)


@app.post(
    '/user/reset',
    tags=['users'])
async def reset_password(
        email: str,
        request: Request,
        db: AsyncSession = Depends(get_db)):
    """Reset logged in user's password - a user may become logged in via an emailed access token during forgotten password"""
    logger.info(f'{email} sending password reset link ({request.client})')
    user = await models.User.from_email(email, db)
    if user:
        mail.send_password_reset(user)
    return Response(status_code=status.HTTP_200_OK)


@app.post(
    '/user',
    responses={
        status.HTTP_200_OK: {'description': 'User info updated successfully'},
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['users'])
async def update_user(
        new_info: schemas.UserRequestModel,
        request: Request,
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Process UserRequestModel"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    uid = user.uid
    try:
        user_dict = dict(user)
        if user_dict.pop('password', None):
            user.password = models.User.hash_password(
                new_info.password)  # Handle password change
            logger.info(
                f'{user} has updated their password ({request.client})')
        for key in user_dict:  # Remaining UserRequestModel attributes
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e
    return Response(status_code=status.HTTP_200_OK)


@app.post(
    '/login',
    response_model=schemas.OAuth2AccessTokenModel,
    responses={
        status.HTTP_403_FORBIDDEN: {
            'description': 'Email not found or password not correct'}
    },
    tags=['users'])
async def login(
        request: Request,
        credentials: OAuth2PasswordRequestFormStrict = Depends(),
        db: AsyncSession = Depends(get_db)):
    """Process LoginRequestModel to return LoginTokenModel"""
    user = await models.User.from_email(credentials.username, db)
    if not user or not models.User.check_password(user, credentials.password):
        logger.warning(f'Incorrect password for {user} ({request.client})')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return schemas.OAuth2AccessTokenModel(access_token=user.b64_access_token)


@app.get(
    '/chats',
    response_model=list[schemas.ChatModel],
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['chats'])
async def get_chat_list(
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """List ChatModels of logged in user"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    raise NotImplemented


@app.get(
    '/chat',
    response_model=list[schemas.MessageResultModel],
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['chats'])
async def get_chat_history(
        uid: int = None,
        pid: int = None,
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """List MessageResultModels of logged in user in dm with uid or pid"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    raise NotImplemented


@app.post(
    '/chat',
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['chats'])
async def send_message(
        msg: schemas.MessageRequestModel,
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Send MessageRequestModel from logged in User"""
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


@app.post(
    '/user/picture',
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            'description': 'Invalid content type uploaded - must be image/png'}
    },
    tags=['pictures', 'users'])
async def upload_user_picture(
        picture: UploadFile,
        settings: Settings = Depends(get_settings),
        access_token: str = Depends(oauth2),
        db: AsyncSession = Depends(get_db)):
    """Upload logged in User's profile picture"""
    user = await models.User.from_b64_access_token(access_token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if picture.content_type != 'image/png':
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    picture_data = picture.file.read()
    local_file = (settings.picture_storage /
                  sha256(picture_data).hexdigest()).with_suffix('.png')
    if not local_file.exists():
        with local_file.open('wb') as f:
            f.write(picture_data)
    logger.debug(f'{local_file.name}')
    user.picture = local_file.name
    await db.commit()
    return Response(status_code=status.HTTP_200_OK)
