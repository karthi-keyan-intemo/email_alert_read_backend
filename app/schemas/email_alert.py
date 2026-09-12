from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


class EmailAlertReadRequest(BaseModel):
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.from_date > self.to_date:
            raise ValueError("from_date cannot be later than to_date")
        return self


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

    requests: list[EmailAlertRequestResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }


class EmailAlertSummary(BaseModel):
    total_alerts: int
    unknown_errors: int
    response_validation_errors: int
    total_requests: int


class PaginatedEmailAlertResponse(BaseModel):
    items: list[EmailAlertResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    summary: EmailAlertSummary


class AnalyticsSummary(BaseModel):
    total_alerts: int
    total_requests: int
    unknown_errors: int
    response_validation_errors: int
    unique_sources: int
    unique_environments: int


class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    trend: list[dict]
    error_type_distribution: list[dict]
    by_source: list[dict]
    by_environment: list[dict]
    top_errors: list[dict]
    source_error_type: list[dict]
    recent_alerts: list[EmailAlertResponse]