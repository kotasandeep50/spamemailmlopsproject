from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_prediction():
    response = client.post('/predict', json={'text': 'Free prize, click now'})
    assert response.status_code == 200
    assert response.json()['label'] in {'spam', 'ham'}
