from sqlalchemy import UUID, select
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.email_alert import EmailAlert
from app.models.email_alert_request import EmailAlertRequest


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
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[EmailAlert]:

        statement = (
            select(EmailAlert)
            .order_by(EmailAlert.created_at.desc())
        )

        if from_date is not None:
            statement = statement.where(
                EmailAlert.email_received_at >= from_date
            )

        if to_date is not None:
            statement = statement.where(
                EmailAlert.email_received_at <= to_date
            )

        return list(
            self.__db.scalars(statement).unique().all()
        )
    
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