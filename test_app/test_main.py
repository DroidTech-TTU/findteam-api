"""
FindTeam FastAPI test app
"""

from app.main import app
from fastapi.testclient import TestClient
from app.models import User

client = TestClient(app)


def test_index():
    response = client.get('/')
    assert response.status_code == 200

def test_register():
    response = client.post('/register', json={
        'first_name': 'Test',
        'middle_name': 'Ing',
        'last_name': 'User',
        'email': 'testing@user.com',
        'password': 'hunter2'
    })
    assert response.status_code == 200
    # TODO