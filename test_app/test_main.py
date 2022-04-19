from . import client


def test_index():
    response = client.get('/')
    assert response.status_code == 200

# TODO