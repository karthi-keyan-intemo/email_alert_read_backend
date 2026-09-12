from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.email_alert import EmailAlert


class EmailAlertRequest(Base):
    __tablename__ = "email_alert_request"
    
    __table_args__ = (
        UniqueConstraint(
            "email_alert_id",
            "request_id",
            name="uq_email_alert_request",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    email_alert_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "email_alert.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    request_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    email_alert: Mapped["EmailAlert"] = relationship(
        back_populates="requests",
    )