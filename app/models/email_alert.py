from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.email_alert_request import EmailAlertRequest


class ErrorType(str, Enum):
    UNKNOWN = "UNKNOWN"
    RESPONSE_VALIDATION = "RESPONSE_VALIDATION"


class EmailAlert(Base):
    __tablename__ = "email_alert"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    message_id: Mapped[str | None] = mapped_column(
        String(500),
        unique=True,
        nullable=True,
    )

    azure_task: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    email_subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    error_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    environment: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    source_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    alert_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    email_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sender_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    original_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    requests: Mapped[list["EmailAlertRequest"]] = relationship(
        back_populates="email_alert",
        cascade="all, delete-orphan",
    )