from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core import auth as auth_core
from app.main import app
from app.models.auth import Permission, Role, User
from app.services.auth_service import create_access_token, hash_password


client = TestClient(app)


class FakeRepository:
    user = None

    def __init__(self, db):
        pass

    def find_user_by_email(self, email):
        if self.user is not None and self.user.email == email:
            return self.user
        return None

    def find_user_by_id(self, user_id):
        if self.user is not None and self.user.id == user_id:
            return self.user
        return None


def make_user(active=True):
    permission = Permission(name="ALERT_VIEW")
    role = Role(name="VIEWER", permissions=[permission])
    return User(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        password_hash=hash_password("correct-password"),
        is_active=active,
        roles=[role],
    )


def test_login_success_and_me(monkeypatch):
    FakeRepository.user = make_user()
    monkeypatch.setattr(auth_routes, "AuthRepository", FakeRepository)
    monkeypatch.setattr(auth_core, "AuthRepository", FakeRepository)

    response = client.post("/api/auth/login", json={"email": "ADMIN@EXAMPLE.COM", "password": "correct-password"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "admin@example.com"
    assert "password_hash" not in payload["user"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me_response.status_code == 200
    assert me_response.json()["roles"] == ["VIEWER"]


def test_login_rejects_invalid_password(monkeypatch):
    FakeRepository.user = make_user()
    monkeypatch.setattr(auth_routes, "AuthRepository", FakeRepository)

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_login_rejects_inactive_user(monkeypatch):
    FakeRepository.user = make_user(active=False)
    monkeypatch.setattr(auth_routes, "AuthRepository", FakeRepository)

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "correct-password"})

    assert response.status_code == 401


def test_me_rejects_missing_and_invalid_tokens():
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_permission_dependency_returns_403_for_viewer():
    FakeRepository.user = make_user()
    monkeypatch_token = create_access_token(FakeRepository.user.id)
    import app.core.auth as auth_module
    original_repository = auth_module.AuthRepository
    auth_module.AuthRepository = FakeRepository
    try:
        response = client.post("/api/email-alerts/read", headers={"Authorization": f"Bearer {monkeypatch_token}"}, json={"from_date": "2026-09-08", "to_date": "2026-09-10"})
    finally:
        auth_module.AuthRepository = original_repository

    assert response.status_code == 403