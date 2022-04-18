from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_index():
    response = client.get('/')
    print(response)
    assert response.status_code == 200