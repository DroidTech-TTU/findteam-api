"""
FindTeam FastAPI test app
"""

from app.main import app
from fastapi.testclient import TestClient
from pytest import fixture
from app.models import MembershipType, Status


@fixture
def client():
    with TestClient(app) as c:
        yield c


def test_register(client):
    response = client.post('/register', json={
        'first_name': 'Test',
        'middle_name': 'Ing',
        'last_name': 'User',
        'email': 'testing@user.com',
        'password': 'hunter2'
    })
    assert response.status_code == 200


def test_login(client):
    response = client.post('/login', json={
        'username': 'testing@user.com',
        'password': 'hunter2',
        'grant_type': 'password'
    })
    assert response.status_code == 200


def test_create_project(client):
    response = client.post('/login', json={
        'username': 'testing@user.com',
        'password': 'hunter2',
        'grant_type': 'password'
    })
    assert response.status_code == 200
    response = client.post('/create', json={
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
    })
    assert response.status_code == 200


def test_search(client):
    raise NotImplementedError