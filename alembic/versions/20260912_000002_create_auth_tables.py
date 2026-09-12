"""create authentication and authorization tables

Revision ID: 20260912_000002
Revises: 07ba62c978da
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260912_000002"
down_revision: Union[str, None] = "07ba62c978da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_permissions_name"),
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    roles = {
        "ADMIN": ("00000000-0000-0000-0000-000000000001", "Full alert management access"),
        "USER": ("00000000-0000-0000-0000-000000000002", "Standard alert management access"),
        "VIEWER": ("00000000-0000-0000-0000-000000000003", "Read-only alert access"),
    }
    permissions = {
        "ALERT_VIEW": ("00000000-0000-0000-0000-000000000011", "View alert data"),
        "ALERT_SYNC": ("00000000-0000-0000-0000-000000000012", "Synchronize email alerts"),
        "ALERT_EXPORT": ("00000000-0000-0000-0000-000000000013", "Export alert data"),
        "ALERT_EDIT": ("00000000-0000-0000-0000-000000000014", "Edit Azure Task values"),
    }
    for name, (role_id, description) in roles.items():
        op.execute(sa.text("INSERT INTO roles (id, name, description) VALUES (:id, :name, :description)").bindparams(id=role_id, name=name, description=description))
    for name, (permission_id, description) in permissions.items():
        op.execute(sa.text("INSERT INTO permissions (id, name, description) VALUES (:id, :name, :description)").bindparams(id=permission_id, name=name, description=description))
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
        WHERE r.name IN ('ADMIN', 'USER')
        UNION ALL
        SELECT r.id, p.id FROM roles r JOIN permissions p ON p.name = 'ALERT_VIEW'
        WHERE r.name = 'VIEWER'
    """))


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("roles")
    op.drop_table("users")