from fastapi.testclient import TestClient

from app.main import create_app


def test_health():
    client = TestClient(create_app())
    response = client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "sefin" in body
