from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_up():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_model_can_be_imported():
    from app.models.email_alert import EmailAlert

    assert EmailAlert.__tablename__ == "email_alert"
