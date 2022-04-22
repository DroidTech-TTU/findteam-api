"""
FindTeam FastAPI test app
"""

from app.main import app
from fastapi.testclient import TestClient
from pytest import fixture

@fixture
def client():
    with TestClient(app) as c:
        yield c

def test_index(client):
    response = client.get('/')
    print(response)

def test_register(client):
    response = client.post('/register', json={
        'first_name': 'Test',
        'middle_name': 'Ing',
        'last_name': 'User',
        'email': 'testing@user.com',
        'password': 'hunter2'
    })
    #assert response.status_code == 200
    # TODO