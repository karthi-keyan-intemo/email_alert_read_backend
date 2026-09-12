from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel


class EmailAlertReadRequest(BaseModel):
    from_date: date
    to_date: date


class EmailAlertReadResponse(BaseModel):
    emails_found: int
    alerts_created: int
    alerts_skipped: int


class EmailAlertAzureTaskUpdateRequest(BaseModel):
    azure_task: str | None = None

    @staticmethod
    def _normalize(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = " ".join(value.split())
        return normalized or None

    def model_post_init(self, __context) -> None:
        self.azure_task = self._normalize(self.azure_task)


class EmailAlertAzureTaskUpdateResponse(BaseModel):
    id: UUID
    azure_task: str | None

    model_config = {
        "from_attributes": True,
    }


class EmailAlertRequestResponse(BaseModel):
    id: UUID
    request_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class EmailAlertResponse(BaseModel):
    id: UUID
    message_id: str | None
    azure_task: str | None
    email_subject: str
    error_type: str
    environment: str | None
    source_name: str | None
    error_message: str | None
    alert_timestamp: datetime | None
    email_received_at: datetime | None
    sender_email: str | None
    original_body: str | None
    created_at: datetime

    requests: list[EmailAlertRequestResponse] = []

    model_config = {
        "from_attributes": True,
    }