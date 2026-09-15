import logging
from datetime import date, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.db.database import SessionLocal
from app.repositories.email_alert_repository import EmailAlertRepository
from app.services.email_alert_service import EmailAlertService
from app.services.email_reader import EmailReader

logger = logging.getLogger(__name__)


def run_email_sync() -> None:
    from_date = date.today() - timedelta(days=settings.CRON_LOOKBACK_DAYS)
    to_date = date.today()

    logger.info("Email alert sync starting (from_date=%s, to_date=%s)", from_date, to_date)
    db = SessionLocal()
    try:
        service = EmailAlertService(
            email_reader=EmailReader(),
            repository=EmailAlertRepository(db=db),
        )
        result = service.process_emails(
            from_date=from_date,
            to_date=to_date,
        )
        logger.info(
            "Email alert sync %s to %s completed: %s",
            from_date,
            to_date,
            result,
        )
    except Exception:
        logger.exception(
            "Email alert sync %s to %s failed",
            from_date,
            to_date,
        )
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler | None:
    if not settings.CRON_ENABLED:
        logger.info("Application cron disabled (CRON_ENABLED=false)")
        return None

    logger.info(
        "Application cron enabled: schedule=%s timezone=%s lookback_days=%s",
        settings.CRON_SCHEDULE,
        settings.CRON_TIMEZONE,
        settings.CRON_LOOKBACK_DAYS,
    )
    scheduler = BackgroundScheduler(timezone=settings.CRON_TIMEZONE)
    scheduler.add_job(
        run_email_sync,
        CronTrigger.from_crontab(
            settings.CRON_SCHEDULE,
            timezone=settings.CRON_TIMEZONE,
        ),
        id="email_alert_sync",
        max_instances=1,
        coalesce=True,
    )
    return scheduler