from sqlalchemy.orm import Session

from app.repositories.email_alert_repository import EmailAlertRepository


class N8nIntegrationService:
    def __init__(self, repository: EmailAlertRepository):
        self.__repository = repository

    def update_azure_task_for_error_message(
        self,
        error_message: str,
        azure_task_url: str,
    ) -> int:
        normalized_error_message = " ".join(error_message.split()).strip()
        normalized_url = " ".join(azure_task_url.split()).strip()

        if not normalized_error_message:
            raise ValueError("error_message cannot be empty.")

        if not normalized_url:
            raise ValueError("azure_task_url cannot be empty.")

        try:
            alerts_updated = self.__repository.update_azure_task_by_error_message_contains(
                error_message=normalized_error_message,
                azure_task_url=normalized_url,
            )

            if alerts_updated == 0:
                raise ValueError("No alert found matching the provided error message")

            self.__repository.commit()
            return alerts_updated
        except Exception:
            self.__repository.rollback()
            raise
