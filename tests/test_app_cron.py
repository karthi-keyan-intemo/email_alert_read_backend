import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("EMAIL", "test@example.com")
os.environ.setdefault("APP_PASSWORD", "secret")
os.environ.setdefault("GMAIL_FOLDER", "INBOX")
os.environ.setdefault("JWT_SECRET_KEY", "jwt-secret")
os.environ.setdefault("N8N_WEBHOOK_SECRET", "n8n-secret")

from app.cron import create_scheduler  # noqa: E402
from app.core.config import settings  # noqa: E402


def test_scheduler_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "CRON_ENABLED", False)
    assert create_scheduler() is None


def test_scheduler_creates_job_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "CRON_ENABLED", True)
    scheduler = create_scheduler()
    assert scheduler is not None
    assert scheduler.get_job("email_alert_sync") is not None


def test_default_schedule_is_10am_ist():
    assert settings.CRON_SCHEDULE == "30 4 * * *"
    assert settings.CRON_TIMEZONE == "Asia/Kolkata"