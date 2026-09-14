import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("EMAIL", "test@example.com")
os.environ.setdefault("APP_PASSWORD", "secret")
os.environ.setdefault("GMAIL_FOLDER", "INBOX")
os.environ.setdefault("JWT_SECRET_KEY", "jwt-secret")
os.environ.setdefault("N8N_WEBHOOK_SECRET", "n8n-secret")

from app.core.config import settings
from app.db import database as db_module
from app.db.base import Base
from app.main import app
from app.models.email_alert import EmailAlert
from app.models.email_alert_request import EmailAlertRequest

settings.N8N_WEBHOOK_SECRET = "n8n-secret"

client = TestClient(app)


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    original_session_local = db_module.SessionLocal
    db_module.SessionLocal = SessionLocal

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[db_module.get_db] = override_get_db
    try:
        yield SessionLocal
    finally:
        app.dependency_overrides.clear()
        db_module.SessionLocal = original_session_local


def seed_alerts(session_factory, records):
    with session_factory() as db:
        for item in records:
            db.add(EmailAlert(**item))
        db.commit()


def test_n8n_webhook_updates_all_matching_alerts_and_returns_summary(sqlite_session):
    seed_alerts(sqlite_session, [
        {"id": uuid4(), "message_id": "msg-1", "email_subject": "Unknown error found in Spot Rates", "error_type": "UNKNOWN", "environment": "PRODUCTION", "source_name": "ONEY", "error_message": "ElementMissingInPage: Dropdown options contain 'DRY 40' and 'DRY 40H' but do not include the expected 'DRY 20'.", "azure_task": None},
        {"id": uuid4(), "message_id": "msg-2", "email_subject": "Unknown error found in Spot Rates", "error_type": "UNKNOWN", "environment": "PRODUCTION", "source_name": "ONEY", "error_message": "ElementMissingInPage: Another test message", "azure_task": None},
        {"id": uuid4(), "message_id": "msg-3", "email_subject": "Response Validation Error Found in Spot Rates", "error_type": "RESPONSE_VALIDATION", "environment": "PRODUCTION", "source_name": "ONEY", "error_message": "validation failed", "azure_task": None},
    ])

    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "elementmissinginpage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["alerts_updated"] == 2
    assert payload["error_message"] == "elementmissinginpage"
    assert payload["azure_task_url"] == "https://dev.azure.com/example/project/_workitems/edit/123"

    with sqlite_session() as db:
        matches = db.query(EmailAlert).filter(EmailAlert.error_message.ilike("%ElementMissingInPage%"))
        assert sum(1 for _ in matches if _.azure_task == "https://dev.azure.com/example/project/_workitems/edit/123") == 2
        untouched = db.query(EmailAlert).filter(EmailAlert.error_message.ilike("%validation failed%"))
        assert all(alert.azure_task is None for alert in untouched)


def test_n8n_webhook_requires_secret_header(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
    )
    assert response.status_code == 401


def test_n8n_webhook_rejects_invalid_secret(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": "wrong-secret"},
    )
    assert response.status_code == 401


def test_n8n_webhook_rejects_empty_secret(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": ""},
    )
    assert response.status_code == 401


def test_n8n_webhook_returns_404_when_no_match(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "Totally unrelated error", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/456"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "No alert found matching the provided error message"


def test_n8n_webhook_validates_missing_error_message(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 422


def test_n8n_webhook_validates_blank_error_message(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "   ", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 422


def test_n8n_webhook_validates_missing_azure_task_url(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 422


def test_n8n_webhook_validates_blank_azure_task_url(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "   "},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 422


def test_n8n_webhook_validates_invalid_url(sqlite_session):
    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "not-a-valid-url"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )
    assert response.status_code == 422


def test_n8n_webhook_only_updates_azure_task_field(sqlite_session):
    alert = EmailAlert(
        id=uuid4(),
        message_id="msg-4",
        email_subject="Unknown error found in Spot Rates",
        error_type="UNKNOWN",
        environment="PRODUCTION",
        source_name="ONEY",
        error_message="ElementMissingInPage: Dropdown options contain 'DRY 40' and 'DRY 40H' but do not include the expected 'DRY 20'.",
        azure_task=None,
    )
    with sqlite_session() as db:
        db.add(alert)
        db.add(EmailAlertRequest(email_alert_id=alert.id, request_id=uuid4()))
        db.commit()

    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/999"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )

    assert response.status_code == 200
    with sqlite_session() as db:
        saved = db.query(EmailAlert).filter_by(id=alert.id).one()
        assert saved.azure_task == "https://dev.azure.com/example/project/_workitems/edit/999"
        assert saved.email_subject == "Unknown error found in Spot Rates"
        assert saved.error_message == "ElementMissingInPage: Dropdown options contain 'DRY 40' and 'DRY 40H' but do not include the expected 'DRY 20'."
        assert saved.environment == "PRODUCTION"
        assert db.query(EmailAlertRequest).count() == 1


def test_n8n_webhook_is_idempotent(sqlite_session):
    seed_alerts(sqlite_session, [
        {"id": uuid4(), "message_id": "msg-5", "email_subject": "Unknown error found in Spot Rates", "error_type": "UNKNOWN", "environment": "PRODUCTION", "source_name": "ONEY", "error_message": "ElementMissingInPage: Dropdown options contain 'DRY 40' and 'DRY 40H' but do not include the expected 'DRY 20'.", "azure_task": "https://dev.azure.com/example/project/_workitems/edit/123"},
    ])

    response = client.post(
        "/api/integrations/n8n/azure-task",
        json={"error_message": "ElementMissingInPage", "azure_task_url": "https://dev.azure.com/example/project/_workitems/edit/123"},
        headers={"X-Webhook-Secret": "n8n-secret"},
    )

    assert response.status_code == 200
    assert response.json()["alerts_updated"] == 1


def test_ui_azure_task_endpoint_still_works(sqlite_session):
    alert = EmailAlert(
        id=uuid4(),
        message_id="msg-ui-1",
        email_subject="Test subject",
        error_type="UNKNOWN",
        environment="PRODUCTION",
        source_name="ONEY",
        error_message="ElementMissingInPage: Dropdown options contain 'DRY 40' and 'DRY 40H' but do not include the expected 'DRY 20'.",
        azure_task=None,
    )
    with sqlite_session() as db:
        db.add(alert)
        db.commit()

    from app.api.routes import email_alert as email_alert_routes

    original = email_alert_routes.require_permission
    email_alert_routes.require_permission = lambda permission_name: (lambda: alert)
    try:
        response = client.patch(
            f"/api/email-alerts/{alert.id}/azure-task",
            json={"azure_task": "https://dev.azure.com/example/project/_workitems/edit/ui-123"},
        )
    finally:
        email_alert_routes.require_permission = original

    assert response.status_code == 200
    assert response.json()["azure_task"] == "https://dev.azure.com/example/project/_workitems/edit/ui-123"
