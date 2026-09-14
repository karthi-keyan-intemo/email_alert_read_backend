from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class N8nAzureTaskWebhookRequest(BaseModel):
    error_message: str = Field(..., min_length=1, max_length=2000)
    azure_task_url: str = Field(..., min_length=1, max_length=2000)

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if not normalized:
            raise ValueError("error_message cannot be empty")
        return normalized

    @field_validator("azure_task_url")
    @classmethod
    def validate_azure_task_url(cls, value: str) -> str:
        normalized = " ".join(value.split()).strip()
        if not normalized:
            raise ValueError("azure_task_url cannot be empty")
        parsed = urlparse(normalized)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("azure_task_url must be a valid HTTP or HTTPS URL")
        return normalized

    model_config = {"extra": "forbid"}


class N8nAzureTaskWebhookResponse(BaseModel):
    success: bool = True
    error_message: str
    azure_task_url: str
    alerts_updated: int

    model_config = {"from_attributes": True}
