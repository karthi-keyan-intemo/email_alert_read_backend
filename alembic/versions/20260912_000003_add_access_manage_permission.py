"""add access management permission

Revision ID: 20260912_000003
Revises: 20260912_000002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260912_000003"
down_revision: Union[str, None] = "20260912_000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("permissions", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.add_column("permissions", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.alter_column("permissions", "created_at", nullable=False)
    op.alter_column("permissions", "updated_at", nullable=False)
    op.execute(sa.text("""
        INSERT INTO permissions (id, name, description)
        VALUES (:id, 'ACCESS_MANAGE', 'Manage users, roles, and permissions')
        ON CONFLICT (name) DO NOTHING
    """).bindparams(id="00000000-0000-0000-0000-000000000015"))
    op.execute(sa.text("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id FROM roles r CROSS JOIN permissions p
        WHERE r.name = 'ADMIN' AND p.name = 'ACCESS_MANAGE'
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM role_permissions
        WHERE permission_id = (SELECT id FROM permissions WHERE name = 'ACCESS_MANAGE')
    """))
    op.execute(sa.text("DELETE FROM permissions WHERE name = 'ACCESS_MANAGE'"))
    op.drop_column("permissions", "updated_at")
    op.drop_column("permissions", "created_at")