"""add competition category

Revision ID: 20260818000001
Revises: 20260818000000
Create Date: 2026-08-18 15:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260818000001"
down_revision = "20260818000000"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "competitions",
            sa.Column(
                "category",
                sa.String(33),
                nullable=False,
                server_default="AI for Engineering and Technology",
            ),
    )


def downgrade():
    op.drop_column("competitions", "category")
