"""
FindTeam FastAPI test app
"""

import pytest
from app.db import drop_models, init_models
from app.main import app
from app.models import Status
from fastapi import status
from httpx import AsyncClient


@pytest.fixture(scope='package')
def anyio_backend():
    """SQLAlchemy is asyncio, so use that"""
    return 'asyncio'


@pytest.fixture(scope='module')
async def client():
    """Yield AsyncClient"""
    async with AsyncClient(
            app=app,
            base_url='http://findteam.2labz.com/') as c:
        yield c


@pytest.fixture(scope='function')
async def ensure_db():
    """Recreate app.models"""
    await drop_models()
    await init_models()


def register_test_ing_user(client, user=1):
    """Post example user 1 or 2 data to /register"""
    if user == 1:
        return client.post(
            '/register',
            json={
                'first_name': 'Test',
                'middle_name': 'Ing',
                'last_name': 'User',
                'email': 'testing@user.com',
                'password': 'hunter2'
            })
    elif user == 2:
        return client.post(
            '/register',
            json={
                'first_name': 'Test',
                'middle_name': 'ed',
                'last_name': 'Success',
                'email': 'tested@success.com',
                'password': 'hunter3'})


@pytest.mark.anyio
async def test_register(client, ensure_db):
    """Register user and check for bearer access token"""
    register = await register_test_ing_user(client)
    assert register.status_code == status.HTTP_200_OK
    json = register.json()
    assert 'access_token' in json
    assert json['token_type'] == 'Bearer'


@pytest.mark.anyio
async def test_login(client, ensure_db):
    """Register user, post to /login, check json for equal bearer access token"""
    # Register, store access_token
    register = await register_test_ing_user(client)
    assert register.status_code == status.HTTP_200_OK
    access_token = register.json()['access_token']
    # Login, compare access_token to result
    login = await client.post(
        '/login',
        data={
            'username': 'testing@user.com',
            'password': 'hunter2',
            'grant_type': 'password'
        })
    assert login.status_code == status.HTTP_200_OK
    json = login.json()
    assert json['access_token'] == access_token  # Same


@pytest.mark.anyio
async def test_create_project(client, ensure_db):
    """Register user, post to /create, check for 200 OK and sane PID"""
    register = await register_test_ing_user(client)
    assert register.status_code == status.HTTP_200_OK
    access_token = register.json()['access_token']
    # Create project using user 1
    create = await client.post(
        '/create',
        json={
            'title': 'A Very Cool Project',
            'status': Status.AWAITING_TEAM,
            'description': 'This is a test.',
            'members': [],
            'tags': [
                {
                    'text': 'Lubbock',
                    'category': 'Location',
                    'is_user_requirement': True
                }
            ]
        },
        headers={
            'Authorization': f'Bearer {access_token}'
        })
    assert create.status_code == status.HTTP_200_OK
    pid = create.json()
    # First PID starts at 1
    assert pid == 1


@pytest.mark.anyio
async def test_send_message(client, ensure_db):
    """Register two users, send chat and compare chat lists"""
    # Register user 1
    register = await register_test_ing_user(client, 1)
    assert register.status_code == status.HTTP_200_OK
    access_token_1 = register.json()['access_token']
    # Register user 2
    register = await register_test_ing_user(client, 2)
    assert register.status_code == status.HTTP_200_OK
    access_token_2 = register.json()['access_token']
    # Access token sanity check (users not same)
    assert access_token_1 != access_token_2
    # Send chat from 1 to 2
    chat = await client.post(
        '/chat',
        json={
            'text': 'Test Message',
            'to_uid': 2
        },
        headers={
            'Authorization': f'Bearer {access_token_1}'
        }
    )
    assert chat.status_code == status.HTTP_200_OK
    # User 1 chats should contain 2
    chats = await client.get(
        '/chats',
        headers={
            'Authorization': f'Bearer {access_token_1}'
        })
    assert chats.status_code == status.HTTP_200_OK
    assert all(chat['to_uid'] == 2 for chat in chats.json())
    # User 2 chats should contain 1
    chats = await client.get(
        '/chats',
        headers={
            'Authorization': f'Bearer {access_token_2}'
        })
    assert chats.status_code == status.HTTP_200_OK
    assert all(chat['to_uid'] == 1 for chat in chats.json())
