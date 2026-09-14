from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import UUID as SQLAlchemyUUID, String, case, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.email_alert import EmailAlert
from app.models.email_alert_request import EmailAlertRequest


@dataclass(frozen=True)
class EmailAlertFilters:
    from_date: date | None = None
    to_date: date | None = None
    environment: str | None = None
    source_name: str | None = None
    error_type: str | None = None
    email_subject: str | None = None
    error_message: str | None = None
    azure_task: str | None = None
    request_id: str | None = None
    alert_timestamp_from: date | None = None
    alert_timestamp_to: date | None = None
    email_received_at_from: date | None = None
    email_received_at_to: date | None = None
    search: str | None = None


class EmailAlertRepository:

    def __init__(self, db: Session):
        self.__db = db

    def exists_by_message_id(
        self,
        message_id: str,
    ) -> bool:
        print(f"Checking existence for message_id: {message_id}")
        statement = select(EmailAlert.id).where(
            EmailAlert.message_id == message_id
        )

        return self.__db.scalar(statement) is not None

    def save(
        self,
        alert: EmailAlert,
    ) -> EmailAlert:
        print(f"Saving alert with message_id: {alert.message_id}")
        self.__db.add(alert)
        self.__db.flush()

        return alert
    
    def commit(self):
        self.__db.commit()
        
    def find_by_alert_details(
        self,
        environment: str | None,
        source_name: str | None,
        error_message: str | None,
    ) -> EmailAlert | None:

        statement = select(EmailAlert).where(
            EmailAlert.environment == environment,
            EmailAlert.source_name == source_name,
            EmailAlert.error_message == error_message,
        )

        return self.__db.scalar(statement)
    
    def find_all(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        offset: int = 0,
        limit: int | None = None,
        search: str | None = None,
        sort_by: str = "alert_timestamp",
        sort_order: str = "desc",
        filters: EmailAlertFilters | None = None,
    ) -> list[EmailAlert]:
        statement = select(EmailAlert).options(selectinload(EmailAlert.requests))
        filters = filters or EmailAlertFilters(from_date=from_date, to_date=to_date, search=search)
        statement = self._apply_filters(statement, filters)
        sort_column = {
            "alert_timestamp": EmailAlert.alert_timestamp,
            "email_received_at": EmailAlert.email_received_at,
            "environment": EmailAlert.environment,
            "source_name": EmailAlert.source_name,
            "error_type": EmailAlert.error_type,
            "created_at": EmailAlert.created_at,
        }.get(sort_by, EmailAlert.alert_timestamp)
        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
        statement = statement.order_by(ordering, EmailAlert.created_at.desc(), EmailAlert.id.desc())
        if limit is not None:
            statement = statement.offset(offset).limit(limit)

        return list(self.__db.scalars(statement).unique().all())

    def get_page_summary(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        search: str | None = None,
        filters: EmailAlertFilters | None = None,
    ) -> dict[str, int]:
        statement = (
            select(
                func.count(func.distinct(EmailAlert.id)),
                func.count(func.distinct(case((EmailAlert.error_type == "UNKNOWN", EmailAlert.id)))),
                func.count(func.distinct(case((EmailAlert.error_type == "RESPONSE_VALIDATION", EmailAlert.id)))),
                func.count(EmailAlertRequest.id),
            )
            .select_from(EmailAlert)
            .outerjoin(EmailAlertRequest, EmailAlertRequest.email_alert_id == EmailAlert.id)
        )
        filters = filters or EmailAlertFilters(from_date=from_date, to_date=to_date, search=search)
        statement = self._apply_filters(statement, filters)
        total_alerts, unknown_errors, response_validation_errors, total_requests = self.__db.execute(statement).one()
        return {
            "total_alerts": int(total_alerts),
            "unknown_errors": int(unknown_errors),
            "response_validation_errors": int(response_validation_errors),
            "total_requests": int(total_requests),
        }

    def find_all_for_export(
        self,
        from_date: date | datetime | None = None,
        to_date: date | datetime | None = None,
        filters: EmailAlertFilters | None = None,
    ) -> list[EmailAlert]:
        statement = select(EmailAlert).options(selectinload(EmailAlert.requests))
        filters = filters or EmailAlertFilters(from_date=from_date, to_date=to_date)
        statement = self._apply_filters(statement, filters)
        statement = statement.order_by(EmailAlert.created_at.desc(), EmailAlert.id.desc())
        return list(
            self.__db.scalars(statement).unique().all()
        )

    @staticmethod
    def _as_utc_boundary(value: date | datetime, end: bool = False) -> datetime:
        if isinstance(value, datetime):
            return value
        boundary = datetime.combine(value, time.min, tzinfo=timezone.utc)
        return boundary + timedelta(days=1) if end else boundary

    def _apply_filters(self, statement, filters: EmailAlertFilters):
        if filters.from_date is not None:
            statement = statement.where(EmailAlert.email_received_at >= self._as_utc_boundary(filters.from_date))
        if filters.to_date is not None:
            statement = statement.where(EmailAlert.email_received_at < self._as_utc_boundary(filters.to_date, end=True))
        for column, value in (
            (EmailAlert.environment, filters.environment),
            (EmailAlert.error_type, filters.error_type),
        ):
            if value:
                statement = statement.where(column == value)
        for column, value in (
            (EmailAlert.source_name, filters.source_name),
            (EmailAlert.email_subject, filters.email_subject),
            (EmailAlert.error_message, filters.error_message),
            (EmailAlert.azure_task, filters.azure_task),
        ):
            if value:
                statement = statement.where(column.ilike(f"%{value.strip()}%"))
        if filters.alert_timestamp_from:
            statement = statement.where(EmailAlert.alert_timestamp >= self._as_utc_boundary(filters.alert_timestamp_from))
        if filters.alert_timestamp_to:
            statement = statement.where(EmailAlert.alert_timestamp < self._as_utc_boundary(filters.alert_timestamp_to, end=True))
        if filters.email_received_at_from:
            statement = statement.where(EmailAlert.email_received_at >= self._as_utc_boundary(filters.email_received_at_from))
        if filters.email_received_at_to:
            statement = statement.where(EmailAlert.email_received_at < self._as_utc_boundary(filters.email_received_at_to, end=True))
        if filters.request_id:
            try:
                request_uuid = UUID(filters.request_id)
                statement = statement.where(exists(select(1).where(EmailAlertRequest.email_alert_id == EmailAlert.id, EmailAlertRequest.request_id == request_uuid)))
            except ValueError:
                statement = statement.where(exists(select(1).where(
                    EmailAlertRequest.email_alert_id == EmailAlert.id,
                    EmailAlertRequest.request_id.cast(String).ilike(f"%{filters.request_id.strip()}%"),
                )))
        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            statement = statement.where(or_(
                EmailAlert.source_name.ilike(pattern),
                EmailAlert.error_message.ilike(pattern),
                EmailAlert.email_subject.ilike(pattern),
                EmailAlert.environment.ilike(pattern),
                exists(select(1).where(
                    EmailAlertRequest.email_alert_id == EmailAlert.id,
                    EmailAlertRequest.request_id.cast(String).ilike(pattern),
                )),
            ))
        return statement

    def get_analytics(self, filters: EmailAlertFilters) -> dict:
        base = self._apply_filters(select(EmailAlert), filters).subquery()
        request_counts = select(EmailAlertRequest.email_alert_id, func.count(EmailAlertRequest.id).label("requests")).group_by(EmailAlertRequest.email_alert_id).subquery()
        summary_row = self.__db.execute(select(
            func.count(base.c.id),
            func.coalesce(func.sum(case((base.c.error_type == "UNKNOWN", 1), else_=0)), 0),
            func.coalesce(func.sum(case((base.c.error_type == "RESPONSE_VALIDATION", 1), else_=0)), 0),
            func.count(func.distinct(base.c.source_name)),
            func.count(func.distinct(base.c.environment)),
        )).one()
        total_alerts, unknown, validation, unique_sources, unique_environments = summary_row
        total_requests = self.__db.scalar(select(func.coalesce(func.sum(request_counts.c.requests), 0)).select_from(request_counts.join(base, request_counts.c.email_alert_id == base.c.id))) or 0

        trend_rows = self.__db.execute(select(
            func.date_trunc("day", base.c.email_received_at).label("day"),
            func.count(base.c.id),
            func.coalesce(func.sum(case((base.c.error_type == "UNKNOWN", 1), else_=0)), 0),
            func.coalesce(func.sum(case((base.c.error_type == "RESPONSE_VALIDATION", 1), else_=0)), 0),
        ).where(base.c.email_received_at.is_not(None)).group_by("day").order_by("day")).all()
        source_rows = self.__db.execute(
            select(
                base.c.source_name,
                func.count(base.c.id),
                func.coalesce(func.sum(request_counts.c.requests), 0),
                func.coalesce(func.sum(case((base.c.error_type == "UNKNOWN", 1), else_=0)), 0),
                func.coalesce(func.sum(case((base.c.error_type == "RESPONSE_VALIDATION", 1), else_=0)), 0),
            )
            .select_from(base.outerjoin(request_counts, base.c.id == request_counts.c.email_alert_id))
            .group_by(base.c.source_name)
            .order_by(func.count(base.c.id).desc())
        ).all()
        environment_rows = self.__db.execute(
            select(
                base.c.environment,
                func.count(base.c.id),
                func.coalesce(func.sum(request_counts.c.requests), 0),
            )
            .select_from(base.outerjoin(request_counts, base.c.id == request_counts.c.email_alert_id))
            .group_by(base.c.environment)
            .order_by(func.count(base.c.id).desc())
        ).all()
        top_error_rows = self.__db.execute(select(base.c.error_message, func.count(base.c.id), func.array_agg(func.distinct(base.c.source_name))).group_by(base.c.error_message).order_by(func.count(base.c.id).desc()).limit(10)).all()
        matrix_rows = self.__db.execute(select(base.c.source_name, base.c.error_type, func.count(base.c.id)).group_by(base.c.source_name, base.c.error_type)).all()
        recent_rows = self.find_all(filters=filters, limit=10, sort_by="created_at", sort_order="desc")
        return {
            "summary": {"total_alerts": int(total_alerts), "total_requests": int(total_requests), "unknown_errors": int(unknown), "response_validation_errors": int(validation), "unique_sources": int(unique_sources), "unique_environments": int(unique_environments)},
            "trend": [{"date": row[0].date(), "total": row[1], "unknown": row[2], "response_validation": row[3]} for row in trend_rows],
            "error_type_distribution": [{"error_type": "UNKNOWN", "count": int(unknown)}, {"error_type": "RESPONSE_VALIDATION", "count": int(validation)}],
            "by_source": [{"source_name": row[0], "alerts": row[1], "requests": row[2], "unknown": row[3], "response_validation": row[4]} for row in source_rows],
            "by_environment": [{"environment": row[0], "alerts": row[1], "requests": row[2], "percentage": round((row[1] / total_alerts) * 100, 2) if total_alerts else 0} for row in environment_rows],
            "top_errors": [{"error_message": row[0], "count": row[1], "sources": [source for source in (row[2] or []) if source]} for row in top_error_rows],
            "source_error_type": [{"source_name": row[0], "error_type": row[1], "count": row[2]} for row in matrix_rows],
            "recent_alerts": recent_rows,
        }
    
    def exists_by_alert_id_and_request_id(
        self,
        email_alert_id: UUID,
        request_id: UUID,
    ) -> bool:

        statement = select(EmailAlertRequest.id).where(
            EmailAlertRequest.email_alert_id == email_alert_id,
            EmailAlertRequest.request_id == request_id,
        )

        return self.__db.scalar(statement) is not None

    def update_azure_task(
        self,
        alert_id: UUID,
        azure_task: str | None,
    ) -> EmailAlert | None:
        alert = self.__db.get(EmailAlert, alert_id)

        if alert is None:
            return None

        alert.azure_task = azure_task
        self.__db.flush()

        return alert

    def update_azure_task_by_error_message_contains(
        self,
        error_message: str,
        azure_task_url: str,
    ) -> int:
        sanitized_error_message = error_message.strip()
        if not sanitized_error_message:
            return 0

        result = self.__db.execute(
            EmailAlert.__table__.update()
            .where(func.lower(EmailAlert.error_message) == sanitized_error_message.lower())
            .values(azure_task=azure_task_url)
        )
        return result.rowcount or 0

    def commit(self):
        self.__db.commit()

    def rollback(self):
        self.__db.rollback()