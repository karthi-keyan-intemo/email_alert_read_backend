"""drop reference id

Revision ID: 07ba62c978da
Revises: 20260910_000001
Create Date: 2026-09-11 00:27:30.341255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07ba62c978da'
down_revision = '20260910_000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column(
        "email_alert",
        "reference_id",
    )

    op.create_unique_constraint(
        "uq_email_alert_request_alert_request",
        "email_alert_request",
        ["email_alert_id", "request_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_email_alert_request_alert_request",
        "email_alert_request",
        type_="unique",
    )

    op.add_column(
        "email_alert",
        sa.Column(
            "reference_id",
            sa.String(length=255),
            nullable=True,
        ),
    )