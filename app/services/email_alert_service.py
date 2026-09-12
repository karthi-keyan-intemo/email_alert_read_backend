from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from datetime import date, datetime
import math
from uuid import UUID

from app.models.email_alert_request import EmailAlertRequest
from app.models.email_alert import EmailAlert
from app.repositories.email_alert_repository import EmailAlertRepository
from app.repositories.email_alert_repository import EmailAlertFilters
from app.services.email_parser import get_error_type
from app.services.email_body_parser import get_body
from app.services.alert_body_parser import parse_alert_body
from app.services.email_reader import EmailReader


class EmailAlertService:

    def __init__(
        self,
        email_reader: EmailReader,
        repository: EmailAlertRepository,
    ):
        self.__email_reader = email_reader
        self.__repository = repository

    def process_emails(
        self,
        from_date: datetime,
        to_date: datetime,
    ):

        messages = self.__email_reader.read_emails(
            from_date,
            to_date,
        )

        alerts_created = 0
        alerts_skipped = 0

        # Track request IDs processed during this execution.
        # Key = (alert_id, request_id)
        processed_request_ids = set()

        for message in messages:

            # -----------------------------------------
            # Subject
            # -----------------------------------------

            raw_subject = message.get("Subject", "")

            subject = str(
                make_header(
                    decode_header(raw_subject)
                )
            ).strip()

            error_type = get_error_type(subject)

            if error_type is None:
                continue

            # -----------------------------------------
            # Message ID - technical deduplication
            # -----------------------------------------

            message_id = message.get("Message-ID")

            if (
                message_id
                and self.__repository.exists_by_message_id(
                    message_id
                )
            ):
                alerts_skipped += 1
                continue

            # -----------------------------------------
            # Email body
            # -----------------------------------------

            body_data = get_body(message)

            body = body_data["body"]

            parsed = parse_alert_body(body)

            # -----------------------------------------
            # Email received time
            # -----------------------------------------

            email_received_at = None

            date_header = message.get("Date")

            if date_header:
                try:
                    email_received_at = parsedate_to_datetime(
                        date_header
                    )
                except (TypeError, ValueError):
                    pass

            # -----------------------------------------
            # Find existing alert
            # -----------------------------------------

            alert = self.__repository.find_by_alert_details(
                environment=parsed["environment"],
                source_name=parsed["source_name"],
                error_message=parsed["error_message"],
            )

            # -----------------------------------------
            # Create new parent if not found
            # -----------------------------------------

            if alert is None:

                alert = EmailAlert(
                    message_id=message_id,
                    email_subject=subject,
                    error_type=error_type,
                    environment=parsed["environment"],
                    source_name=parsed["source_name"],
                    error_message=parsed["error_message"],
                    azure_task=parsed["azure_task"],
                    alert_timestamp=parsed["alert_timestamp"],
                    email_received_at=email_received_at,
                    sender_email=message.get("From"),
                    original_body=body,
                )

                self.__repository.save(alert)

                alerts_created += 1

            # -----------------------------------------
            # Add request IDs
            # -----------------------------------------

            for request_id in parsed["request_ids"]:

                request_key = (
                    alert.id,
                    request_id,
                )

                # Already processed during this execution
                if request_key in processed_request_ids:
                    print(
                        f"Request ID {request_id} already processed "
                        f"for alert ID {alert.id}"
                    )
                    continue

                # Already exists in database
                if self.__repository.exists_by_alert_id_and_request_id(
                    alert.id,
                    request_id,
                ):
                    print(
                        f"Request ID {request_id} already exists "
                        f"for alert ID {alert.id}"
                    )

                    processed_request_ids.add(request_key)
                    continue

                # Add new request
                alert.requests.append(
                    EmailAlertRequest(
                        request_id=request_id
                    )
                )

                # IMPORTANT
                # Mark it immediately to prevent duplicates
                # within this same process.
                processed_request_ids.add(request_key)

        self.__repository.commit()

        return {
            "emails_found": len(messages),
            "alerts_created": alerts_created,
            "alerts_skipped": alerts_skipped,
        }
    
    def get_email_alerts(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_by: str = "alert_timestamp",
        sort_order: str = "desc",
        filters: EmailAlertFilters | None = None,
    ) -> dict:
        summary = self.__repository.get_page_summary(
            from_date=from_date,
            to_date=to_date,
            search=search,
            filters=filters,
        )
        total = summary["total_alerts"]
        return {
            "items": self.__repository.find_all(
                from_date=from_date,
                to_date=to_date,
                offset=(page - 1) * page_size,
                limit=page_size,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order,
                filters=filters,
            ),
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": math.ceil(total / page_size) if total else 0,
            "summary": summary,
        }

    def get_analytics(self, filters: EmailAlertFilters) -> dict:
        return self.__repository.get_analytics(filters)

    def export_email_alerts(
        self,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[EmailAlert]:
        return self.__repository.find_all_for_export(
            from_date=from_date,
            to_date=to_date,
        )

    def update_azure_task(
        self,
        alert_id: UUID,
        azure_task: str | None,
    ) -> EmailAlert:
        normalized_task = None

        if azure_task is not None:
            normalized_task = " ".join(azure_task.split())
            if normalized_task == "":
                normalized_task = None

        updated_alert = self.__repository.update_azure_task(
            alert_id=alert_id,
            azure_task=normalized_task,
        )

        if updated_alert is None:
            raise ValueError("Alert not found.")

        self.__repository.commit()

        return updated_alert

    def update_azure_task(
        self,
        alert_id,
        azure_task: str | None,
    ) -> EmailAlert:
        normalized_task = None

        if azure_task is not None:
            normalized_task = " ".join(azure_task.split())
            if normalized_task == "":
                normalized_task = None

        updated_alert = self.__repository.update_azure_task(
            alert_id=alert_id,
            azure_task=normalized_task,
        )

        if updated_alert is None:
            raise ValueError("Alert not found.")

        self.__repository.commit()

        return updated_alert