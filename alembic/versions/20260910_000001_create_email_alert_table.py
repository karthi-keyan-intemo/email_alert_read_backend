"""create email alert table

Revision ID: 20260910_000001
Revises: 
Create Date: 2026-09-10 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4
from sqlalchemy.dialects import postgresql

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260910_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # email_alert
    # ---------------------------------------------------------
    op.create_table(
        "email_alert",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "message_id",
            sa.String(length=500),
            nullable=True,
        ),
        
        sa.Column(
            "azure_task",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "email_subject",
            sa.String(length=500),
            nullable=False,
        ),

        sa.Column(
            "error_type",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "environment",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "source_name",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "reference_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "alert_timestamp",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "email_received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "sender_email",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "original_body",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "message_id",
            name="uq_email_alert_message_id",
        ),
    )

    # Indexes for commonly queried fields
    op.create_index(
        "ix_email_alert_message_id",
        "email_alert",
        ["message_id"],
        unique=False,
    )

    op.create_index(
        "ix_email_alert_environment",
        "email_alert",
        ["environment"],
        unique=False,
    )

    op.create_index(
        "ix_email_alert_source_name",
        "email_alert",
        ["source_name"],
        unique=False,
    )

    op.create_index(
        "ix_email_alert_error_type",
        "email_alert",
        ["error_type"],
        unique=False,
    )

    op.create_index(
        "ix_email_alert_alert_timestamp",
        "email_alert",
        ["alert_timestamp"],
        unique=False,
    )

    # ---------------------------------------------------------
    # email_alert_request
    # ---------------------------------------------------------
    op.create_table(
        "email_alert_request",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "email_alert_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        sa.ForeignKeyConstraint(
            ["email_alert_id"],
            ["email_alert.id"],
            name="fk_email_alert_request_email_alert_id",
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "email_alert_id",
            "request_id",
            name="uq_email_alert_request",
        ),
    )

    op.create_index(
        "ix_email_alert_request_email_alert_id",
        "email_alert_request",
        ["email_alert_id"],
        unique=False,
    )

    op.create_index(
        "ix_email_alert_request_request_id",
        "email_alert_request",
        ["request_id"],
        unique=False,
    )


def downgrade() -> None:
    # Child table must be dropped first because it contains
    # the foreign key to email_alert.
    op.drop_index(
        "ix_email_alert_request_request_id",
        table_name="email_alert_request",
    )

    op.drop_index(
        "ix_email_alert_request_email_alert_id",
        table_name="email_alert_request",
    )

    op.drop_table("email_alert_request")

    # Parent table
    op.drop_index(
        "ix_email_alert_alert_timestamp",
        table_name="email_alert",
    )

    op.drop_index(
        "ix_email_alert_error_type",
        table_name="email_alert",
    )

    op.drop_index(
        "ix_email_alert_source_name",
        table_name="email_alert",
    )

    op.drop_index(
        "ix_email_alert_environment",
        table_name="email_alert",
    )

    op.drop_index(
        "ix_email_alert_message_id",
        table_name="email_alert",
    )

    op.drop_table("email_alert")
