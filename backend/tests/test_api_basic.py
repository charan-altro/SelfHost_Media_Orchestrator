from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "SelfHost Media Orchestrator API is running"}

def test_get_settings():
    response = client.get("/api/settings/")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)
