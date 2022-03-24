"""
FindTeam FastAPI app
"""

from datetime import datetime
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
        async_session: AsyncSession = Depends(get_db)):
    """Process RegisterRequestModel to return LoginTokenModel"""
    user = models.User(
        first_name=credentials.first_name,
        middle_name=credentials.middle_name,
        last_name=credentials.last_name,
        email=credentials.email,
        password=models.User.hash_password(credentials.password))
    async_session.add(user)
    try:
        await async_session.commit()
    except SQLAlchemyError as exception:
        logger.exception('Error during User registration commit')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exception
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
        async_session: AsyncSession = Depends(get_db)):
    """Return the specified UserResultModel by uid, otherwise return currently logged in user"""
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if uid:
        user = await models.User.from_uid(uid, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return await schemas.UserResultModel.from_orm(user, async_session)


@app.post(
    '/user/reset',
    tags=['users'])
async def reset_password(
        email: str,
        request: Request,
        async_session: AsyncSession = Depends(get_db)):
    """Reset logged in user's password -
    a user may become logged in via an emailed access token during forgotten password"""
    logger.info('%s sending password reset link (%s)',
                email, request.client.host)
    user = await models.User.from_email(email, async_session)
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
        async_session: AsyncSession = Depends(get_db)):
    """Process UserRequestModel"""
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    uid = user.uid
    try:
        user_dict = dict(user)
        if user_dict.pop('password', None):
            user.password = models.User.hash_password(
                new_info.password)  # Handle password change
            logger.info('%s has updated their password (%s)',
                        user, request.client.host)
        for key in user_dict:  # Remaining UserRequestModel attributes
            try:
                setattr(user, key, getattr(new_info, key))
            except AttributeError:  # Ignore extras
                pass
        await async_session.commit()
        await models.Tag.set_tags(
            uid,
            [dict(tag_dict) for tag_dict in new_info.tags],
            async_session)
        await models.UserUrl.set_user_urls(
            uid,
            [dict(url_model) for url_model in new_info.urls],
            async_session)
    except SQLAlchemyError as exception:
        logger.exception('Error during User update commit')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exception
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
        async_session: AsyncSession = Depends(get_db)):
    """Process LoginRequestModel to return LoginTokenModel"""
    user = await models.User.from_email(credentials.username, async_session)
    if not user or not models.User.check_password(user, credentials.password):
        logger.warning('Incorrect password for %s (%s)',
                       user, request.client.host)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return schemas.OAuth2AccessTokenModel(access_token=user.b64_access_token)


@app.get(
    '/chats',
    response_model=set[int],
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['chats'])
async def get_chat_list(
        access_token: str = Depends(oauth2),
        async_session: AsyncSession = Depends(get_db)):
    """List active direct message uids between current user"""
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return await models.Message.get_chat_list(user.uid, async_session)


@app.get(
    '/chat',
    response_model=list[schemas.MessageResultModel],
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'},
        status.HTTP_406_NOT_ACCEPTABLE: {
            'description': 'uid XOR pid must be specified'}
    },
    tags=['chats'])
async def get_chat_history(
        uid: int = None,
        pid: int = None,
        access_token: str = Depends(oauth2),
        async_session: AsyncSession = Depends(get_db)):
    """List MessageResultModels of logged in user in chat with uid or pid"""
    if not uid and not pid:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    chat_history = await models.Message.get_chat_history(
        user.uid,
        async_session,
        to_uid=uid,
        to_pid=pid)
    results = []
    for message in chat_history:
        if message.to_uid == user.uid:
            message.is_read = True
        results.append(schemas.MessageResultModel.from_orm(message))
    return results


@app.post(
    '/chat',
    responses={
        status.HTTP_403_FORBIDDEN: {'description': 'User authorization error'}
    },
    tags=['chats'])
async def send_message(
        msg: schemas.MessageRequestModel,
        access_token: str = Depends(oauth2),
        async_session: AsyncSession = Depends(get_db)):
    """Send MessageRequestModel from logged in User"""
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    message = models.Message(
        from_uid=user.uid,
        to_uid=msg.to_uid,
        to_pid=msg.to_pid,
        date=datetime.now(),
        text=msg.text,
        is_read=False)
    async_session.add(message)
    try:
        await async_session.commit()
    except SQLAlchemyError as exception:
        logger.exception('Error during Message send commit')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exception


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
        request: Request,
        settings: Settings = Depends(get_settings),
        access_token: str = Depends(oauth2),
        async_session: AsyncSession = Depends(get_db)):
    """Upload logged in User's profile picture"""
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if picture.content_type != 'image/png':
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    picture_data = picture.file.read()
    local_file_path = (settings.picture_storage /
                       sha256(picture_data).hexdigest()).with_suffix('.png')
    if not local_file_path.exists():
        with local_file_path.open('wb') as local_file:
            local_file.write(picture_data)
    logger.debug('%s uploaded %s (%s)', user,
                 local_file_path, request.client.host)
    user.picture = local_file_path.name
    await async_session.commit()
    return Response(status_code=status.HTTP_200_OK)


@app.get(
    '/project',
    response_model=schemas.ProjectResultModel,
    responses={
        status.HTTP_403_FORBIDDEN: {
            'description': 'User authorization or permission error'}
    },
    tags=['projects'])
async def view_project(
        pid: int,
        access_token: str = Depends(oauth2),
        async_session: AsyncSession = Depends(get_db)):
    user = await models.User.from_b64_access_token(access_token, async_session)
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    project = await models.Project.from_pid(pid, async_session)
    return await schemas.ProjectResultModel.from_orm(project, async_session)
