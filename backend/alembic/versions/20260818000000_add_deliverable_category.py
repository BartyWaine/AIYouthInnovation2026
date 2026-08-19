"""add deliverable category

Revision ID: 20260818000000
Revises: 20230816180000
Create Date: 2026-08-18 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260818000000"
down_revision = "20230816180000"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "deliverables",
            sa.Column(
                "category",
                sa.String(33),
                nullable=True,
            ),
    )


def downgrade():
    op.drop_column("deliverables", "category")
